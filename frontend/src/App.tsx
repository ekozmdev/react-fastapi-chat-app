import type React from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

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

  return <LoginPage />;
};

// メインAppコンポーネント
const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginRoute />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/:conversationId?"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route path="/not-found-error" element={<NotFoundPage />} />
        {/* 存在しないパスは認証済みならルートへ、未認証ならログインへ */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
};

export default App;
