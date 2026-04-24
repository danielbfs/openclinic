# Produção — Next.js com output standalone
# Stage 1: instala TODAS as dependências e compila
FROM node:22-alpine AS builder
WORKDIR /app

# Copia manifesto e instala dependências
# Aceita package-lock.json (npm ci) ou sem lock (npm install)
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copia código e compila
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: imagem final mínima apenas com o output standalone
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# public/ pode não existir em ambientes de desenvolvimento mínimos
RUN mkdir -p ./public
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
