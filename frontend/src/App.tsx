import type React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import LoginRoute from './auth/LoginRoute';
import ProtectedRoute from './auth/ProtectedRoute';
import Chat from './pages/Chat';
import NotFound from './pages/NotFound';

// メインAppコンポーネント
const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        {/* ログインページ（認証済みの場合は自動リダイレクト） */}
        <Route path="/login" element={<LoginRoute />} />
        {/* 404エラーページ */}
        <Route path="/not-found-error" element={<NotFound />} />
        <Route element={<ProtectedRoute />}>
          {/* ホーム - チャットページ */}
          <Route path="/" element={<Chat />} />
          {/* 特定の会話ページ */}
          <Route path="/chat/:conversationId?" element={<Chat />} />
        </Route>
        {/* 未定義パスの場合はルートにリダイレクト */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
};

export default App;
