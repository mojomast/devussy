DevPlan: Adding an IRC Add‑on to the Devussy Front‑end (devussy‑testing)
Context

The devussy‑testing branch of the Devussy project does not contain any IRC client or server integration. The front‑end window system currently defines window types such as 'init', 'interview', 'design', 'plan', 'execute', 'handoff', 'help' and 'model‑settings'
raw.githubusercontent.com
, and the size switch in getWindowSize lacks an 'irc' entry
raw.githubusercontent.com
. The docker‑compose.yml in this branch defines only the frontend, streaming‑server and nginx services
raw.githubusercontent.com
 without any IRC server or gateway containers. Therefore, an IRC add‑on must be implemented from scratch for this branch.

Objectives

Implement a React/Next.js IRC client as an add‑on window. The client must provide a chat interface, user list, nickname change, reconnection logic and a demo mode fallback.

Containerize an IRC daemon and WebSocket gateway using Docker. The server will run InspIRCd with a WebIRC gateway (KiwiIRC’s webircgateway) to translate WebSocket messages to IRC. The services should be added to docker‑compose.yml alongside existing services.

Integrate the IRC client into the Devussy front‑end by registering a new window type 'irc', adding an item to the taskbar/start menu, and optionally auto‑launching the chat window on page load.

Provide configuration, documentation and tests to ensure maintainability and reproducibility.

High‑Level Architecture
Component	Purpose	Implementation
IRC Client	A React functional component rendered inside a Devussy window. Connects via WebSocket to the IRC gateway, sends JSON commands (NICK, JOIN, PRIVMSG) and renders messages, join/part notices and system messages. Supports nickname changes, user list, reconnect logic and demo mode.	New file devussy-web/src/components/addons/irc/IrcClient.tsx using shadcn UI components.
IRC Server (InspIRCd)	Provides IRC protocol implementation and manages channels, users and modes. Configuration stored in devussy-web/irc/conf/inspircd.conf.	Docker container inspircd/inspircd-docker:latest.
WebIRC Gateway	Translates WebSocket connections to IRC commands and back. Reads configuration from gateway.conf defining the IRC server host and WebSocket listener.	Docker container kiwiirc/webircgateway:latest.
Docker Compose	Orchestrates the front‑end, streaming server, nginx, IRC server and gateway. Adds new services for irc-server and irc-gateway with proper volumes and environment variables.	Update devussy-web/docker-compose.yml.
Nginx Proxy	Optionally proxy WebSocket connections from /ws/irc to the irc-gateway service to expose a single HTTPS endpoint.	Update devussy-web/nginx/nginx.conf.
Detailed Design
1. Implementing the IRC Client

New component – Create devussy-web/src/components/addons/irc/IrcClient.tsx. Use useState to track messages, users, nickname and connection state. Use useEffect to establish a WebSocket connection on mount and to perform cleanup on unmount. The connection URL should come from NEXT_PUBLIC_IRC_WS_URL with a sensible fallback such as wss://localhost:8080.

Joining the channel – After the WebSocket connection is opened, send NICK <nickname> and JOIN <channel> commands encoded as JSON. Nicknames may come from local storage or be randomly generated. Support PRIVMSG for sending messages and handle incoming events such as PRIVMSG, JOIN, PART, NICK and 353 (name list).

Demo mode – If the connection cannot be established within a timeout (e.g. 3 s), switch to a demo mode that generates simulated users and messages. Display a banner indicating the chat is in demo mode. This ensures the UI remains functional even when the IRC services are unavailable.

User interface – Use shadcn components (Card, ScrollArea, Input, Button) to build the chat UI. Display messages with timestamps and differentiate join/part/system messages by colour. Include a user list sidebar and a nickname change dialog with validation (e.g. maximum 30 characters). The chat window should automatically scroll to the newest message.

Reconnection logic – On disconnect, attempt to reconnect with exponential backoff, up to three attempts. After repeated failures, notify the user or switch to demo mode. Reconnect gracefully when the page regains focus or network connectivity.

2. Front‑End Integration

Window type – Add 'irc' to the WindowType union in src/app/page.tsx and update the getWindowSize switch to return a suitable default (e.g., { width: 800, height: 600 }) for 'irc'
raw.githubusercontent.com
.

Spawning the window – Implement a handleOpenIrc function in page.tsx. It should:

Check whether an IRC window already exists; if so, bring it to the front and optionally toggle minimization.

If not, call spawnWindow('irc', 'IRC Chat – #devussy') to create a new window. The props can be used to pass configuration to the IRC client.

Optionally minimize the window immediately after spawning to avoid disrupting the user experience.

Taskbar and start menu – Add an option to open the IRC chat in the taskbar or start menu. For example, import MessageSquare icon and insert a button labelled “IRC Chat” that calls handleOpenIrc. Ensure the icon matches the theme.

Auto‑launch (optional) – Use a useEffect hook to automatically spawn (and minimize) the IRC window after the page loads. Provide a user preference stored in localStorage (e.g., devussy_auto_launch_irc) to disable auto‑launch.

Persistence – Store the current nickname and last 50 messages in localStorage so that the IRC state persists across page reloads. Clear the storage only when the user explicitly disconnects or leaves the channel.

3. Containerizing the IRC Server and Gateway

Directory structure – Create devussy-web/irc/ with subdirectories:

conf/ – configuration files for InspIRCd, including inspircd.conf. Include modules m_webirc.so and m_cgiirc.so, define a <cgihost> entry for WebIRC and set a secure operator password. Document the meaning of each directive.

logs/ – host volume for server logs.

data/ – persistent storage for server state (e.g., certificates, user data).

