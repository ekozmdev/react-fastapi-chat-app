# ビルドステージ
FROM node:18-alpine AS build

WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm ci

# アプリケーションコードをコピー
COPY . .

# Viteでビルド
RUN npm run build

# 本番ステージ
FROM nginx:alpine

# Nginxのデフォルト設定を削除
RUN rm /etc/nginx/conf.d/default.conf

# ビルドしたReactアプリをNginxのドキュメントルートにコピー
COPY --from=build /app/dist /usr/share/nginx/html

# ポート80を公開
EXPOSE 80

# Nginxを起動
CMD ["nginx", "-g", "daemon off;"]