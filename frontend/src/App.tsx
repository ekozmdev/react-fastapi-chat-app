import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface StreamingMessage {
  id: string;
  content: string;
  isStreaming: boolean;
}

interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

const App: React.FC = () => {
  /* ----------------------- state & refs ----------------------- */
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  /* ----------------------- fetch helpers ---------------------- */
  const fetchConversations = async () => {
    try {
      const res = await fetch('/api/conversations');
      const data = await res.json();
      setConversations(data.conversations);
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
    }
  };

  const fetchConversation = async (convId: string) => {
    try {
      const res = await fetch(`/api/conversations/${convId}`);
      const data = await res.json();
      setMessages(data.messages);
      setConversationId(convId);
    } catch (err) {
      console.error('Failed to fetch conversation:', err);
    }
  };

  /* ----------------------- websocket -------------------------- */
  const initWebSocket = (convId: string) => {
    if (wsRef.current) wsRef.current.close();

    // 開発環境では直接バックエンドに接続、本番環境では相対パスを使用
    let wsUrl = '';
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      // 開発環境：直接バックエンドに接続
      wsUrl = `ws://localhost:8000/ws/${convId}`;
    } else {
      // 本番環境：相対パスでNginxプロキシを使用
      if (window.location.protocol === 'https:') {
        wsUrl = `wss://${window.location.host}/ws/${convId}`;
      } else {
        wsUrl = `ws://${window.location.host}/ws/${convId}`;
      }
    }

    const ws = new WebSocket(wsUrl);
    console.log('WebSocket connecting to:', wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected successfully:', convId);
    };

    ws.onmessage = evt => {
      const data = JSON.parse(evt.data);
      switch (data.type) {
        case 'start':
          setStreamingMessage({ id: data.message_id, content: '', isStreaming: true });
          break;
        case 'stream':
          setStreamingMessage(prev =>
            prev ? { ...prev, content: prev.content + data.content } : prev
          );
          break;
        case 'end':
          setStreamingMessage(prev => {
            if (prev) {
              setMessages(m => [
                ...m,
                { id: data.message_id, role: 'assistant', content: prev.content, timestamp: new Date().toISOString() }
              ]);
            }
            return null;
          });
          setIsLoading(false);
          fetchConversations();
          break;
      }
    };

    ws.onerror = err => {
      console.error('WebSocket error:', err);
      setIsLoading(false);
    };

    ws.onclose = evt => {
      console.log('WebSocket closed:', evt.code, evt.reason);
      if (isLoading) setIsLoading(false);
    };

    wsRef.current = ws;
  };

  /* ----------------------- effects ---------------------------- */
  useEffect(() => {
    fetchConversations();          // ← await する必要はない
  }, []);

  // WebSocketの初期化はuseEffectから削除して、メッセージ送信時に管理
  // useEffect(() => {
  //   if (conversationId) initWebSocket(conversationId);

  //   return () => {
  //     if (wsRef.current) wsRef.current.close();
  //   };
  // }, [conversationId]);

  // コンポーネントがアンマウントされるときのクリーンアップ
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [
    messages,
    streamingMessage
  ]);

  /* ----------------------- handlers --------------------------- */
  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setInputMessage('');
    setStreamingMessage(null);
    // WebSocket接続を明示的に閉じる
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleSelectConversation = (conv: Conversation) => {
    setStreamingMessage(null);
    // 既存のWebSocket接続を閉じる
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    fetchConversation(conv.id);
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`/api/conversations/${convId}`, { method: 'DELETE' });
      fetchConversations();
      if (conversationId === convId) handleNewChat();
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
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // 新規チャットの場合はまず会話IDを作成
      let convId = conversationId;
      if (!convId) {
        const res = await fetch('/api/conversations', { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        convId = data.conversation_id;
        setConversationId(convId);
      }

      // WebSocketが未接続または閉じている場合は接続を確立
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        initWebSocket(convId!);
        // WebSocket接続が確立されるまで待機
        await new Promise((resolve, reject) => {
          const checkConnection = () => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              resolve(true);
            } else if (wsRef.current?.readyState === WebSocket.CLOSED) {
              reject(new Error('WebSocket connection failed'));
            } else {
              setTimeout(checkConnection, 100);
            }
          };
          checkConnection();
        });
      }

      // WebSocket経由で送信
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ message: userMessage.content }));
      } else {
        setIsLoading(false);
        alert('WebSocket接続に失敗しました。再試行してください。');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  /* ----------------------- format utils ----------------------- */
  const formatTime = (ts: string) => new Date(ts).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

  const formatDate = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diff = Math.ceil(Math.abs(+now - +date) / 86_400_000);
    if (diff === 0) return '今日';
    if (diff === 1) return '昨日';
    if (diff < 7) return `${diff}日前`;
    return date.toLocaleDateString('ja-JP');
  };

  /* ----------------------- render ----------------------------- */
  return (
    <div className="app">
      {/* ------------- sidebar ------------- */}
      <div className="sidebar">
        <button className="new-chat-btn" onClick={handleNewChat}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          新しいチャット
        </button>

        <div className="chat-history">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`chat-item ${conversationId === conv.id ? 'active' : ''}`}
              onClick={() => handleSelectConversation(conv)}
            >
              <div className="chat-item-content">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 5L8 2L14 5V10C14 12.21 12.21 14 10 14H6C3.79 14 2 12.21 2 10V5Z" stroke="currentColor" strokeWidth="1.5" />
                </svg>
                <span className="chat-item-title">{conv.title || '新しいチャット'}</span>
              </div>
              <div className="chat-item-meta">
                <span className="chat-item-date">{formatDate(conv.updated_at)}</span>
                <button className="chat-item-delete" onClick={e => handleDeleteConversation(conv.id, e)}>
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ------------- main ------------- */}
      <div className="main-content">
        <div className="chat-container">
          {messages.length === 0 && !streamingMessage && (
            <div className="welcome-message">
              <h1>こんにちは！</h1>
              <p>何かお手伝いできることはありますか？</p>
            </div>
          )}

          <div className="messages">
            {messages.map(msg => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">{msg.role === 'user' ? 'You' : 'AI'}</div>
                <div className="message-content">
                  <div className="message-text">{msg.content}</div>
                  <div className="message-time">{formatTime(msg.timestamp)}</div>
                </div>
              </div>
            ))}

            {streamingMessage && (
              <div className="message assistant">
                <div className="message-avatar">AI</div>
                <div className="message-content">
                  <div className="message-text">
                    {streamingMessage.content}
                    <span className="typing-indicator">▊</span>
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
              onChange={e => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="メッセージを入力..."
              className="message-input"
              rows={1}
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={!inputMessage.trim() || isLoading}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M2 10L18 2L14 18L10 11L2 10Z" fill="currentColor" />
              </svg>
            </button>
          </form>
          <div className="input-hint">
            <kbd>Enter</kbd> で送信、<kbd>Shift + Enter</kbd> で改行
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
