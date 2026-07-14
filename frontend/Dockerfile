# Fase 1: Builder para construir la app de Next.js
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

# Fase 2: Runner de producción
FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/pnpm-lock.yaml ./pnpm-lock.yaml
RUN npm install -g pnpm && pnpm install --prod --frozen-lockfile
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js ./next.config.js

EXPOSE 3000
CMD ["pnpm", "run", "start"]
