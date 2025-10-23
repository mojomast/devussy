# Configuration System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WEB INTERFACE USER                               │
│                    (Non-technical user using browser)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + TypeScript)                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        SettingsPage.tsx                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ Credentials  │  │   Global     │  │   Presets    │          │   │
│  │  │     Tab      │  │  Config Tab  │  │     Tab      │          │   │
│  │  │              │  │              │  │              │          │   │
│  │  │ • Add Key    │  │ • Select     │  │ • Cost       │          │   │
│  │  │ • Test Key   │  │   Model      │  │   Optimized  │          │   │
│  │  │ • Delete     │  │ • Configure  │  │ • Max        │          │   │
│  │  │   Key        │  │   Stages     │  │   Quality    │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                       │
│                                  │ configApi.ts                          │
│                                  ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CreateProjectPage.tsx                         │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │  Step 5: Configuration (Optional)                          │ │   │
│  │  │  ☐ Use custom configuration                               │ │   │
│  │  │  ┌──────────────────────────────────────────────────────┐ │ │   │
│  │  │  │ Selected: Cost-Optimized Preset                      │ │ │   │
│  │  │  │ Estimated Cost: $0.50                                │ │ │   │
│  │  │  │ Compare to Global: Save $0.70 per project            │ │ │   │
│  │  │  └──────────────────────────────────────────────────────┘ │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ REST API / JSON
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + Python)                          │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    /api/config/* Routes                          │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │ POST   /credentials          - Add API key                 │ │   │
│  │  │ GET    /credentials          - List keys (masked)          │ │   │
│  │  │ POST   /credentials/{id}/test - Test connection            │ │   │
│  │  │ PUT    /global               - Update defaults             │ │   │
│  │  │ GET    /presets              - List presets                │ │   │
│  │  │ POST   /estimate-cost        - Calculate cost              │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                       │
│                                  ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     ProjectManager                               │   │
│  │  resolve_config(project_id) → effective_config                  │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │  1. Load project override (if exists)                      │ │   │
│  │  │  2. Load global config                                     │ │   │
│  │  │  3. Check environment variables                            │ │   │
│  │  │  4. Merge (project → global → env → defaults)             │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                       │
│                                  ▼                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │  SecureKeyStorage│  │  ConfigStorage   │  │  ConfigModels    │     │
│  │                  │  │                  │  │                  │     │
│  │ • encrypt()      │  │ • save_cred()    │  │ • Credentials    │     │
│  │ • decrypt()      │  │ • load_cred()    │  │ • ModelConfig    │     │
│  │ • mask_key()     │  │ • save_config()  │  │ • StageConfig    │     │
│  │                  │  │ • load_config()  │  │ • GlobalConfig   │     │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────────┘     │
│           │                      │                                       │
│           │ Fernet encryption    │ JSON files / SQLite                  │
│           ▼                      ▼                                       │
└─────────────────────────────────────────────────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────┐  ┌────────────────────────────────────────────┐
│  Environment Vars   │  │         Storage (.config/)                  │
│                     │  │                                             │
│ DEVUSSY_ENCRYPTION  │  │  credentials/                               │
│   _KEY              │  │    cred_openai_prod.json (encrypted)        │
│                     │  │    cred_anthropic.json (encrypted)          │
│ OPENAI_API_KEY      │  │                                             │
│ (fallback)          │  │  global_config.json                         │
│                     │  │    { default_model_config: {...},           │
│ DESIGN_API_KEY      │  │      stage_overrides: {...} }               │
│ (fallback)          │  │                                             │
│                     │  │  presets/                                   │
│                     │  │    cost_optimized.json                      │
│                     │  │    max_quality.json                         │
│                     │  │                                             │
│                     │  │  projects/                                  │
│                     │  │    proj_abc123_override.json                │
└─────────────────────┘  └────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW EXAMPLE                                 │
│                                                                           │
│  User Action: Create project with custom config                         │
│                                                                           │
│  1. User clicks "Create Project" in web UI                              │
│  2. Fills form: name="My API", type="api", languages=["Python"]         │
│  3. Step 5: Selects "Cost-Optimized" preset                             │
│  4. Frontend: POST /api/projects with project_config_override           │
│  5. Backend ProjectManager:                                              │
│     a. Save project metadata                                             │
│     b. resolve_config(project_id):                                       │
│        - Load project override (Cost-Optimized preset)                   │
│        - Get credential for design stage: "openai_prod"                  │
│        - Decrypt API key: sk-proj-abc123...                              │
│        - Get credential for devplan stage: "openai_prod"                 │
│        - Decrypt API key: sk-proj-abc123...                              │
│        - Apply temperature/tokens from preset                            │
│     c. Pass config to PipelineOrchestrator                               │
│  6. PipelineOrchestrator:                                                │
│     a. Design stage: Use GPT-4 with decrypted key                        │
│     b. DevPlan stage: Use GPT-3.5-turbo with decrypted key              │
│     c. Handoff stage: Use GPT-3.5-turbo with decrypted key              │
│  7. WebSocket streams progress to frontend                               │
│  8. User sees real-time updates                                          │
│  9. Files generated and saved                                            │
│  10. User downloads/copies results                                       │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                                      │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │ Layer 1: HTTPS (Transport)                                     │     │
│  │ All data encrypted in transit                                  │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │ Layer 2: API Key Masking (Display)                             │     │
│  │ Keys shown as "sk-t...st123" in frontend                       │     │
│  │ Full keys NEVER sent to browser                                │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │ Layer 3: Fernet Encryption (Storage)                           │     │
│  │ Keys encrypted at rest in JSON files                           │     │
│  │ Encryption key from environment variable                       │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │ Layer 4: Audit Logging                                         │     │
│  │ All config changes logged with timestamp                       │     │
│  │ Who, what, when tracked                                        │     │
│  └───────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                   CONFIGURATION RESOLUTION ORDER                         │
│                                                                           │
│  Question: What model should be used for the design stage?              │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │ 1. Check Project Override                                │           │
│  │    File: .config/projects/proj_abc123_override.json      │           │
│  │    Has design_model? → Use it!                           │           │
│  └─────────────────────────────────────────────────────────┘           │
│                              │ No                                        │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │ 2. Check Global Config                                   │           │
│  │    File: .config/global_config.json                      │           │
│  │    Has stage_overrides.design.model_config? → Use it!    │           │
│  └─────────────────────────────────────────────────────────┘           │
│                              │ No                                        │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │ 3. Check Environment Variable                            │           │
│  │    Env: DESIGN_MODEL                                     │           │
│  │    Set? → Use it!                                        │           │
│  └─────────────────────────────────────────────────────────┘           │
│                              │ No                                        │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │ 4. Use Default from Global Config                        │           │
│  │    File: .config/global_config.json                      │           │
│  │    Use: default_model_config.model_name                  │           │
│  └─────────────────────────────────────────────────────────┘           │
│                              │                                           │
│                              ▼                                           │
│                         Result: gpt-4                                    │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESET SYSTEM                                     │
│                                                                           │
│  Built-in Presets:                                                       │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Cost-Optimized                                            │          │
│  │ • Design: GPT-4 ($0.03/1K tokens)                         │          │
│  │ • DevPlan: GPT-3.5-turbo ($0.001/1K tokens)              │          │
│  │ • Handoff: GPT-3.5-turbo ($0.001/1K tokens)              │          │
│  │ Estimated: $0.50/project                                  │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Maximum Quality                                           │          │
│  │ • Design: GPT-4-turbo ($0.01/1K tokens)                   │          │
│  │ • DevPlan: GPT-4-turbo ($0.01/1K tokens)                 │          │
│  │ • Handoff: GPT-4-turbo ($0.01/1K tokens)                 │          │
│  │ Estimated: $1.20/project                                  │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Anthropic Claude                                          │          │
│  │ • Design: Claude 3 Opus ($0.015/1K tokens)                │          │
│  │ • DevPlan: Claude 3 Sonnet ($0.003/1K tokens)            │          │
│  │ • Handoff: Claude 3 Sonnet ($0.003/1K tokens)            │          │
│  │ Estimated: $0.80/project                                  │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                           │
│  When user clicks "Apply Preset":                                        │
│  1. Load preset JSON                                                     │
│  2. Update global_config.json with preset values                         │
│  3. Save to storage                                                      │
│  4. Show success message                                                 │
│  5. Refresh UI to show new config                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Architecture Principles

### 1. Security First
- **Encryption:** All API keys encrypted with Fernet before storage
- **No Exposure:** Keys never sent to frontend (only masked)
- **Environment Fallback:** Supports environment variables for Docker/cloud
- **HTTPS:** Required in production

### 2. Layered Configuration
- **Project Level:** Override everything for specific project
- **Global Level:** Default for all projects
- **Environment Level:** Fallback for deployment scenarios
- **Hardcoded Defaults:** Last resort

### 3. User Experience
- **Presets:** Common configs ready to apply
- **Cost Transparency:** Show estimates before running
- **Testing:** Validate API keys before using
- **Flexibility:** Simple for beginners, powerful for experts

### 4. Backend Design
- **RESTful:** Standard CRUD operations
- **Validation:** Pydantic models ensure data integrity
- **Separation:** Security, storage, and API in separate modules
- **Extensibility:** Easy to add new providers

### 5. Frontend Design
- **Component Based:** Reusable UI components
- **Progressive Disclosure:** Simple by default, advanced when needed
- **Real-time Feedback:** Immediate validation and testing
- **Responsive:** Works on desktop and mobile

## Implementation Notes

### Storage Evolution
- **MVP:** JSON files (simple, human-readable)
- **v1:** SQLite (better querying, transactions)
- **v2:** PostgreSQL (if multi-user, cloud-hosted)

### API Design
- **REST:** Standard CRUD for credentials and config
- **WebSocket:** Real-time streaming for project execution
- **OpenAPI:** Auto-generated documentation with Swagger

### Testing Strategy
- **Unit:** Test each module in isolation
- **Integration:** Test API endpoints end-to-end
- **E2E:** Test full user flows in browser
- **Security:** Verify encryption, masking, HTTPS

### Migration Path
- **Backward Compatible:** Existing config.yaml still works
- **Environment Variables:** Take precedence over stored config
- **Migration Script:** Convert old config to new format
- **Coexistence:** CLI and web UI can both work

---

**See WEB_CONFIG_DESIGN.md for detailed specification**  
**See IMPLEMENTATION_GUIDE.md for step-by-step instructions**
