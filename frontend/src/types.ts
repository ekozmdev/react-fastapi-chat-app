// === チャット・メッセージ関連型 ===
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string; // user/assistant: プレーンテキスト、tool: JSON文字列
  timestamp: string;
}

export interface MessageContent {
  // user メッセージ
  text?: string;

  // tool メッセージ
  tool_call_id?: string;
  tool_name?: string;
  output?: string;
  status?: 'success' | 'error';
}

export interface StreamingMessage {
  id: string;
  content: string;
  isStreaming: boolean;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

// === 認証・ユーザー関連型 ===
export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  updateUser: (userData: Partial<User>) => void;
}
