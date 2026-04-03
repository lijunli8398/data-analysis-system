# 前端Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# 安装依赖
COPY package.json .
RUN npm install

# 复制源码并构建
COPY . .
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制前端构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制查看者页面
COPY viewer.html /usr/share/nginx/html/viewer.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]