FROM node:20-alpine AS builder
WORKDIR /app

# Install build dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy app source and build
COPY . .

# Build arguments with defaults for production
ARG NEXT_PUBLIC_IRC_WS_URL=wss://dev.ussy.host/irc
ARG NEXT_PUBLIC_IRC_CHANNEL=#devussy-chat
ENV NEXT_PUBLIC_IRC_WS_URL=$NEXT_PUBLIC_IRC_WS_URL
ENV NEXT_PUBLIC_IRC_CHANNEL=$NEXT_PUBLIC_IRC_CHANNEL

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy build artifacts and configuration
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

# Runtime environment variables
ARG NEXT_PUBLIC_IRC_WS_URL=wss://dev.ussy.host/irc
ARG NEXT_PUBLIC_IRC_CHANNEL=#devussy-chat
ENV NEXT_PUBLIC_IRC_WS_URL=$NEXT_PUBLIC_IRC_WS_URL
ENV NEXT_PUBLIC_IRC_CHANNEL=$NEXT_PUBLIC_IRC_CHANNEL

EXPOSE 3000

CMD ["npm", "run", "start"]
