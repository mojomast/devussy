# Web Configuration System Design

**Created:** October 21, 2025  
**Status:** Planning Phase  
**Goal:** Enable granular API key, endpoint, and model configuration through web UI

---

## Overview

The web interface needs comprehensive configuration management that allows users to:

1. **Configure API keys and endpoints** for multiple LLM providers
2. **Set global defaults** for all projects
3. **Override per-stage** with different models/providers (design, devplan, handoff)
4. **Create per-project configs** that override global settings
5. **Manage multiple provider accounts** (e.g., different OpenAI keys for different teams)
6. **Test configurations** before using them
7. **Estimate costs** based on selected models
8. **Store secrets securely** with encryption

---

## Current State Analysis

### ✅ What We Have (CLI-based)

**Config File (`config/config.yaml`):**
- Global provider/model settings
- Per-stage overrides (design_model, devplan_model, handoff_model)
- Retry, timeout, concurrency settings
- Git, logging, output configuration

**Environment Variables:**
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- Per-stage keys: `DESIGN_API_KEY`, `DEVPLAN_API_KEY`, `HANDOFF_API_KEY`

**Code Support:**
- `src/config.py` - Loads config from YAML + env vars
- `src/clients/factory.py` - Creates LLM clients based on config
- Multi-LLM support already implemented

### ❌ What We're Missing (Web UI)

1. **No API for configuration management** - Can't GET/PUT config via REST
2. **No secure storage for API keys** - Just env vars (not user-friendly)
3. **No UI for configuration** - Users need to edit YAML files manually
4. **No per-project overrides** - Global config applies to all projects
5. **No configuration validation** - Can't test API keys before using
6. **No provider presets** - Users need to know model names
7. **No cost estimation** - No visibility into expected costs
8. **No multi-account support** - Only one key per provider

---

## Design Goals

### User Experience Goals

**For Non-Technical Users:**
- 🎯 Add API keys through a simple form (no terminal editing)
- 🎯 Select models from dropdowns (no need to know exact names)
- 🎯 Use presets like "Cost-Optimized" or "Max Quality"
- 🎯 See cost estimates before running projects
- 🎯 Test API keys with one click

**For Power Users:**
- 🎯 Configure different models per pipeline stage
- 🎯 Set up multiple provider accounts
- 🎯 Override settings per project
- 🎯 Fine-tune temperature, max_tokens, etc.
- 🎯 Import/export configurations

### Security Goals

- 🔒 API keys encrypted at rest
- 🔒 Keys never sent to frontend (only masked display)
- 🔒 Audit log for configuration changes
- 🔒 Option to use environment variables (for Docker/cloud deployments)

### Flexibility Goals

- ⚙️ Granular control at every level (global → stage → project)
- ⚙️ Support for future providers (easy to add)
- ⚙️ Backward compatible with existing config.yaml
- ⚙️ Works offline (local config) and online (cloud database)

---

## Architecture Design

### 1. Data Model (Pydantic)

