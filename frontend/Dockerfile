# Destiny web client image: a static SPA build served by nginx, which also
# reverse-proxies /api to the backend so the browser sees one origin.
#   docker build -t destiny-frontend ./frontend

FROM node:22-alpine AS build

WORKDIR /build

# Dependencies first: this layer only invalidates when the lockfile changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json tsconfig.app.json tsconfig.node.json tailwind.config.ts postcss.config.js vite.config.ts index.html ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1/ || exit 1
