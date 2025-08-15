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
        {/* 認証なしでアクセス可能なルート */}
        <Route path="/login" element={<LoginRoute />} />
        {/* ログインページ（認証済みの場合は自動リダイレクト） */}
        <Route path="/not-found-error" element={<NotFound />} /> {/* 404エラーページ */}
        {/* 認証が必要な保護されたルート群 */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Chat />} /> {/* ホーム - チャットページ */}
          <Route path="/chat/:conversationId?" element={<Chat />} /> {/* 特定の会話ページ */}
        </Route>
        {/* 未定義パスのフォールバック - ルートにリダイレクト */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
};

export default App;