```python
# src/web/config_models.py

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    GENERIC = "generic"
    REQUESTY = "requesty"

class ProviderCredentials(BaseModel):
    """Secure storage for provider API keys and endpoints."""
    id: str  # Unique credential ID
    name: str  # User-friendly name (e.g., "OpenAI - Production")
    provider: ProviderType
    api_key_encrypted: str  # Encrypted API key
    api_base: Optional[str] = None  # Custom endpoint
    organization_id: Optional[str] = None  # For OpenAI orgs
    created_at: datetime
    last_tested: Optional[datetime] = None
    is_valid: bool = False

class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    provider_credential_id: str  # References ProviderCredentials
    model_name: str  # e.g., "gpt-4", "claude-3-opus"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

class StageConfig(BaseModel):
    """Configuration for a pipeline stage."""
    stage: PipelineStage  # DESIGN, DEVPLAN, HANDOFF
    model_config: ModelConfig
    enabled: bool = True
    timeout: int = 60
    max_retries: int = 3

class GlobalConfig(BaseModel):
    """Global configuration (applies to all projects)."""
    id: str = "global"
    default_model_config: ModelConfig
    stage_overrides: Dict[PipelineStage, StageConfig] = {}
    
    # Retry settings
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 60.0
    retry_exponential_base: float = 2.0
    
    # Concurrency
    max_concurrent_requests: int = 5
    
    # Output settings
    output_dir: str = "./web_projects"
    enable_git: bool = True
    enable_streaming: bool = True

class ProjectConfigOverride(BaseModel):
    """Per-project configuration overrides."""
    project_id: str
    override_global: bool = False
    model_config: Optional[ModelConfig] = None
    stage_overrides: Dict[PipelineStage, StageConfig] = {}

class ConfigPreset(BaseModel):
    """Preset configuration for common use cases."""
    id: str
    name: str
    description: str
    default_model_config: ModelConfig
    stage_overrides: Dict[PipelineStage, StageConfig]
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": "cost_optimized",
                    "name": "Cost-Optimized (GPT-4 + GPT-3.5)",
                    "description": "Use GPT-4 for design, GPT-3.5 for devplan/handoff",
                    "default_model_config": {"model_name": "gpt-4", ...},
                    "stage_overrides": {
                        "DEVPLAN": {"model_name": "gpt-3.5-turbo", ...},
                        "HANDOFF": {"model_name": "gpt-3.5-turbo", ...}
                    }
                },
                {
                    "id": "max_quality",
                    "name": "Maximum Quality (GPT-4 Turbo)",
                    "description": "Use latest GPT-4 Turbo for all stages",
                },
                {
                    "id": "anthropic_claude",
                    "name": "Anthropic Claude 3",
                    "description": "Use Claude 3 Opus for all stages",
                }
            ]
        }
```

### 2. Secure Storage Layer

```python
# src/web/security.py

from cryptography.fernet import Fernet
import os

class SecureKeyStorage:
    """Encrypt/decrypt API keys using Fernet symmetric encryption."""
    
    def __init__(self):
        # Load encryption key from environment or generate
        self.key = os.getenv("DEVUSSY_ENCRYPTION_KEY")
        if not self.key:
            self.key = Fernet.generate_key()
            # In production, store this securely!
        self.cipher = Fernet(self.key)
    
    def encrypt(self, api_key: str) -> str:
        """Encrypt an API key."""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """Decrypt an API key."""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    def mask_key(self, api_key: str) -> str:
        """Return masked version for display (sk-...abc123)."""
        if len(api_key) < 8:
            return "***"
        return f"{api_key[:4]}...{api_key[-6:]}"
```

### 3. Configuration Storage

**Option A: JSON Files (Simple, for MVP)**
```
web_projects/
  .config/
    global_config.json
    credentials/
      cred_abc123.json
      cred_def456.json
    presets/
      cost_optimized.json
      max_quality.json
    projects/
      proj_abc123_override.json
```

**Option B: SQLite Database (Better for v1)**
```sql
CREATE TABLE credentials (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_base TEXT,
    organization_id TEXT,
    created_at TIMESTAMP,
    last_tested TIMESTAMP,
    is_valid BOOLEAN
);

CREATE TABLE global_config (
    id TEXT PRIMARY KEY DEFAULT 'global',
    config_json TEXT NOT NULL,
    updated_at TIMESTAMP
);

CREATE TABLE project_config_overrides (
    project_id TEXT PRIMARY KEY,
    config_json TEXT NOT NULL,
    updated_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### 4. REST API Endpoints

```python
# src/web/routes/config.py

router = APIRouter(prefix="/api/config")

# Credentials Management
@router.post("/credentials", response_model=ProviderCredentials)
async def create_credential(request: CreateCredentialRequest):
    """Add a new API key/credential."""
    pass

@router.get("/credentials", response_model=List[ProviderCredentials])
async def list_credentials():
    """List all credentials (API keys masked)."""
    pass

@router.get("/credentials/{id}", response_model=ProviderCredentials)
async def get_credential(id: str):
    """Get credential details (API key masked)."""
    pass

@router.put("/credentials/{id}", response_model=ProviderCredentials)
async def update_credential(id: str, request: UpdateCredentialRequest):
    """Update credential (e.g., rotate API key)."""
    pass

@router.delete("/credentials/{id}")
async def delete_credential(id: str):
    """Delete a credential."""
    pass

@router.post("/credentials/{id}/test")
async def test_credential(id: str):
    """Test if API key is valid by making a test request."""
    pass

