# 校园美食 · 前端镜像（Vite 构建 -> Nginx 托管）
FROM node:20-alpine AS build
WORKDIR /build

COPY package.json package-lock.json ./
# 国内网络可换用镜像源，如：--registry=https://registry.npmmirror.com
RUN npm install

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html
EXPOSE 80
