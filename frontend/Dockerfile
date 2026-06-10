# ---- Build stage ----
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Production stage: unified nginx (SPA + reverse proxy) ----
FROM nginx:alpine

RUN apk add --no-cache curl

# Copy built SPA
COPY --from=build /app/dist /usr/share/nginx/html

# Copy unified nginx config (serves SPA, proxies /api/ and /ws/ to backend)
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