# Global Configuration
@router.get("/global", response_model=GlobalConfig)
async def get_global_config():
    """Get current global configuration."""
    pass

@router.put("/global", response_model=GlobalConfig)
async def update_global_config(request: GlobalConfig):
    """Update global configuration."""
    pass

# Presets
@router.get("/presets", response_model=List[ConfigPreset])
async def list_presets():
    """List available configuration presets."""
    pass

@router.post("/presets/apply/{preset_id}")
async def apply_preset(preset_id: str):
    """Apply a preset to global configuration."""
    pass

# Project Overrides
@router.get("/projects/{project_id}", response_model=ProjectConfigOverride)
async def get_project_config(project_id: str):
    """Get project-specific configuration overrides."""
    pass

@router.put("/projects/{project_id}", response_model=ProjectConfigOverride)
async def set_project_config(project_id: str, request: ProjectConfigOverride):
    """Set project-specific configuration overrides."""
    pass

# Cost Estimation
@router.post("/estimate-cost", response_model=CostEstimate)
async def estimate_cost(request: CostEstimateRequest):
    """Estimate cost for a project based on configuration."""
    pass

# Model Discovery
@router.get("/models/{provider}", response_model=List[ModelInfo])
async def list_available_models(provider: ProviderType):
    """List available models for a provider."""
    pass
```

### 5. Frontend Components

**Component Structure:**
```
frontend/src/
  pages/
    SettingsPage.tsx                 # Main settings page
    ┣━ CredentialsTab.tsx            # Manage API keys
    ┣━ GlobalConfigTab.tsx           # Global defaults
    ┣━ PresetsTab.tsx                # Quick presets
    ┗━ AdvancedTab.tsx               # Fine-tuning
  
  components/
    config/
      CredentialForm.tsx             # Add/edit API key
      CredentialList.tsx             # List all credentials
      CredentialTestButton.tsx       # Test API key
      ModelSelector.tsx              # Select model from dropdown
      StageConfigEditor.tsx          # Configure per-stage settings
      PresetCard.tsx                 # Preset visualization
      CostEstimator.tsx              # Show cost preview
      ConfigImportExport.tsx         # Import/export config JSON
```

**Example UI Flow:**

```tsx
// CredentialForm.tsx - Add API Key
<form>
  <Input label="Name" placeholder="OpenAI - Production" />
  <Select label="Provider" options={["OpenAI", "Anthropic", "Google"]} />
  <Input 
    type="password" 
    label="API Key" 
    placeholder="sk-..."
    help="Your key is encrypted and never exposed"
  />
  <Input label="Custom Endpoint (Optional)" placeholder="https://..." />
  <Button onClick={testConnection}>Test Connection</Button>
  <Button type="submit">Save</Button>
</form>

// GlobalConfigTab.tsx - Global Settings
<div>
  <h2>Default Model Configuration</h2>
  <CredentialSelector label="Provider Account" />
  <ModelSelector provider={selectedProvider} />
  <Slider label="Temperature" min={0} max={2} step={0.1} />
  <NumberInput label="Max Tokens" />
  
  <h2>Per-Stage Overrides</h2>
  <Accordion>
    <AccordionItem title="Design Stage">
      <StageConfigEditor stage="design" />
    </AccordionItem>
    <AccordionItem title="DevPlan Stage">
      <StageConfigEditor stage="devplan" />
    </AccordionItem>
    <AccordionItem title="Handoff Stage">
      <StageConfigEditor stage="handoff" />
    </AccordionItem>
  </Accordion>
  
  <h2>Cost Estimate</h2>
  <CostEstimator config={currentConfig} />
</div>

// PresetsTab.tsx - Quick Presets
<div className="grid grid-cols-2 gap-4">
  <PresetCard 
    name="Cost-Optimized"
    description="GPT-4 for design, GPT-3.5 for devplan/handoff"
    estimatedCost="$0.50 per project"
    onApply={() => applyPreset("cost_optimized")}
  />
  <PresetCard 
    name="Maximum Quality"
    description="GPT-4 Turbo for all stages"
    estimatedCost="$1.20 per project"
    onApply={() => applyPreset("max_quality")}
  />
  <PresetCard 
    name="Anthropic Claude"
    description="Claude 3 Opus for all stages"
    estimatedCost="$0.80 per project"
    onApply={() => applyPreset("anthropic_claude")}
  />
