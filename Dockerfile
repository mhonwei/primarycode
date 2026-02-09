FROM node:20-alpine

WORKDIR /app

# 安装 better-sqlite3 编译依赖
RUN apk add --no-cache python3 make g++

COPY package.json package-lock.json ./
RUN npm ci --production

COPY server/ ./server/
COPY client/ ./client/

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 3000

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

CMD ["node", "server/index.js"]
