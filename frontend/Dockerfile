# ─────────────────────────────────────────────────────────────────────────────
# AMAN ERP — Frontend Dockerfile
# Multi-stage: deps → builder → nginx runtime
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Install dependencies ─────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline


# ── Stage 2: Build production bundle ──────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Bake the API URL at build time (overridable via --build-arg)
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

# Embed commit SHA for post-deploy verification
ARG BUILD_SHA=dev
ENV VITE_BUILD_SHA=$BUILD_SHA

RUN npm run build
RUN printf '%s\n' "$BUILD_SHA" > /app/dist/build-sha.txt


# ── Stage 3: Serve with nginx ──────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Custom nginx config (SPA routing + proxy to backend)
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
