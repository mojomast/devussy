# Devussy Web Frontend

A Next.js-based web interface for Devussy, featuring real-time streaming, multi-window execution, and concurrent phase generation.

## 🎉 Status: Production Ready

All core features are implemented and fully functional:
- ✅ Interactive interview with streaming
- ✅ Design generation with real-time output
- ✅ Development plan with editable phase cards
- ✅ **Concurrent multi-phase execution** with live streaming
- ✅ Complete artifact download with phase documents
- ✅ Window management and taskbar
- ✅ Per-stage model configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Installation

1. **Install Python dependencies** (from project root):
```bash
pip install -e .
```

2. **Install frontend dependencies**:
```bash
cd devussy-web
npm install
```

### Running the Application

1. **Start the backend server** (port 8000):
```bash
# From devussy-web directory
python dev_server.py
```

2. **Generate App Configuration** (optional, for IRC/Apps):
```bash
# From devussy-web/, generates docker-compose.apps.generated.yml and nginx config
npm run generate:compose
# or, if you prefer using npx directly:
# npx ts-node scripts/generate-compose.ts
```

This script reads app-level `services` / `proxy` / `env` metadata from
`src/apps/AppRegistry` and writes:

- `docker-compose.apps.generated.yml` – additional app-provided services and a
  `frontend` environment overlay
- `nginx/conf.d/apps.generated.conf` – nginx `location` blocks for any
  app-defined proxies

It is **non-destructive**: it never modifies `docker-compose.yml` or
`nginx/nginx.conf`; you always layer the generated compose file on top of the
handwritten base.

3. **Start the frontend** (port 3000):
```bash
# Standard dev mode
npm run dev
```

4. **Run with Docker Apps (IRC, etc)**:
```bash
# To include generated app services:
docker compose -f docker-compose.yml -f docker-compose.apps.generated.yml up
```

This command overlays any app-defined services (for example the IRC `ircd`
container) on top of the base stack. The base `docker-compose.yml` and
`nginx/nginx.conf` remain the source of truth; the generated nginx fragment
adds optional aliases such as `/apps/irc/ws/` that point to the same IRC
backend as the canonical `/ws/irc/` path.

3. **Open browser**:
```
http://localhost:3000
```

## 📋 Features

### Interview Phase
- Interactive questionnaire with LLM-driven questions
- Real-time streaming responses
- Repository analysis for existing projects
- Context-aware question generation

### Design Phase
- Streaming design document generation
- Editable markdown output
- Approve/regenerate functionality
- Saves design for next phase

### Plan Phase
- Streaming development plan generation
- **Editable phase cards** with full content
- Add, edit, delete, and reorder phases
- Auto-scrolling terminal output
- Proper connection cleanup for phases 7+

### Handoff Phase
- Automatic handoff documentation generation
- **Complete artifact download** including:
  - Project design document
  - Development plan JSON
  - Handoff instructions
  - **Individual phase documents** with detailed steps
- GitHub integration (optional)

### Window Management
- Multiple windows for each phase
- Draggable and minimizable windows
- Z-index management (click to focus)
- Taskbar for quick window switching
- Persistent window state

### Model Configuration
- Global settings with per-stage overrides
- Temperature control (0.0 - 2.0)
- Reasoning effort (low/medium/high)
- Concurrency control for execution
- Multiple LLM provider support

### HiveMind Mode 🐝 NEW
A multi-agent swarm generation system that provides diverse perspectives on any phase:

### IRC Chat 💬 NEW
Real-time collaboration directly within the Devussy interface:
- **Native WebSocket Support**: Connects directly to InspIRCd via secure WebSocket.
- **Multi-Channel Support**: Join multiple channels and private message users.
- **Persistent State**: Remembers your nickname and recent messages.
- **Auto-Retry**: Automatically handles nickname collisions and reconnections.
- **Demo Mode**: Fallback mode for UI testing when server is unavailable.

**How It Works:**
- Click "IRC Chat" in the Taskbar or Start Menu.
- Enter a nickname (or use the generated one).
- Start chatting in `#devussy-chat`.

**How It Works:**
- Click "🐝 Hive Mode" on any phase card (available for all statuses)
- Opens a 4-pane real-time streaming window:
  - **Drone 1** (Cyan): Temperature-varied analysis
  - **Drone 2** (Purple): Alternative perspective  
  - **Drone 3** (Orange): Third viewpoint
  - **Arbiter** (Green): Synthesizes consensus from all drones

**Use Cases:**
- Generate multiple approaches for complex phases
- Re-evaluate completed phases with swarm intelligence
- Compare single-agent vs multi-agent results
- Refine phases before or after standard generation

**Technical Details:**
- Streams all 4 agents simultaneously via Server-Sent Events (SSE)
- Drones execute sequentially with temperature jitter (0.5-1.0)
- Arbiter synthesizes consensus using specialized prompt template
- Backward compatible with existing pipeline (optional feature)

**Configuration:**
Backend: `src/config.py` → `HiveMindConfig`
```yaml
hivemind:
  enabled: true
  drone_count: 3
  temperature_jitter: true
```

## 🏗️ Architecture

### Tech Stack
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Shadcn UI
- **Icons**: Lucide React
- **Backend**: Python with ThreadingHTTPServer
- **Streaming**: Server-Sent Events (SSE)
- **Concurrency**: Async event loops per thread

