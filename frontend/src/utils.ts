import type { Conversation, Message, MessageContent } from './types';

/**
 * フロントエンド用の一意IDを生成
 * @returns ユニークなID文字列
 */
export const generateUserMessageId = (): string => {
  return crypto.randomUUID();
};

/**
 * メッセージ内容をパースして適切な形式に変換
 * @param message メッセージオブジェクト
 * @returns パース済みメッセージ内容
 */
export const parseMessageContent = (message: Message): MessageContent => {
  if (message.role === 'tool') {
    try {
      return JSON.parse(message.content);
    } catch {
      console.error('Failed to parse tool message content');
      return {};
    }
  }

  if (message.role === 'assistant') {
    try {
      // JSON形式の場合（tool_callsあり）
      return JSON.parse(message.content);
    } catch {
      // プレーンテキストの場合
      return { text: message.content };
    }
  }

  // user メッセージはプレーンテキスト
  return { text: message.content };
};

/**
 * タイムスタンプを時刻形式にフォーマット
 * @param ts ISO形式のタイムスタンプ文字列
 * @returns フォーマット済み時刻文字列 (HH:MM)
 */
export const formatTime = (ts: string): string =>
  new Date(ts).toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });

/**
 * タイムスタンプを相対日付形式にフォーマット
 * @param ts ISO形式のタイムスタンプ文字列
 * @returns フォーマット済み日付文字列 (今日/昨日/N日前/日付)
 */
export const formatDate = (ts: string): string => {
  const date = new Date(ts);
  const now = new Date();
  const diff = Math.ceil(Math.abs(+now - +date) / 86_400_000);
  if (diff === 0) return '今日';
  if (diff === 1) return '昨日';
  if (diff < 7) return `${diff}日前`;
  return date.toLocaleDateString('ja-JP');
};

/**
 * 削除される会話の次に表示すべき会話を決定
 * @param deletedId 削除される会話ID
 * @param conversations 現在の会話一覧
 * @returns 次に表示する会話（なければnull）
 */
export const findNextConversation = (
  deletedId: string,
  conversations: Conversation[]
): Conversation | null => {
  const deletedIndex = conversations.findIndex((conv) => conv.id === deletedId);

  if (deletedIndex === -1) return null;

  // 1つ下の会話（配列の次のインデックス）
  if (deletedIndex < conversations.length - 1) {
    return conversations[deletedIndex + 1];
  }

  // 下がない場合は1つ上（配列の前のインデックス）
  if (deletedIndex > 0) {
    return conversations[deletedIndex - 1];
  }

  // 他に会話がない場合（最後の1つを削除）
  return null;
};
