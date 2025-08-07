import type React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

const ProtectedRoute: React.FC = () => {
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

  if (!isAuthenticated) {
    // ログイン後に元のページに戻れるよう現在のURLを保存
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />; // 子ルートをレンダリング
};

export default ProtectedRoute;
