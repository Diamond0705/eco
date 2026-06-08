FROM node:22-alpine AS react_builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/src ./src
RUN npm run build

FROM nginx:1.27-alpine

COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=react_builder /frontend/dist /usr/share/nginx/html