</div>
```

### 6. Project Creation Flow with Config

**Enhanced ProjectCreateRequest:**
```tsx
// Frontend: Create Project Page
<form>
  {/* Step 1: Project Basics */}
  <Input label="Project Name" />
  <Select label="Project Type" />
  {/* ... */}
  
  {/* NEW: Step 5: Configuration Override (Optional) */}
  <h3>Model Configuration (Optional)</h3>
  <Checkbox 
    label="Use custom configuration for this project"
    onChange={(e) => setUseCustomConfig(e.target.checked)}
  />
  
  {useCustomConfig && (
    <div>
      <Alert>
        This will override your global configuration for this project only.
      </Alert>
      
      <CredentialSelector label="Provider Account" />
      <ModelSelector label="Model" />
      
      <Accordion>
        <AccordionItem title="Advanced: Per-Stage Models">
          <StageConfigEditor stage="design" />
          <StageConfigEditor stage="devplan" />
          <StageConfigEditor stage="handoff" />
        </AccordionItem>
      </Accordion>
      
      <CostEstimator 
        config={customConfig} 
        showComparison={true}
        comparisonConfig={globalConfig}
      />
    </div>
  )}
  
  <Button type="submit">Create Project</Button>
</form>
```

---

## Implementation Plan

### Phase 1: Backend Foundation (Days 1-2)

**Priority 1: Security & Storage**
- [ ] Create `src/web/security.py` with encryption
- [ ] Create `src/web/config_models.py` with all Pydantic models
- [ ] Create `src/web/config_storage.py` for JSON file storage
- [ ] Add `.config/` to `.gitignore`

**Priority 2: Configuration API**
- [ ] Create `src/web/routes/config.py` with all endpoints
- [ ] Implement credential CRUD operations
- [ ] Implement global config GET/PUT
- [ ] Add credential validation/testing

**Priority 3: Integration**
- [ ] Modify `project_manager.py` to use stored credentials
- [ ] Add config resolution logic (project → global → default)
- [ ] Update `ProjectCreateRequest` to accept config overrides

### Phase 2: Preset System (Day 3)

**Priority 1: Built-in Presets**
- [ ] Create preset definitions (cost-optimized, max-quality, etc.)
- [ ] Implement preset application logic
- [ ] Add preset validation

**Priority 2: Cost Estimation**
- [ ] Create cost calculation module
- [ ] Add token estimation based on project size
- [ ] Implement cost comparison

### Phase 3: Frontend UI (Days 4-5)

**Priority 1: Settings Page**
- [ ] Create `SettingsPage.tsx` with tab navigation
- [ ] Implement `CredentialsTab.tsx`
  - [ ] Credential form (add/edit)
  - [ ] Credential list with masked keys
  - [ ] Test connection button
- [ ] Implement `GlobalConfigTab.tsx`
  - [ ] Model selector with dropdowns
  - [ ] Per-stage override UI
  - [ ] Cost estimator widget

**Priority 2: Preset UI**
- [ ] Create `PresetsTab.tsx`
- [ ] Implement preset cards
- [ ] Add apply/preview functionality

**Priority 3: Project Creation**
- [ ] Add configuration step to project creation wizard
- [ ] Implement custom config toggle
- [ ] Show cost comparison

### Phase 4: Testing & Polish (Day 6)

**Priority 1: Backend Tests**
- [ ] Test encryption/decryption
- [ ] Test credential CRUD
- [ ] Test config resolution logic
- [ ] Test API endpoint validation

**Priority 2: Frontend Tests**
- [ ] Component unit tests
- [ ] Integration tests for settings page
- [ ] E2E test for full config flow

**Priority 3: Documentation**
- [ ] Update WEB_INTERFACE_GUIDE.md
- [ ] Add security best practices
- [ ] Document preset system
- [ ] Add troubleshooting guide

---

## Security Considerations

### API Key Storage

**Development (MVP):**
- Encrypt keys with Fernet
- Store encryption key in environment variable
- Use JSON files for credential storage

**Production (v1):**
- Use dedicated secret management service (AWS Secrets Manager, HashiCorp Vault)
- Rotate encryption keys periodically
- Add access logging

### Best Practices

1. **Never log API keys** - Mask in all logs
2. **Never send to frontend** - Only send masked versions
3. **Validate on backend** - Test keys server-side only
4. **Use HTTPS** - Require TLS for web interface
5. **Audit trail** - Log all config changes with timestamps
6. **Rate limit** - Prevent brute-force testing of keys
7. **Session management** - Timeout inactive sessions

---

## User Experience Enhancements

### Smart Defaults

1. **Auto-detect provider from key format**
   - `sk-...` → OpenAI
   - `sk-ant-...` → Anthropic
   - Auto-populate provider field

2. **Model recommendations based on task**
   - Complex design → GPT-4
   - Structured output → GPT-3.5 Turbo
   - Show recommended models with badges

3. **Validation warnings**
   - "GPT-4 is expensive - consider GPT-3.5 for devplan"
   - "This model may be slow for long projects"
   - "API key not tested - test before using"

### Cost Transparency

1. **Real-time cost preview**
   - Estimate tokens based on project description
   - Show cost breakdown per stage
   - Compare different configurations

2. **Historical tracking**
   - Track actual costs per project
   - Monthly spending reports
   - Budget alerts

### Error Handling

1. **Friendly error messages**
   - ❌ "Invalid API key" → ✅ "API key test failed. Please check your key or try testing the connection again."
   - ❌ "Rate limit" → ✅ "You've hit the API rate limit. Your project will resume automatically in 30 seconds."

2. **Automatic fallbacks**
   - If primary credential fails, try backup
   - If expensive model unavailable, suggest alternative
   - Graceful degradation

---

## Migration & Backward Compatibility

### Support Existing Config Files

```python
# src/web/config_migration.py

