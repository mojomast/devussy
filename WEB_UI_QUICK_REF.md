# Web UI Quick Reference

**Version:** 0.3.0-alpha  
**Status:** Fully Functional

---

## 🚀 Quick Start

```powershell
# Start backend (Terminal 1)
python -m src.web.app
# Running at http://localhost:8000

# Start frontend (Terminal 2)
cd frontend
npm run dev
# Running at http://localhost:3000
```

---

## 📁 File Structure

```
frontend/src/
├── services/
│   ├── configApi.ts          # Configuration API client
│   └── projectsApi.ts         # Projects API client (NEW!)
├── pages/
│   ├── HomePage.tsx           # Dashboard (UPDATED!)
│   ├── SettingsPage.tsx       # Settings with tabs
│   ├── ProjectsListPage.tsx   # Projects grid (NEW!)
│   ├── ProjectDetailPage.tsx  # Real-time monitoring (NEW!)
│   └── CreateProjectPage.tsx  # Project creation form (NEW!)
├── components/
│   ├── Layout.tsx             # Main layout
│   └── config/                # Settings components
└── App.tsx                    # Router setup
```

---

## 🔌 API Endpoints

### Projects API (`/api/projects`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create new project |
| GET | `/` | List projects (with filtering) |
| GET | `/{id}` | Get project details |
| DELETE | `/{id}` | Delete project |
| POST | `/{id}/cancel` | Cancel running project |
| GET | `/{id}/files/{filename}` | Get file content |
| WS | `/api/ws/projects/{id}` | Real-time updates |

### Configuration API (`/api/config`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/credentials` | Create credential |
| GET | `/credentials` | List credentials |
| PUT | `/credentials/{id}` | Update credential |
| DELETE | `/credentials/{id}` | Delete credential |
| POST | `/credentials/{id}/test` | Test credential |
| GET | `/global` | Get global config |
| PUT | `/global` | Update global config |
| GET | `/presets` | List presets |
| POST | `/presets/apply/{id}` | Apply preset |

---

## 🎨 Pages Overview

### HomePage (`/`)
- Dashboard with recent projects
- Configuration status check
- Feature showcase
- Quick action buttons
- **Status:** ✅ Complete

### ProjectsListPage (`/projects`)
- Grid of all projects
- Status filtering
- Search functionality
- Create/delete actions
- **Status:** ✅ Complete

### ProjectDetailPage (`/projects/:id`)
- Real-time progress monitoring
- WebSocket streaming
- Live logs console
- File content viewer
- Cancel/delete actions
- **Status:** ✅ Complete

### CreateProjectPage (`/create`)
- Project creation form
- Configuration validation
- Git & streaming options
- Form validation
- **Status:** ✅ Complete

### SettingsPage (`/settings`)
- Credentials management
- Global configuration
- Presets
- **Status:** ✅ Complete

---

## 🔄 WebSocket Protocol

### Connection
```typescript
const ws = new WebSocket(`ws://localhost:8000/api/ws/projects/${projectId}`);
```

### Message Format
```typescript
{
  type: 'progress' | 'stage' | 'output' | 'error' | 'complete',
  data: any
}
```

### Message Types

**progress:**
```typescript
{ type: 'progress', data: { progress: 45 } }
```

**stage:**
```typescript
{ type: 'stage', data: { stage: 'DEVPLAN' } }
```

**output:**
```typescript
{ type: 'output', data: { text: 'Generating...' } }
```

**error:**
```typescript
{ type: 'error', data: { error: 'Something went wrong' } }
```

**complete:**
```typescript
{ type: 'complete', data: { files: {...} } }
```

---

## 🎯 TypeScript Types

### ProjectResponse
```typescript
interface ProjectResponse {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  current_stage?: PipelineStage;
  progress: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error?: string;
  output_dir: string;
  config_id?: string;
  files: {
    design?: string;
    devplan?: string;
    handoff?: string;
  };
}
```

### ProjectCreateRequest
```typescript
interface ProjectCreateRequest {
  name: string;
  description: string;
  config_id?: string;
  options?: {
    enable_git?: boolean;
    enable_streaming?: boolean;
    output_dir?: string;
  };
}
```

---

## 🎨 Common Patterns

### Loading State
```typescript
const [loading, setLoading] = useState(true);
const [data, setData] = useState(null);
const [error, setError] = useState(null);

useEffect(() => {
  loadData();
}, []);

const loadData = async () => {
  try {
    setLoading(true);
    setError(null);
    const result = await api.getData();
    setData(result);
  } catch (err: any) {
    setError(err.response?.data?.detail || 'Failed');
  } finally {
    setLoading(false);
  }
};
```

### Status Badge
```typescript
const getStatusColor = (status: ProjectStatus) => {
  switch (status) {
    case ProjectStatus.COMPLETED:
      return 'bg-green-100 text-green-800';
    case ProjectStatus.RUNNING:
      return 'bg-blue-100 text-blue-800';
    case ProjectStatus.FAILED:
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};
```

### WebSocket Setup
```typescript
useEffect(() => {
  const ws = projectsApi.createWebSocket(projectId);
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
  };
  
  return () => ws.close();
}, [projectId]);
```

---

## 🧪 Testing Checklist

### Manual Testing
- [ ] Create project without credentials (should warn)
- [ ] Create project with credentials (should work)
- [ ] View projects list with filtering
- [ ] Monitor real-time progress
- [ ] View generated files
- [ ] Cancel running project
- [ ] Delete completed project
- [ ] Test all status filters
- [ ] Check responsive design
- [ ] Verify error handling

### Automated Testing (TODO)
- [ ] Component tests for all pages
- [ ] API integration tests
- [ ] WebSocket tests
- [ ] E2E workflow tests

---

## 🐛 Known Issues

1. **WebSocket Reconnection:** No auto-reconnect if connection drops
2. **Markdown Rendering:** Files display as plain text, not rendered
3. **No Caching:** API calls repeated on every page load
4. **No Debouncing:** Search/filter triggers immediate API calls

---

## 💡 Next Steps

### Priority 1: Testing
- Set up Vitest
- Write component tests
- Add E2E tests

### Priority 2: Polish
- Loading skeletons
- Toast notifications
- Better error boundaries

### Priority 3: Features
- Markdown rendering
- Dark mode
- Export functionality
- Search improvements

---

## 📚 Resources

- **API Docs:** `WEB_INTERFACE_GUIDE.md`
- **Session Notes:** `SESSION_SUMMARY_OCT21_WEB_UI.md`
- **Handoff:** `HANDOFF.md`
- **Architecture:** `docs/ARCHITECTURE.md`

---

**Last Updated:** October 21, 2025  
**Maintained By:** Development Team
