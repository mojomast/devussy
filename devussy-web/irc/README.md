# Devussy IRC Add-on

This directory contains the configuration and documentation for the Devussy IRC add-on.

## Components

1.  **IRC Server**: InspIRCd (Dockerized) running on port 6667 (internal) and 8080 (WebSocket).
2.  **IRC Client**: A React component (`IrcClient.tsx`) integrated into the Devussy frontend.

## Setup

The IRC services are defined in `docker-compose.yml`. To start them:

```bash
docker-compose up -d ircd
```

Ensure your `.env` file (or environment) has the following variables for the frontend:

```
NEXT_PUBLIC_IRC_WS_URL=wss://dev.ussy.host/ws/irc/
NEXT_PUBLIC_IRC_CHANNEL=#devussy-chat
```

## Configuration

### InspIRCd (`conf/inspircd_v2.conf`)
- **Modules**: Loads `m_websocket.so` and `m_sha1.so` (required for handshake).
- **Ports**: Listens on 6667 (IRC) and 8080 (WebSocket).
- **DNS**: DNS resolution is disabled to prevent issues with Docker hostnames.
- **Ping Frequency**: Set to 15s to quickly detect and remove ghost connections.

### Nginx Proxy
- Proxies WebSocket connections from `/ws/irc/` to `ircd:8080`.
- Handles SSL termination.

### Compose / nginx overlay workflow

- The IRC `ircd` service is defined in the base `devussy-web/docker-compose.yml`
  and remains the ground truth for the IRC container.
- The app framework can also generate an overlay file
  `docker-compose.apps.generated.yml` (via `scripts/generate-compose.ts`) that
  adds app-defined services and an nginx fragment at
  `nginx/conf.d/apps.generated.conf`.
- When running with Docker apps, you typically combine the two files with:
  `docker compose -f docker-compose.yml -f docker-compose.apps.generated.yml up`.
- The frontend IRC client continues to use `NEXT_PUBLIC_IRC_WS_URL` pointing at
  the canonical `/ws/irc/` WebSocket path; the generated nginx fragment may add
  an additional `/apps/irc/ws/` alias that routes to the same backend.

## Usage

1.  Open Devussy Studio.
2.  Click "IRC Chat" in the Taskbar or Start Menu.
3.  Enter a nickname if prompted (defaults to Guest).
4.  Chat!

### Demo Mode
If the IRC server is unreachable, the client will automatically switch to "Demo Mode" after connection failures. This simulates a chat environment for UI testing.

### Persistence
- Nickname and the last 50 messages are saved in `localStorage`.

## Troubleshooting

- **Connection Refused**: Ensure `ircd` container is running and port 8080 is accessible.
- **503 Service Unavailable**: Check Nginx logs. Ensure Nginx can resolve the `ircd` hostname.
- **Nickname in Use**: The client automatically handles this by appending an underscore (`_`) to your nickname and retrying.
- **Ghost Users**: If you reload the page, your previous session might stay active for ~15 seconds until the server times it out.