def migrate_yaml_to_web_config():
    """Migrate existing config.yaml to web storage format."""
    
    # Read config.yaml
    old_config = load_yaml_config()
    
    # Create global config
    global_config = GlobalConfig(
        default_model_config=ModelConfig(
            provider_credential_id="default",
            model_name=old_config.model,
            temperature=old_config.temperature,
            max_tokens=old_config.max_tokens
        ),
        # ... map other settings
    )
    
    # Save to new format
    save_global_config(global_config)
    
    # Migrate API keys from env vars
    for key_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        if key := os.getenv(key_name):
            credential = ProviderCredentials(
                id=f"migrated_{key_name}",
                name=f"Migrated {key_name}",
                provider=detect_provider(key),
                api_key_encrypted=encrypt(key),
                # ...
            )
            save_credential(credential)
```

### Environment Variable Fallback

```python
# Always check environment variables first
def get_api_key(provider: str, stage: Optional[str] = None):
    """Get API key with fallback chain."""
    
    # 1. Try stage-specific env var (DESIGN_API_KEY)
    if stage:
        if key := os.getenv(f"{stage.upper()}_API_KEY"):
            return key
    
    # 2. Try provider env var (OPENAI_API_KEY)
    if key := os.getenv(f"{provider.upper()}_API_KEY"):
        return key
    
    # 3. Try stored credential
    if credential := load_credential_for_provider(provider):
        return decrypt(credential.api_key_encrypted)
    
    # 4. Fail with helpful message
    raise ValueError(f"No API key found for {provider}")
```

---

## Success Metrics

### Must-Have for MVP
- ✅ Users can add API keys through web UI
- ✅ Users can select models from dropdowns
- ✅ Configuration persists across sessions
- ✅ API keys are encrypted
- ✅ At least 2 presets available
- ✅ Configuration works for project creation

### Nice-to-Have for v1
- ✅ Cost estimation shows before project creation
- ✅ API key testing works
- ✅ Per-project overrides functional
- ✅ Import/export configuration
- ✅ Multiple credentials per provider

### Future Enhancements
- Team sharing of configurations
- Configuration versioning
- A/B testing different configs
- Auto-optimization based on results
- Integration with billing systems

---

## Next Steps

1. ✅ **Review this design** with stakeholders
2. **Start implementation** with Phase 1 (Backend Foundation)
3. **Iterate** based on user feedback
4. **Document** as we build
5. **Test thoroughly** with real API keys
6. **Update HANDOFF.md** when complete

---

**Document Status:** Draft for Review  
**Estimated Effort:** 6 days full-time development  
**Priority:** High - Critical for web UI usability
