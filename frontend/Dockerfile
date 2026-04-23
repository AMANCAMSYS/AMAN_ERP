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

# Hardening: run as the non-root nginx user. The base image already creates
# /var/cache/nginx and /var/run with the correct ownership, but we re-chown
# to be defensive when this image is used with --read-only and tmpfs mounts.
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid \
    && sed -i 's/^user .*/user nginx;/' /etc/nginx/nginx.conf || true

USER nginx

EXPOSE 8080

# When running with --read-only, mount tmpfs to /var/cache/nginx and /var/run.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
