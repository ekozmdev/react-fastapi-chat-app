import type React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useNavigate, useParams } from 'react-router-dom';
import remarkGfm from 'remark-gfm';
import '../styles/App.css';
import { useAuth } from '../auth/AuthContext';
import type { Conversation, Message, StreamingMessage } from '../types';
import {
  findNextConversation,
  formatDate,
  formatTime,
  generateUserMessageId,
  parseMessageContent,
} from '../utils';

const Chat: React.FC = () => {
  const { user, logout, token, isLoading: isAuthLoading } = useAuth();
  const { conversationId: urlConversationId } = useParams<{
    conversationId?: string;
  }>();
  const navigate = useNavigate();
  /* ----------------------- state & refs ----------------------- */
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  // 右サイドバー関連の状態管理
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [selectedToolMessages, setSelectedToolMessages] = useState<Message[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  /* ----------------------- fetch helpers ---------------------- */
  const fetchConversations = useCallback(async (): Promise<void> => {
    try {
      const res = await fetch('/api/conversations', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      setConversations(data.conversations);
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
      throw err; // エラーを再スローして呼び出し元で処理可能に
    }
  }, [token]);

  const fetchConversation = useCallback(
    async (convId: string) => {
      try {
        setIsLoadingConversation(true);
        // 既存メッセージをクリア（スムーズな遷移のため）
        setMessages([]);

        const res = await fetch(`/api/conversations/${convId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();

        // メッセージと状態を即座に設定
        setMessages(data.messages);
        setConversationId(convId);
        setIsLoadingConversation(false);
      } catch (err) {
        console.error('Failed to fetch conversation:', err);
        setIsLoadingConversation(false);

        // 404エラーの場合はNotFoundページに遷移
        if (err instanceof Error && err.message.includes('404')) {
          navigate('/not-found-error');
        }
      }
    },
    [token, navigate]
  );

  /* ----------------------- SSE -------------------------- */
  const startSSEStream = async (conversationId: string, message: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      // SSEエンドポイントにPOSTリクエストを送信
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          conversation_id: conversationId || "",
          message 
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      const processSSEStream = async () => {
        try {
          let keepReading = true;
          while (keepReading) {
            const { done, value } = await reader.read();
            if (done) {
              keepReading = false;
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            let currentEvent = null;
            let currentData = '';

            for (const line of lines) {
              if (line.startsWith('event: ')) {
                // 前のイベントを処理
                if (currentEvent && currentData) {
                  try {
                    const data = JSON.parse(currentData);
                    if (currentEvent === 'done') {
                      // ストリーミング完了処理
                      setStreamingMessage((prev) => {
                        if (prev) {
                          setMessages((m) => [
                            ...m,
                            {
                              id: data.id,
                              role: 'assistant',
                              content: prev.content,
                              timestamp: new Date().toISOString(),
                            },
                          ]);
                        }
                        return null;
                      });
                      setIsLoading(false);
                      fetchConversations();
                    }
                  } catch (e) {
                    console.error('Failed to parse event data:', e);
                  }
                }

                // 新しいイベントを開始
                currentEvent = line.slice(7);
                currentData = '';
              } else if (line.startsWith('data: ')) {
                if (currentEvent) {
                  // イベント内のdata行
                  currentData = line.slice(6);
                } else {
                  // 通常のdataメッセージ（既存のSSE形式）
                  try {
                    const data = JSON.parse(line.slice(6));

                    // 新規会話作成イベントのチェック
                    if (data.type === 'conversation_created') {
                      const newConvId = data.conversation_id;
                      if (!conversationId) {  // 新規チャットの場合
                        setConversationId(newConvId);
                        navigate(`/chat/${newConvId}`);
                        fetchConversations();  // サイドバー更新
                      }
                      break;
                    }

                    switch (data.role) {
                      case 'tool':
                        // ツールメッセージを直接メッセージ履歴に追加
                        setMessages((prev) => [
                          ...prev,
                          {
                            id: data.id,
                            role: 'tool',
                            content: data.content, // JSON文字列
                            timestamp: data.timestamp || new Date().toISOString(),
                          },
                        ]);
                        break;
                      case 'assistant':
                        // assistantメッセージのストリーミング処理
                        setStreamingMessage((prev) => {
                          if (!prev) {
                            // 初回コンテンツの場合、新しいストリーミングメッセージを作成
                            return {
                              id: data.id,
                              content: data.content,
                              isStreaming: true,
                            };
                          }
                          return {
                            ...prev,
                            content: prev.content + data.content,
                          };
                        });
                        break;
                      default:
                        // エラー処理（従来形式）
                        if (data.error) {
                          console.error('SSE error:', data.error);
                          setIsLoading(false);
                          alert(`エラー: ${data.error}`);
                        }
                        break;
                    }
                  } catch (e) {
                    console.error('Failed to parse SSE data:', e);
                  }
                }
              } else if (line === '') {
                // 空行でイベント終了
                if (currentEvent && currentData) {
                  try {
                    const data = JSON.parse(currentData);
                    if (currentEvent === 'done') {
                      // ストリーミング完了処理
                      setStreamingMessage((prev) => {
                        if (prev) {
                          setMessages((m) => [
                            ...m,
                            {
                              id: data.id,
                              role: 'assistant',
                              content: prev.content,
                              timestamp: new Date().toISOString(),
                            },
                          ]);
                        }
                        return null;
                      });
                      setIsLoading(false);
                      fetchConversations();
                    }
                  } catch (e) {
                    console.error('Failed to parse event data:', e);
                  }
                }
                currentEvent = null;
                currentData = '';
              }
            }
          }
        } catch (error) {
          console.error('SSE stream error:', error);
          setIsLoading(false);
        } finally {
          reader.releaseLock();
        }
      };

      processSSEStream();
    } catch (error) {
      console.error('Failed to start SSE stream:', error);
      setIsLoading(false);
      alert('ストリーミング接続に失敗しました。再試行してください。');
    }
  };

  /* ----------------------- effects ---------------------------- */
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // 認証完了後の会話復元専用（画面更新対応）
  useEffect(() => {
    if (!isAuthLoading && token && urlConversationId) {

      // 削除済み会話IDの場合は無視（conversations配列に存在しない）
      const conversationExists = conversations.some((conv) => conv.id === urlConversationId);
      if (!conversationExists) {
        return;
      }

      // 会話IDが異なる場合は常に取得
      if (conversationId !== urlConversationId) {
        setConversationId(urlConversationId);
        fetchConversation(urlConversationId);
      }
    }
  }, [
    isAuthLoading,
    token,
    urlConversationId,
    conversationId,
    fetchConversation,
    conversations, // conversations配列も依存に追加
  ]);

  // URLクリア処理専用
  useEffect(() => {
    if (!urlConversationId && conversationId) {
      setConversationId(null);
      setMessages([]);
    }
  }, [urlConversationId, conversationId]);

  // コンポーネントがアンマウントされるときのクリーンアップ
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // メッセージが更新されたら自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  /* ----------------------- handlers --------------------------- */
  const handleNewChat = () => {
    navigate('/');
    setConversationId(null);
    setMessages([]);
    setInputMessage('');
    setStreamingMessage(null);
    // 右サイドバーを閉じる
    setRightSidebarOpen(false);
    setSelectedToolMessages([]);
    // SSE接続を明示的に閉じる
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const handleSelectConversation = (conv: Conversation) => {
    navigate(`/chat/${conv.id}`);
    setStreamingMessage(null);
    // 右サイドバーを閉じる
    setRightSidebarOpen(false);
    setSelectedToolMessages([]);
    // 既存のSSE接続を閉じる
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  /**
   * 現在開いている会話の削除処理
   * @param nextConversation 事前に決定された次の会話（なければnull）
   */
  const handleCurrentConversationDeletion = async (nextConversation: Conversation | null) => {
    if (nextConversation) {
      // 次の会話に移動
      navigate(`/chat/${nextConversation.id}`);
      // 注意: setConversationId等は行わない（useEffectで自動更新される）
    } else {
      // 最後の会話だった場合はルートへ
      navigate('/');
      setConversationId(null);
      setMessages([]);
      setStreamingMessage(null);
    }

    // 共通クリーンアップ処理
    setRightSidebarOpen(false);
    setSelectedToolMessages([]);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    const isCurrentConversation = conversationId === convId;

    try {
      // 削除前に次の会話を決定（現在の会話の場合のみ）
      let nextConversation: Conversation | null = null;
      if (isCurrentConversation) {
        nextConversation = findNextConversation(convId, conversations);
      }

      // 1. 削除API実行
      await fetch(`/api/conversations/${convId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // 2. 会話一覧更新（重要: awaitで完了を待つ）
      await fetchConversations();

      // 3. 現在開いている会話の場合のみ特別処理
      if (isCurrentConversation) {
        await handleCurrentConversationDeletion(nextConversation);
      }
      // 現在開いていない会話の削除は何もしない（既存の動作を維持）
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    // フロントエンドで即座にID生成してUI更新
    // バックエンドは独自にIDを生成してDB保存（フロントエンドIDは送信されない）
    const userMessage: Message = {
      id: generateUserMessageId(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageContent = inputMessage;
    setInputMessage('');
    // テキストエリアの高さをリセット
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsLoading(true);

    try {
      // シンプル！1回のAPI呼び出しで完結
      await startSSEStream(conversationId || "", messageContent);
    } catch (err) {
      console.error('Error sending message:', err);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!inputMessage.trim() || isLoading) return;

      // フォームイベントを作成
      const formEvent = {
        preventDefault: () => {},
        target: e.target,
        currentTarget: e.target,
      } as React.FormEvent;

      handleSubmit(formEvent);
    }
  };

  const adjustTextareaHeight = (textarea: HTMLTextAreaElement) => {
    textarea.style.height = 'auto';
    // 1行約24px（line-height 1.6 × font-size 15px）× 10行 = 240px
    const maxHeight = 24 * 10;
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    adjustTextareaHeight(e.target);
  };

  // 右サイドバーを開いてツール結果を表示
  const openToolSidebar = (toolMessages: Message[]) => {
    setSelectedToolMessages(toolMessages);
    setRightSidebarOpen(true);
  };

  // インデックスベースでツール検索
  const getToolMessagesBeforeAssistant = (assistantIndex: number): Message[] => {
    const toolMessages = [];
    // assistantメッセージの直前からツールメッセージを逆順検索
    for (let i = assistantIndex - 1; i >= 0 && messages[i] && messages[i].role === 'tool'; i--) {
      toolMessages.unshift(messages[i]); // 時系列順に配置
    }
    return toolMessages;
  };

  const renderMessage = (message: Message) => {
    const content = parseMessageContent(message);

    switch (message.role) {
      case 'user':
        return <div className="message-text">{content.text || message.content}</div>;
      case 'assistant': {
        // 元のmessages配列でのインデックスを取得
        const originalIndex = messages.findIndex((m) => m.id === message.id);
        const relatedTools = getToolMessagesBeforeAssistant(originalIndex);

        return (
          <div className="message-text">
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content.text || message.content}
              </ReactMarkdown>
            </div>
            {relatedTools.length > 0 && (
              <button
                type="button"
                className="tool-results-link"
                onClick={() => openToolSidebar(relatedTools)}
              >
                🔧 ツール実行結果
              </button>
            )}
          </div>
        );
      }
      default:
        return <div className="message-text">{message.content}</div>;
    }
  };

  // 右サイドバーコンポーネント
  const renderRightSidebar = () => (
    <div className={`right-sidebar ${rightSidebarOpen ? 'open' : 'closed'}`}>
      {rightSidebarOpen && (
        <>
          <div className="sidebar-header">
            <h3>ツール実行結果</h3>
            <button
              type="button"
              className="close-btn"
              onClick={() => setRightSidebarOpen(false)}
              aria-label="サイドバーを閉じる"
            >
              ×
            </button>
          </div>
          <div className="tool-results-content">
            {selectedToolMessages.map((toolMsg) => {
              const toolContent = parseMessageContent(toolMsg);
              return (
                <div key={toolMsg.id} className="tool-result-item">
                  <h4>{toolContent.tool_name}</h4>
                  <div className="tool-output">
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {toolContent.output || ''}
                      </ReactMarkdown>
                    </div>
                  </div>
                  <small className="tool-timestamp">{formatTime(toolMsg.timestamp)}</small>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );

  /* ----------------------- render ----------------------------- */
  return (
    <div className="app">
      {/* ------------- sidebar ------------- */}
      <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : 'expanded'}`}>
        <div className="sidebar-toggle">
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? 'サイドバーを開く' : 'サイドバーを閉じる'}
            aria-label={sidebarCollapsed ? 'サイドバーを開く' : 'サイドバーを閉じる'}
          >
            {sidebarCollapsed ? '>' : '<'}
          </button>
        </div>

        {/* サイドバー展開時・閉じた時両方で新しいチャットボタン表示 */}
        <button
          type="button"
          className={`new-chat-btn ${sidebarCollapsed ? 'collapsed' : 'expanded'}`}
          onClick={handleNewChat}
          title={sidebarCollapsed ? '新しいチャット' : undefined}
          aria-label="新しいチャット"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-label="新しいチャット"
            role="img"
          >
            <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          {!sidebarCollapsed && <span>新しいチャット</span>}
        </button>

        {!sidebarCollapsed && (
          <div className="sidebar-content">
            <div className="chat-history">
              {conversations.map((conv) => (
                // biome-ignore lint/a11y/useSemanticElements: Div is needed for CSS layout reasons
                <div
                  key={conv.id}
                  className={`chat-item ${conversationId === conv.id ? 'active' : ''}`}
                  onClick={() => handleSelectConversation(conv)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleSelectConversation(conv);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="chat-item-content">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      aria-label="チャット"
                      role="img"
                    >
                      <path
                        d="M2 5L8 2L14 5V10C14 12.21 12.21 14 10 14H6C3.79 14 2 12.21 2 10V5Z"
                        stroke="currentColor"
                        strokeWidth="1.5"
                      />
                    </svg>
                    <span className="chat-item-title">{conv.title || '新しいチャット'}</span>
                  </div>
                  <div className="chat-item-meta">
                    <span className="chat-item-date">{formatDate(conv.updated_at)}</span>
                    <button
                      type="button"
                      className="chat-item-delete"
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 14 14"
                        fill="none"
                        aria-label="削除"
                        role="img"
                      >
                        <path
                          d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="user-info">
              <div className="user-avatar">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  aria-label="ユーザー"
                  role="img"
                >
                  <circle cx="10" cy="6" r="3" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M5 18c0-4 2.5-7 5-7s5 3 5 7" stroke="currentColor" strokeWidth="1.5" />
                </svg>
              </div>
              <div className="user-details">
                <div className="username">{user?.username}</div>
                <div className="user-email">{user?.email}</div>
              </div>
              <button type="button" className="logout-btn" onClick={logout} title="ログアウト">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-label="ログアウト"
                  role="img"
                >
                  <path d="M6 16L1 16L1 0L6 0" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M11 12L15 8L11 4" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M15 8L6 8" stroke="currentColor" strokeWidth="1.5" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ------------- main ------------- */}
      <div className="main-content">
        <div className="chat-container">
          {messages && messages.length === 0 && !streamingMessage && !urlConversationId && (
            <div className="welcome-message">
              <h1>こんにちは！</h1>
              <p>何かお手伝いできることはありますか？</p>
            </div>
          )}

          <div className="messages">
            {isLoadingConversation && (
              <div className="loading-messages">
                <div className="spinner"></div>
                <span>メッセージを読み込み中...</span>
              </div>
            )}
            {messages
              ?.filter((msg) => msg.role !== 'tool')
              .map((msg) => (
                <div key={msg.id} className={`message ${msg.role}`}>
                  <div className="message-avatar">{msg.role === 'user' ? 'You' : 'AI'}</div>
                  <div className="message-content">
                    {renderMessage(msg)}
                    <div className="message-time">{formatTime(msg.timestamp)}</div>
                  </div>
                </div>
              ))}

            {/* ローディング中の表示（ユーザー送信直後から表示） */}
            {isLoading && !streamingMessage && (
              <div className="message assistant">
                <div className="message-avatar">AI</div>
                <div className="message-content">
                  <div className="message-spinner">
                    <div className="streaming-spinner"></div>
                  </div>
                </div>
              </div>
            )}

            {streamingMessage && (
              <div className="message assistant">
                <div className="message-avatar">AI</div>
                <div className="message-content">
                  <div className="message-text">
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamingMessage.content}
                      </ReactMarkdown>
                    </div>
                    {streamingMessage.isStreaming && <span className="typing-indicator">▊</span>}
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* ------------- input ------------- */}
        <div className="input-container">
          <form onSubmit={handleSubmit} className="input-form">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="メッセージを入力..."
              className="message-input"
              rows={1}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="send-button"
              disabled={!inputMessage.trim() || isLoading}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                aria-label="送信"
                role="img"
              >
                <path d="M2 10L18 2L14 18L10 11L2 10Z" fill="currentColor" />
              </svg>
            </button>
          </form>
          <div className="input-hint">
            <kbd>Ctrl + Enter</kbd> で送信、<kbd>Enter</kbd> で改行
          </div>
        </div>
      </div>

      {/* ------------- right sidebar ------------- */}
      {renderRightSidebar()}
    </div>
  );
};

export default Chat;
