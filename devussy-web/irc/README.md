# Devussy IRC Add-on

This directory contains the configuration and documentation for the Devussy IRC add-on.

## Components

1.  **IRC Server**: InspIRCd (Dockerized) running on port 6667 (internal).
2.  **IRC Gateway**: KiwiIRC WebIRC Gateway (Dockerized) running on port 8080 (mapped to host).
3.  **IRC Client**: A React component (`IrcClient.tsx`) integrated into the Devussy frontend.

## Setup

The IRC services are defined in `docker-compose.yml`. To start them:

```bash
docker-compose up -d irc-server irc-gateway
```

Ensure your `.env` file (or environment) has the following variables for the frontend:

```
NEXT_PUBLIC_IRC_WS_URL=ws://localhost:8080
NEXT_PUBLIC_IRC_CHANNEL=#devussy
```

## Configuration

### InspIRCd (`conf/inspircd.conf`)
- Configured to listen on 6667.
- Loads `m_webirc.so` for gateway integration.
- **Important**: The `<cgihost>` password must match the gateway configuration.

### WebIRC Gateway (`gateway.conf`)
- Listens on 8080 for WebSocket connections.
- Forwards to `irc-server:6667`.
- Uses the configured WebIRC password.

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

- **Connection Refused**: Ensure `irc-gateway` container is running and port 8080 is accessible.
- **Demo Mode only**: Check browser console for WebSocket errors. Ensure `NEXT_PUBLIC_IRC_WS_URL` matches your setup.
