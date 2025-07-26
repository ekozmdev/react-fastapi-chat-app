import type React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from 'react-router-dom';
import './App.css';
import { AuthProvider, useAuth } from './AuthContext';
import LoginForm from './LoginForm';
import MarkdownRenderer from './MarkdownRenderer';
import ProtectedRoute from './ProtectedRoute';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolExecutions?: ToolExecution[];
}

interface ToolExecution {
  id: string;
  name: string;
  status: 'executing' | 'completed';
  output?: string;
}

interface StreamingMessage {
  id: string;
  content: string;
  isStreaming: boolean;
  toolExecutions: ToolExecution[];
}

interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

const ChatApp: React.FC = () => {
  const { user, logout, token } = useAuth();
  const { conversationId: urlConversationId } = useParams<{
    conversationId?: string;
  }>();
  const navigate = useNavigate();
  /* ----------------------- state & refs ----------------------- */
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(urlConversationId || null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null);
  const [isCreatingNewChat, setIsCreatingNewChat] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const newChatIdRef = useRef<string | null>(null);

  /* ----------------------- fetch helpers ---------------------- */
  const fetchConversations = useCallback(async () => {
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
        const data = await res.json();

        // メッセージを段階的に表示（非同期）
        setTimeout(() => {
          setMessages(data.messages);
          setConversationId(convId);
          setIsLoadingConversation(false);
        }, 50); // 少し遅延させてスムーズに表示
      } catch (err) {
        console.error('Failed to fetch conversation:', err);
        setIsLoadingConversation(false);
      }
    },
    [token]
  );

  /* ----------------------- SSE -------------------------- */
  const startSSEStream = async (convId: string, message: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      // SSEエンドポイントにPOSTリクエストを送信
      const response = await fetch(`/api/chat/stream/${convId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
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

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));

                  // デバッグ用：受信したSSEイベントをログ出力（簡潔化）
                  if (data.type === 'tool_start' || data.type === 'tool_complete') {
                    console.log(`SSE: ${data.type} - ${data.tool_name}`, data.tool_output ? `-> ${data.tool_output.substring(0, 30)}...` : '');
                  }

                  switch (data.type) {
                    case 'status':
                      // ステータスは表示しない
                      break;
                    case 'tool_decision':
                      // 🆕 Phase 4.2: LLM決定時点でスピナー即座表示開始
                      console.log(`🚀 Tool decision detected: ${data.tool_name}`);
                      setStreamingMessage((prev) => {
                        const executionId = data.execution_id || `${data.tool_name}_${Date.now()}`;
                        
                        // 🛡️ 双方向重複チェック: tool_startで既にエントリが存在するかチェック
                        const existingExecution = prev?.toolExecutions.find(exec => 
                          exec.id === executionId || 
                          exec.name === data.tool_name ||
                          (data.execution_id && exec.id === data.execution_id)
                        );
                        
                        if (existingExecution) {
                          // 既にtool_startで作成済み → スキップ
                          console.log(`⚠️ Tool execution already exists for ${data.tool_name}, skipping tool_decision`);
                          return prev;
                        }

                        const newExecution: ToolExecution = {
                          id: executionId,
                          name: data.tool_name,
                          status: 'executing',
                        };

                        if (!prev) {
                          // ストリーミングメッセージがまだない場合は作成
                          return {
                            id: data.message_id,
                            content: '',
                            isStreaming: true,
                            toolExecutions: [newExecution],
                          };
                        }

                        return {
                          ...prev,
                          toolExecutions: [...prev.toolExecutions, newExecution],
                        };
                      });
                      break;
                    case 'tool_start':
                      // ✅ 双方向重複チェック: tool_decisionで既にエントリが存在するかチェック
                      setStreamingMessage((prev) => {
                        const executionId = data.execution_id || `${data.tool_name}_${Date.now()}`;
                        
                        // 🛡️ 強化された重複チェック: より正確なID照合
                        const existingExecution = prev?.toolExecutions.find(exec => 
                          exec.id === executionId || 
                          exec.name === data.tool_name ||
                          (data.execution_id && exec.id === data.execution_id)
                        );
                        
                        if (existingExecution) {
                          // 既にtool_decisionで作成済み → スキップ
                          console.log(`⚠️ Tool execution already exists for ${data.tool_name}, skipping tool_start`);
                          return prev;
                        }

                        // 新規ツール実行の場合のみ作成
                        const newExecution: ToolExecution = {
                          id: executionId,
                          name: data.tool_name,
                          status: 'executing',
                        };

                        if (!prev) {
                          // ストリーミングメッセージがまだない場合は作成
                          return {
                            id: data.message_id,
                            content: '',
                            isStreaming: true,
                            toolExecutions: [newExecution],
                          };
                        }

                        return {
                          ...prev,
                          toolExecutions: [...prev.toolExecutions, newExecution],
                        };
                      });
                      break;
                    case 'tool_complete':
                      // ツール実行完了：結果を表示
                      setStreamingMessage((prev) => {
                        if (!prev) return prev;

                        return {
                          ...prev,
                          toolExecutions: prev.toolExecutions.map((exec) =>
                            exec.name === data.tool_name
                              ? {
                                  ...exec,
                                  status: 'completed',
                                  output: data.tool_output || '',
                                }
                              : exec
                          ),
                        };
                      });
                      break;
                    case 'content':
                      setStreamingMessage((prev) => {
                        if (!prev) {
                          // 初回コンテンツの場合、新しいストリーミングメッセージを作成
                          return {
                            id: data.message_id,
                            content: data.content,
                            isStreaming: true,
                            toolExecutions: [],
                          };
                        }
                        return {
                          ...prev,
                          content: prev.content + data.content,
                        };
                      });
                      break;
                    case 'done':
                      setStreamingMessage((prev) => {
                        if (prev) {
                          setMessages((m) => [
                            ...m,
                            {
                              id: data.message_id,
                              role: 'assistant',
                              content: prev.content,
                              timestamp: new Date().toISOString(),
                              toolExecutions: prev.toolExecutions, // ツール実行情報も保存
                            },
                          ]);
                        }
                        return null;
                      });
                      setIsLoading(false);
                      fetchConversations();
                      // 新規チャットの場合、ストリーミング完了後にナビゲーション
                      if (newChatIdRef.current) {
                        navigate(`/chat/${newChatIdRef.current}`);
                        newChatIdRef.current = null; // クリア
                        // setIsCreatingNewChatはuseEffect内で処理完了後に設定
                      }
                      break;
                    case 'error':
                      console.error('SSE error:', data.message);
                      setIsLoading(false);
                      alert(`エラー: ${data.message}`);
                      break;
                  }
                } catch (e) {
                  console.error('Failed to parse SSE data:', e);
                }
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

  // URLパラメータの変更を監視
  useEffect(() => {
    if (urlConversationId && urlConversationId !== conversationId) {
      // 新規チャット作成中の場合は何もしない
      if (isCreatingNewChat) {
        // 新規チャット作成完了をマーク
        setIsCreatingNewChat(false);
        return;
      }
      // 既存チャットの場合は通常通りfetchConversationを実行
      setConversationId(urlConversationId);
      fetchConversation(urlConversationId);
    } else if (!urlConversationId && conversationId) {
      // 新規チャット作成中の場合はクリアしない
      if (isCreatingNewChat) {
        return;
      }
      // URLに会話IDがない場合はクリア（handleNewChatで既にクリア済みなので重複実行を避ける）
      if (conversationId !== null) {
        setConversationId(null);
        setMessages([]);
      }
    }
  }, [urlConversationId, conversationId, isCreatingNewChat, fetchConversation]);

  // コンポーネントがアンマウントされるときのクリーンアップ
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), []);

  /* ----------------------- handlers --------------------------- */
  const handleNewChat = () => {
    navigate('/');
    setConversationId(null);
    setMessages([]);
    setInputMessage('');
    setStreamingMessage(null);
    setIsCreatingNewChat(false); // 新規チャット作成フラグをクリア
    newChatIdRef.current = null; // 新規チャットIDをクリア
    // SSE接続を明示的に閉じる
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const handleSelectConversation = (conv: Conversation) => {
    navigate(`/chat/${conv.id}`);
    setStreamingMessage(null);
    // 既存のSSE接続を閉じる
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`/api/conversations/${convId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchConversations();
      if (conversationId === convId) {
        navigate('/');
        setConversationId(null);
        setMessages([]);
        setStreamingMessage(null);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
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
      // 新規チャットの場合はまず会話IDを作成
      let convId = conversationId;
      if (!convId) {
        setIsCreatingNewChat(true); // 新規チャット作成開始
        const res = await fetch('/api/conversations', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        convId = data.conversation_id;
        setConversationId(convId);
        newChatIdRef.current = convId; // 新規チャットIDを保存
        // ナビゲーションはSSE完了後に行う
      } else {
        newChatIdRef.current = null; // 既存チャットの場合はクリア
      }

      // SSEストリーミング開始
      if (convId) {
        await startSSEStream(convId, messageContent);
      }
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

  /* ----------------------- format utils ----------------------- */
  const formatTime = (ts: string) =>
    new Date(ts).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
    });

  const formatDate = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diff = Math.ceil(Math.abs(+now - +date) / 86_400_000);
    if (diff === 0) return '今日';
    if (diff === 1) return '昨日';
    if (diff < 7) return `${diff}日前`;
    return date.toLocaleDateString('ja-JP');
  };

  // ツール実行情報表示コンポーネント
  const renderToolExecutions = (toolExecutions: ToolExecution[]) => (
    <div className="tool-executions">
      {toolExecutions.map((tool) => (
        <div key={tool.id} className={`tool-execution ${tool.status}`}>
          <div className="tool-header">
            <div className="tool-icon">
              {tool.status === 'executing' && <div className="tool-spinner"></div>}
              {tool.status === 'completed' && (
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path
                    d="M3 7L6 10L11 4"
                    stroke="#10b981"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              )}
            </div>
            <span className="tool-name">{tool.name}</span>
            <span className="tool-status-text">
              {tool.status === 'executing' && '実行中...'}
              {tool.status === 'completed' && '完了'}
            </span>
          </div>
          {tool.output && tool.status === 'completed' && (
            <div className="tool-output">{tool.output}</div>
          )}
        </div>
      ))}
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
        
        {/* Phase 8: サイドバー展開時・閉じた時両方で新しいチャットボタン表示 */}
        <button 
          type="button" 
          className={`new-chat-btn ${sidebarCollapsed ? 'collapsed' : 'expanded'}`} 
          onClick={handleNewChat}
          title={sidebarCollapsed ? '新しいチャット' : undefined}
          aria-label="新しいチャット"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          {!sidebarCollapsed && <span>新しいチャット</span>}
        </button>

        {!sidebarCollapsed && (
          <div className="sidebar-content">

        <div className="chat-history">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`chat-item ${conversationId === conv.id ? 'active' : ''}`}
              onClick={() => handleSelectConversation(conv)}
            >
              <div className="chat-item-content">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
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
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
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
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <circle cx="10" cy="6" r="3" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M5 18c0-4 2.5-7 5-7s5 3 5 7" stroke="currentColor" strokeWidth="1.5" />
                </svg>
              </div>
              <div className="user-details">
                <div className="username">{user?.username}</div>
                <div className="user-email">{user?.email}</div>
              </div>
              <button type="button" className="logout-btn" onClick={logout} title="ログアウト">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
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
            {messages?.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">{msg.role === 'user' ? 'You' : 'AI'}</div>
                <div className="message-content">
                  {/* ツール実行情報表示 */}
                  {msg.role === 'assistant' && msg.toolExecutions && msg.toolExecutions.length > 0 && 
                    renderToolExecutions(msg.toolExecutions)
                  }
                  <div className="message-text">
                    {msg.role === 'assistant' ? (
                      <MarkdownRenderer content={msg.content} />
                    ) : (
                      msg.content
                    )}
                  </div>
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
                  {/* ツール実行情報表示 */}
                  {streamingMessage.toolExecutions.length > 0 && 
                    renderToolExecutions(streamingMessage.toolExecutions)
                  }
                  <div className="message-text">
                    <MarkdownRenderer content={streamingMessage.content} />
                    {streamingMessage.isStreaming && 
                     streamingMessage.toolExecutions.every(tool => tool.status === 'completed') && 
                     <span className="typing-indicator">▊</span>}
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
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M2 10L18 2L14 18L10 11L2 10Z" fill="currentColor" />
              </svg>
            </button>
          </form>
          <div className="input-hint">
            <kbd>Ctrl + Enter</kbd> で送信、<kbd>Enter</kbd> で改行
          </div>
        </div>
      </div>
    </div>
  );
};

// ログインページ用のコンポーネント（認証済みの場合はリダイレクト）
const LoginRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner-large"></div>
        <p>読み込み中...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    // ログイン前にいたページに戻るか、デフォルトでルートに
    const from = location.state?.from?.pathname || '/';
    return <Navigate to={from} replace />;
  }

  return <LoginForm />;
};

// メインAppコンポーネント
const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <ChatApp />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat/:conversationId?"
            element={
              <ProtectedRoute>
                <ChatApp />
              </ProtectedRoute>
            }
          />
          {/* 存在しないパスは認証済みならルートへ、未認証ならログインへ */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
