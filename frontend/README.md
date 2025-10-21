# DevPlan Orchestrator - Frontend

React + TypeScript frontend for DevPlan Orchestrator web interface.

## Status

🚧 **In Development** - Backend is complete, frontend components need implementation

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open browser
# Visit: http://localhost:3000
```

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Zustand** - State management
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code highlighting

## Project Structure

```
src/
├── main.tsx              # Entry point
├── App.tsx               # Main app component with routing
├── index.css             # Global styles
├── components/           # Reusable components (TO BE CREATED)
│   ├── Layout.tsx        # Layout with header, nav, footer
│   ├── Header.tsx        # App header
│   ├── Navigation.tsx    # Navigation menu
│   └── ...
├── pages/                # Page components (TO BE CREATED)
│   ├── HomePage.tsx      # Landing page
│   ├── CreateProjectPage.tsx  # Project creation form (PRIORITY)
│   ├── ProjectDetailPage.tsx  # Project detail with streaming
│   └── ProjectsListPage.tsx   # Project list/dashboard
├── services/             # API services (TO BE CREATED)
│   └── api.ts            # Axios client for backend API
├── hooks/                # Custom React hooks (TO BE CREATED)
│   ├── useProjectStream.ts    # WebSocket streaming hook
│   └── useApi.ts         # API call hook
├── stores/               # Zustand stores (TO BE CREATED)
│   └── projectStore.ts   # Project state management
├── types/                # TypeScript types (TO BE CREATED)
│   └── index.ts          # Shared types
└── utils/                # Utilities (TO BE CREATED)
    └── index.ts          # Helper functions
```

## What Needs To Be Built

### Priority 1: Core Components (Day 1)

**Layout Component** (`src/components/Layout.tsx`)
- Header with logo and navigation
- Main content area
- Footer
- Responsive design

**API Service** (`src/services/api.ts`)
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

export const createProject = (data: ProjectCreateRequest) => 
  api.post('/projects/', data)

export const getProject = (id: string) => 
  api.get(`/projects/${id}`)

// ... more methods
```

**Home Page** (`src/pages/HomePage.tsx`)
- Hero section with description
- "Create New Project" CTA button
- Features list
- Link to documentation

### Priority 2: Project Creation (Day 2)

**Create Project Page** (`src/pages/CreateProjectPage.tsx`)
- Multi-step form wizard:
  - Step 1: Project basics (name, type, languages)
  - Step 2: Tech stack (frameworks, database, APIs)
  - Step 3: Features (auth, testing, CI/CD, deployment)
  - Step 4: Review and submit
- Form validation
- Progress indicator
- Back/Next navigation
- Submit to API

**Form Data:**
```typescript
interface ProjectFormData {
  name: string
  project_type: 'web_app' | 'api' | 'cli' | ...
  languages: string[]
  requirements: string
  frameworks: string[]
  apis: string[]
  database?: string
  authentication?: boolean
  // ... more fields
}
```

### Priority 3: Real-Time Streaming (Day 3)

**Project Detail Page** (`src/pages/ProjectDetailPage.tsx`)
- Project status display
- Stage indicators (Design → DevPlan → Handoff)
- Progress bar (0-100%)
- Real-time streaming output
- Generated files list
- Action buttons (cancel, download, copy)

**WebSocket Hook** (`src/hooks/useProjectStream.ts`)
```typescript
export const useProjectStream = (projectId: string) => {
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState('connecting')
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/ws/${projectId}`)
    
    ws.onopen = () => setStatus('connected')
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'token') {
        // Add token to display
      } else if (msg.type === 'progress') {
        // Update progress
      }
    }
    ws.onerror = () => setStatus('error')
    ws.onclose = () => setStatus('disconnected')
    
    return () => ws.close()
  }, [projectId])
  
  return { messages, status }
}
```

### Priority 4: File Viewer (Day 4)

**File Viewer Component**
- Tabs for each file (design.md, devplan.md, handoff.md)
- Markdown rendering with `react-markdown`
- Syntax highlighting for code blocks
- Copy button
- Download button

### Priority 5: Project List (Day 4)

**Projects List Page** (`src/pages/ProjectsListPage.tsx`)
- Table or cards of recent projects
- Status badges (completed, running, failed)
- Filters (by status)
- Search
- Quick actions (view, delete)

## Development

### Available Scripts

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### API Integration

The backend API runs on `http://localhost:8000`. The Vite dev server proxies `/api` requests to the backend.

**Example API Calls:**
```typescript
// Create project
const response = await api.post('/projects/', {
  name: 'My Project',
  project_type: 'web_app',
  languages: ['Python', 'TypeScript'],
  requirements: 'Build something cool'
})

// Get project
const project = await api.get(`/projects/${projectId}`)

// List files
const files = await api.get(`/files/${projectId}`)

// Download file
const file = await api.get(`/files/${projectId}/project_design.md`)
```

**WebSocket Connection:**
```typescript
const ws = new WebSocket(`ws://localhost:8000/api/ws/${projectId}`)

ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  
  switch (message.type) {
    case 'token':
      // Display streaming token
      console.log(message.data.token)
      break
    case 'progress':
      // Update progress bar
      console.log(`Progress: ${message.data.progress}%`)
      break
    case 'stage':
      // Update stage indicator
      console.log(`Stage: ${message.data.stage}`)
      break
    case 'complete':
      // Pipeline completed
      console.log('Done!')
      break
  }
}
```

## Styling

Using Tailwind CSS with custom theme in `tailwind.config.js`.

**Utility Classes:**
- `.btn-primary` - Primary button
- `.btn-secondary` - Secondary button
- `.input` - Form input
- `.card` - Card container

**Example:**
```tsx
<button className="btn-primary">
  Create Project
</button>

<input className="input" type="text" placeholder="Project name" />

<div className="card">
  <h2>Project Details</h2>
</div>
```

## Testing

```bash
# Run tests (when implemented)
npm test

# Run E2E tests
npm run test:e2e
```

## Resources

- **Backend API Docs:** http://localhost:8000/docs
- **WEB_INTERFACE_GUIDE.md** - Complete setup guide
- **WEB_INTERFACE_SUMMARY.md** - Development session summary
- **src/web/models.py** - API request/response types

## Tips

1. **Check the backend models** (`src/web/models.py`) to see exact API shapes
2. **Use the API docs** (http://localhost:8000/docs) to test endpoints
3. **Reference interactive CLI** (`src/interactive.py`) for questions to ask
4. **Start with HomePage** - easiest component to build confidence
5. **Build incrementally** - get one page working before moving to next

## Help

If you run into issues:
- Check backend is running: http://localhost:8000/health
- Check console for errors
- Verify API calls in Network tab
- Read WEB_INTERFACE_GUIDE.md for troubleshooting

---

**Status:** 🚧 Scaffolding complete, components need implementation  
**Next Step:** Create `src/components/Layout.tsx` and `src/pages/HomePage.tsx`  
**Priority:** Project creation form for layman-friendly UI
