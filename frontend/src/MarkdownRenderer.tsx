import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 改行を適切に処理
          p: ({ children }) => <p style={{ marginBottom: '0.3em' }}>{children}</p>,
          // リストのスタイリング
          ul: ({ children }) => <ul style={{ marginLeft: '1.2em', marginBottom: '0.3em' }}>{children}</ul>,
          ol: ({ children }) => <ol style={{ marginLeft: '1.2em', marginBottom: '0.3em' }}>{children}</ol>,
          li: ({ children }) => <li style={{ marginBottom: '0.1em' }}>{children}</li>,
          // 見出しのスタイリング
          h1: ({ children }) => <h1 style={{ fontSize: '1.5em', fontWeight: 'bold', marginBottom: '0.3em', marginTop: '0.8em' }}>{children}</h1>,
          h2: ({ children }) => <h2 style={{ fontSize: '1.3em', fontWeight: 'bold', marginBottom: '0.3em', marginTop: '0.6em' }}>{children}</h2>,
          h3: ({ children }) => <h3 style={{ fontSize: '1.1em', fontWeight: 'bold', marginBottom: '0.3em', marginTop: '0.4em' }}>{children}</h3>,
          // 強調表示
          strong: ({ children }) => <strong style={{ fontWeight: 'bold' }}>{children}</strong>,
          em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
          // コードブロック（シンプル）
          code: ({ children, className }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code style={{
                  backgroundColor: '#f5f5f5',
                  padding: '0.2em 0.4em',
                  borderRadius: '3px',
                  fontSize: '0.9em',
                  fontFamily: 'monospace'
                }}>
                  {children}
                </code>
              );
            } else {
              return (
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '1em',
                  borderRadius: '5px',
                  overflow: 'auto',
                  marginBottom: '0.3em'
                }}>
                  <code style={{ fontFamily: 'monospace', fontSize: '0.9em' }}>{children}</code>
                </pre>
              );
            }
          },
          // 引用
          blockquote: ({ children }) => (
            <blockquote style={{
              borderLeft: '4px solid #ddd',
              paddingLeft: '1em',
              margin: '0.3em 0',
              fontStyle: 'italic',
              color: '#666'
            }}>
              {children}
            </blockquote>
          ),
          // 水平線
          hr: () => <hr style={{ border: 'none', borderTop: '1px solid #ddd', margin: '1em 0' }} />,
          // テーブル
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', marginBottom: '0.3em' }}>
              <table style={{
                borderCollapse: 'collapse',
                width: '100%',
                minWidth: '300px',
                border: '1px solid #ddd'
              }}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead style={{ backgroundColor: '#f5f5f5' }}>
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody>
              {children}
            </tbody>
          ),
          th: ({ children }) => (
            <th style={{
              border: '1px solid #ddd',
              padding: '0.5em',
              backgroundColor: '#f5f5f5',
              fontWeight: 'bold',
              textAlign: 'left'
            }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{
              border: '1px solid #ddd',
              padding: '0.5em',
              textAlign: 'left'
            }}>
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;