gateway.conf – configuration for KiwiIRC webircgateway. Define the IRC server host as irc-server, port 6667, and set the WebSocket listener on 0.0.0.0:8080. Tune heartbeat and nickname/channel length limits.

docker‑compose changes – Extend devussy-web/docker-compose.yml by adding two new services:

irc-server:
  image: inspircd/inspircd-docker:latest
  container_name: devussy-irc-server
  ports:
    - "6667:6667"  # plain IRC
    - "6697:6697"  # TLS if enabled
  volumes:
    - ./irc/conf:/inspircd/conf
    - ./irc/logs:/inspircd/logs
    - ./irc/data:/inspircd/data
  command: ["/inspircd/conf/inspircd.conf"]
  restart: unless-stopped

irc-gateway:
  image: kiwiirc/webircgateway:latest
  container_name: devussy-irc-gateway
  ports:
    - "8080:8080"
  environment:
    - GATEWAY_CONFIG=/kiwiirc/webircgateway.conf
  volumes:
    - ./irc/gateway.conf:/kiwiirc/webircgateway.conf
  depends_on:
    - irc-server
  restart: unless-stopped


These services do not exist in the current docker-compose.yml
raw.githubusercontent.com
 and must be added after the existing frontend and streaming-server definitions.

Environment variables – Add NEXT_PUBLIC_IRC_WS_URL and NEXT_PUBLIC_IRC_CHANNEL to .env.example and document them. In frontend.Dockerfile, ensure these variables are passed into the container at runtime. In docker-compose.yml, set defaults such as:

frontend:
  environment:
    - NEXT_PUBLIC_IRC_WS_URL=ws://localhost:8080
    - NEXT_PUBLIC_IRC_CHANNEL=#devussy
    ...


Nginx reverse proxy (optional) – If you want to expose the gateway through nginx, add a location block to devussy-web/nginx/nginx.conf:

location /ws/irc/ {
  proxy_pass http://irc-gateway:8080/;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "Upgrade";
  proxy_read_timeout 86400;
}


Then set NEXT_PUBLIC_IRC_WS_URL=wss://<your-domain>/ws/irc/ in .env.example for production.

4. Configuration and Environment

.env.example updates – Add placeholders for NEXT_PUBLIC_IRC_WS_URL and NEXT_PUBLIC_IRC_CHANNEL below the existing variables. Document that these variables configure the IRC client connection and default channel.

frontend.Dockerfile – No changes are strictly required, but document that environment variables starting with NEXT_PUBLIC_ will be available to the client at build time. The docker-compose file should pass these variables when building/running the frontend service.

Security considerations – Use a strong WEBIRC_PASSWORD (for the <cgihost> entry) and operator password in inspircd.conf. Avoid exposing the raw IRC ports publicly; rely on the gateway and nginx to handle WebSocket connections.

5. Testing and Quality Assurance

Unit tests – Create tests for parsing and handling IRC messages. Mock the WebSocket interface to simulate various server events (e.g., join, part, message, nick change). Use Jest for testing React hooks and state updates.

Integration tests – Use Playwright or Cypress to start the docker compose stack and run a browser test: open Devussy, spawn the IRC window, send a message and assert that it appears in the chat. Simulate network failure to verify that demo mode activates.

Manual QA – Validate dark/light theme support, responsiveness of the chat UI, nickname changes, user list updates and auto‑reconnect. Verify that the taskbar and start menu correctly open and focus the chat window.

6. Documentation

README modifications – In the root README or a new devussy-web/addons/irc/README.md, explain how to enable the IRC add‑on. Provide instructions for starting the IRC services with Docker, configuring environment variables, and connecting to the chat from the Devussy UI.

Configuration docs – Comment the inspircd.conf and gateway.conf files explaining each option (e.g., modules loaded, limits and passwords). Provide guidance on generating SSL certificates if TLS is enabled.

User guide – Describe how to open the IRC chat from the taskbar/start menu, how to change nicknames, how to disable auto‑launch and how demo mode works.

Implementation Timeline

The following phases assume a single developer or small team and should be adjusted based on resource availability:

Scaffolding (≈1 day)

Create irc directory structure and configuration files with secure defaults.

Extend docker-compose.yml to include irc-server and irc-gateway services.

Add environment variables to .env.example and update documentation accordingly.

Build and run the stack locally using docker-compose up; verify that the IRC server accepts connections (e.g., via an external IRC client connecting to localhost:6667).

Client development (≈2 days)

Implement IrcClient.tsx with WebSocket connection, message handling, user list, nickname changes and demo mode.

Add 'irc' to WindowType, update getWindowSize and implement handleOpenIrc in page.tsx.

Modify the taskbar/start menu to include an “IRC Chat” launcher.

Implement auto‑launch with a user preference and persist chat state in localStorage.

Integration and testing (≈1 day)

Integrate environment variables into the Next.js build and verify that the client connects to the gateway via the configured URL.

Write Jest unit tests and at least one E2E test with Playwright/Cypress. Run tests in CI with the full docker stack.

Adjust styling to match the Devussy design system and ensure accessibility (e.g., keyboard navigation and ARIA labels).

Documentation and polish (≈½ day)

Update README and configuration comments.

Add screenshots or GIFs demonstrating the chat feature.

Conduct final manual QA and fix any usability issues or bugs.

Conclusion

By following this plan, developers can introduce a fully functional IRC chat into the devussy‑testing branch without disrupting existing features. The plan covers creating the IRC server and WebSocket gateway, adding a comprehensive chat component, integrating the new window into the existing window manager, and updating configuration, documentation and tests. Once completed, users will be able to collaborate in real time while generating designs and plans within Devussy.