### Project Structure
```
devussy-web/
├── src/
│   ├── app/
│   │   └── page.tsx              # Main app with window management
│   ├── components/
│   │   ├── pipeline/
│   │   │   ├── InterviewView.tsx # Interview phase
│   │   │   ├── DesignView.tsx    # Design generation
│   │   │   ├── PlanView.tsx      # Plan with editable cards
│   │   │   ├── ExecutionView.tsx # Concurrent execution
│   │   │   ├── HiveMindView.tsx  # Multi-agent swarm (4-pane)
│   │   │   ├── HandoffView.tsx   # Artifact download
│   │   │   └── ModelSettings.tsx # Configuration UI
│   │   ├── window/
│   │   │   ├── WindowFrame.tsx   # Window wrapper
│   │   │   └── Taskbar.tsx       # Window taskbar
│   │   └── ui/                   # Shadcn UI components
│   └── lib/
│       └── utils.ts              # Utility functions
├── api/
│   ├── design.py                 # Design generation
│   ├── plan/
│   │   ├── basic.py             # Plan structure
│   │   ├── detail.py            # Phase details
│   │   └── hivemind.py          # HiveMind multi-stream SSE
│   ├── handoff.py               # Handoff generation
│   ├── interview.py             # Interview flow
│   └── models.py                # Available models
├── dev_server.py                 # Local Python server
└── public/                       # Static assets
```

### Backend Integration
- ThreadingHTTPServer for concurrent requests
- Per-thread async event loops (no conflicts)
- SSE streaming with proper connection cleanup
- CORS handling for all endpoints

## 🔧 Configuration

### Backend Configuration
Edit `config/config.yaml`:
```yaml
llm:
  provider: requesty  # or openai, aether, etc.
  model: gpt-5-mini
  temperature: 0.7
  streaming_enabled: true
```

### Frontend Configuration
Model settings available in UI:
- Global defaults
- Per-stage overrides (Interview, Design, Plan, Execute, Handoff)
- Temperature, reasoning effort, concurrency

## 🐛 Troubleshooting

### Phases Stall After 3
**Solution**: Restart Python backend
```bash
# Kill existing process
# Restart
python dev_server.py
```

### Empty Phase Documents
**Solution**: Ensure backend restarted after code changes
- Phase data flows: ExecutionView → Parent → HandoffView
- Check browser console for phase completion logs

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/api/models

# Restart backend
python dev_server.py
```

### Streaming Not Working
1. Check browser console for errors
2. Verify backend logs show streaming
3. Check Network tab for SSE messages
4. Ensure proper newlines in SSE format (`\n\n`)

## 📚 Key Technical Fixes

### Backend
- ✅ Fixed asyncio event loop conflicts (per-thread loops)
- ✅ Proper SSE connection cleanup with `reader.cancel()`
- ✅ ThreadingHTTPServer for concurrent handling
- ✅ Event loop creation/cleanup in finally blocks

### Frontend
- ✅ Removed concurrency queueing - start all phases
- ✅ Fixed React setState during render
- ✅ Proper phase data flow with detailed steps
- ✅ Auto-scrolling terminal output
- ✅ Debounced UI updates (50ms)
- ✅ Connection cleanup to free browser slots

## 🧪 Testing

### Manual Testing Flow
1. Start both servers
2. Complete pipeline: Interview → Design → Plan → Execute → Handoff
3. Verify all phases stream concurrently
4. Download artifacts and check phase documents
5. Verify phase docs contain detailed steps

### Expected Behavior
- **Interview**: Questions stream in real-time
- **Design**: Design document streams progressively
- **Plan**: Plan streams, shows editable cards
- **Execute**: All phases start immediately, stream concurrently
- **Handoff**: Downloads zip with all artifacts including phase docs

## 🎯 Known Issues

None critical - all major functionality working.

### Minor Notes
- Browser connection limit (~6) naturally throttles concurrent phases
- Phases 7+ start automatically as earlier phases complete
- React dev mode may show double renders (normal)

## 🚀 Future Enhancements

### Short Term
- [ ] Save/load project state
- [ ] Export to different formats
- [ ] Enhanced error recovery UI
- [ ] Phase dependency visualization

### Long Term
- [ ] Template library
- [ ] Collaborative editing
- [ ] Real-time collaboration
- [ ] Advanced GitHub integration

## 📝 Development Notes

### Key Implementation Details

1. **Async Event Loops**: Each thread gets its own loop
   ```python
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   try:
       loop.run_until_complete(generate_stream())
   finally:
       loop.close()
   ```

2. **Connection Cleanup**: Always cancel readers
   ```typescript
   try {
       reader.cancel();
   } catch (e) {
       // Already closed
   }
   ```

3. **Phase Data Flow**: ExecutionView stores detailed phases
   ```typescript
   detailedPhase: data.phase  // From backend
   ```

4. **SSE Format**: Actual newlines required
   ```python
   self.wfile.write(f"data: {data}\n\n".encode('utf-8'))
   ```

### Debugging

Enable verbose logging:
```typescript
// Frontend
console.log('[ExecutionView] ...');

// Backend
print(f"[detail.py] ...")
```

Check logs in:
- Browser console (F12)
- Backend terminal
- Network tab (SSE events)

## 🤝 Contributing

1. Follow existing code style
2. Add comprehensive logging
3. Test streaming thoroughly
4. Update documentation
5. Verify end-to-end flow

## 📄 License

Same as parent Devussy project.

## 🙏 Acknowledgments

Built with:
- Next.js 15
- Shadcn UI
- Tailwind CSS
- Lucide Icons
- Python backend with asyncio

---

**Status**: Production-ready ✅  
**Last Updated**: 2025-11-19  
**Version**: 1.0.0
