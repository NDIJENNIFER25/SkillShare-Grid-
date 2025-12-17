### Multi-stage Dockerfile for the Bank-app
FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY package*.json ./
RUN npm ci --production --silent

# Copy app sources
COPY . .

### Final small runtime image
FROM node:18-alpine
ENV NODE_ENV=production
WORKDIR /app

# Create a non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy built app from builder stage
COPY --from=builder /app /app

# Ensure node_modules are readable
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 3000

# Simple healthcheck (alpine includes wget via busybox)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD wget -qO- --tries=1 --timeout=2 http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
