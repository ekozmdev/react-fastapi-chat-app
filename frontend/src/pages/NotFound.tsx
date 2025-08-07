import type React from 'react';
import { Link } from 'react-router-dom';

const NotFound: React.FC = () => {
  return (
    <div className="not-found-container">
      <div className="not-found-content">
        <h1>会話履歴が見つかりませんでした</h1>
        <div className="not-found-actions">
          <Link to="/" className="home-link">
            ホームに戻る
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
