# Web Configuration System - Implementation Guide

**For:** Next Developer  
**Created:** October 21, 2025  
**Status:** Ready to Start Implementation  
**Estimated Time:** 6-9 days

---

## Quick Start (15 minutes)

### Step 1: Read the Design
```powershell
# Open and review the complete specification
code WEB_CONFIG_DESIGN.md
```

**Key sections to understand:**
- Data Model (Pydantic classes)
- Security layer (encryption)
- REST API endpoints
- Frontend components

### Step 2: Verify Environment
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify dependencies are installed
pip list | Select-String "fastapi|pydantic|cryptography"

# If missing cryptography:
pip install cryptography
```

### Step 3: Review Existing Code
```powershell
# Check current web infrastructure
code src\web\app.py
code src\web\models.py
code src\web\routes\projects.py

# Review existing config system
code src\config.py
code config\config.yaml
```

---

## Implementation Checklist

### Phase 1: Backend Foundation (Days 1-3)

#### Day 1: Security & Storage

**Task 1.1: Create Encryption Module**
- [ ] File: `src/web/security.py`
- [ ] Implement `SecureKeyStorage` class
- [ ] Methods: `encrypt()`, `decrypt()`, `mask_key()`
- [ ] Generate/load encryption key from environment
- [ ] Add unit tests

**Example Code:**
```python
# src/web/security.py
from cryptography.fernet import Fernet
import os

class SecureKeyStorage:
    def __init__(self):
        key = os.getenv("DEVUSSY_ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key()
            print(f"Generated encryption key: {key.decode()}")
            print("Store this in environment: DEVUSSY_ENCRYPTION_KEY")
        else:
            key = key.encode() if isinstance(key, str) else key
        self.cipher = Fernet(key)
    
    def encrypt(self, api_key: str) -> str:
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    def mask_key(self, api_key: str) -> str:
        if len(api_key) < 8:
            return "***"
        return f"{api_key[:4]}...{api_key[-6:]}"
```

**Test it:**
```python
# Test encryption
storage = SecureKeyStorage()
encrypted = storage.encrypt("sk-test123")
decrypted = storage.decrypt(encrypted)
assert decrypted == "sk-test123"
print(f"Masked: {storage.mask_key('sk-test123')}")  # sk-t...st123
```

**Task 1.2: Create Configuration Models**
- [ ] File: `src/web/config_models.py`
- [ ] Copy models from WEB_CONFIG_DESIGN.md
- [ ] Import necessary dependencies
- [ ] Add validation and examples
- [ ] Test with sample data

**Quick Copy:**
See lines 60-180 in WEB_CONFIG_DESIGN.md for complete models.

**Task 1.3: Create Storage Layer**
- [ ] File: `src/web/config_storage.py`
- [ ] Implement JSON file storage (simple MVP)
- [ ] Create `.config/` directory structure
- [ ] Methods: save/load credentials, global config, presets
- [ ] Add file locking for concurrent access

**Storage Structure:**
```
web_projects/
  .config/
    global_config.json
    credentials/
      cred_openai_prod.json
      cred_anthropic.json
    presets/
      cost_optimized.json
      max_quality.json
    projects/
      proj_abc123_override.json
```

#### Day 2: Configuration API

**Task 2.1: Create Config Routes**
- [ ] File: `src/web/routes/config.py`
- [ ] Implement all endpoints from design doc:
  - Credential CRUD (create, list, get, update, delete)
  - Credential testing
  - Global config GET/PUT
  - Preset listing and application
  - Project override GET/PUT
  - Cost estimation
  - Model discovery

**Start Here:**
```python
# src/web/routes/config.py
from fastapi import APIRouter, HTTPException
from typing import List
from ..config_models import ProviderCredentials, GlobalConfig, ConfigPreset
from ..security import SecureKeyStorage
from ..config_storage import ConfigStorage

router = APIRouter(prefix="/api/config", tags=["Configuration"])
security = SecureKeyStorage()
storage = ConfigStorage()

@router.post("/credentials", response_model=ProviderCredentials)
async def create_credential(request: dict):
    """Add a new API key/credential."""
    # Encrypt the API key
    encrypted_key = security.encrypt(request["api_key"])
    
    # Create credential object
    credential = ProviderCredentials(
        id=f"cred_{uuid.uuid4().hex[:12]}",
        name=request["name"],
        provider=request["provider"],
        api_key_encrypted=encrypted_key,
        api_base=request.get("api_base"),
        created_at=datetime.utcnow(),
        is_valid=False  # Not tested yet
    )
    
    # Save to storage
    storage.save_credential(credential)
    
    # Return credential (API key masked)
    return credential

@router.get("/credentials", response_model=List[ProviderCredentials])
async def list_credentials():
    """List all credentials (API keys masked)."""
    credentials = storage.load_all_credentials()
    return credentials
```

**Task 2.2: Implement Credential Testing**
- [ ] Add endpoint to test API key validity
- [ ] Make test request to provider
- [ ] Update `is_valid` and `last_tested` fields
- [ ] Return helpful error messages

**Task 2.3: Create Preset System**
- [ ] Define built-in presets (cost-optimized, max-quality, etc.)
- [ ] Load presets from JSON files
- [ ] Implement preset application (update global config)
- [ ] Allow custom presets

#### Day 3: Integration with Existing System

**Task 3.1: Update ProjectManager**
- [ ] File: `src/web/project_manager.py`
- [ ] Add method to resolve configuration for a project
- [ ] Load credentials and decrypt API keys
- [ ] Apply per-project overrides if present
- [ ] Pass config to PipelineOrchestrator

**Task 3.2: Update ProjectCreateRequest**
- [ ] File: `src/web/models.py`
- [ ] Add optional config override fields
- [ ] Add validation for custom configurations
- [ ] Update examples

**Task 3.3: Test End-to-End**
- [ ] Create credential via API
- [ ] Set global config
- [ ] Create project with custom config
- [ ] Verify pipeline uses correct credentials

---

### Phase 2: Frontend UI (Days 4-6)

#### Day 4: Settings Page Foundation

**Task 4.1: Create API Client**
- [ ] File: `frontend/src/services/configApi.ts`
- [ ] Implement all API calls (credentials, config, presets)
- [ ] Add error handling
- [ ] Add TypeScript types

**Example:**
```typescript
// frontend/src/services/configApi.ts
import axios from 'axios';

const API_BASE = '/api/config';

export interface Credential {
  id: string;
  name: string;
  provider: string;
  api_key_encrypted: string;  // Always masked in responses
  created_at: string;
  is_valid: boolean;
}

export const configApi = {
  // Credentials
  async createCredential(data: {
    name: string;
    provider: string;
    api_key: string;
    api_base?: string;
  }): Promise<Credential> {
    const response = await axios.post(`${API_BASE}/credentials`, data);
    return response.data;
  },
  
  async listCredentials(): Promise<Credential[]> {
    const response = await axios.get(`${API_BASE}/credentials`);
    return response.data;
  },
  
  async testCredential(id: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(`${API_BASE}/credentials/${id}/test`);
    return response.data;
  },
  
  // ... more methods
};
```

**Task 4.2: Create Settings Page**
- [ ] File: `frontend/src/pages/SettingsPage.tsx`
- [ ] Set up tab navigation (Credentials, Global, Presets, Advanced)
- [ ] Create layout with sidebar
- [ ] Add routing

**Task 4.3: Build Credentials Tab**
- [ ] File: `frontend/src/components/config/CredentialsTab.tsx`
- [ ] Create credential list component
- [ ] Create credential form (add/edit)
- [ ] Add test connection button
- [ ] Add delete confirmation

#### Day 5: Configuration Forms

**Task 5.1: Build Global Config Tab**
- [ ] File: `frontend/src/components/config/GlobalConfigTab.tsx`
- [ ] Create model selector component
- [ ] Add temperature/max_tokens sliders
- [ ] Build per-stage override accordion
- [ ] Show cost estimate

**Task 5.2: Build Preset Tab**
- [ ] File: `frontend/src/components/config/PresetsTab.tsx`
- [ ] Display preset cards
- [ ] Add apply button
- [ ] Show preview of preset config
- [ ] Add custom preset creation

**Task 5.3: Shared Components**
- [ ] `ModelSelector.tsx` - Dropdown with models
- [ ] `ProviderSelector.tsx` - Select provider
- [ ] `CostEstimator.tsx` - Show cost preview
- [ ] `ConfigPreview.tsx` - Display config JSON

#### Day 6: Project Configuration Integration

**Task 6.1: Update Project Creation Form**
- [ ] File: `frontend/src/pages/CreateProjectPage.tsx`
- [ ] Add "Custom Configuration" step
- [ ] Add toggle for per-project config
- [ ] Show cost comparison
- [ ] Add validation warnings

**Task 6.2: UI Polish**
- [ ] Add loading states
- [ ] Add success/error toasts
- [ ] Add help tooltips
- [ ] Make responsive
- [ ] Add dark mode support

---

### Phase 3: Testing & Documentation (Days 7-9)

#### Day 7: Backend Testing

**Task 7.1: Security Tests**
- [ ] File: `tests/unit/test_web_security.py`
- [ ] Test encryption/decryption
- [ ] Test key masking
- [ ] Test edge cases

**Task 7.2: Storage Tests**
- [ ] File: `tests/unit/test_config_storage.py`
- [ ] Test CRUD operations
- [ ] Test file locking
- [ ] Test error handling

**Task 7.3: API Tests**
- [ ] File: `tests/integration/test_config_api.py`
- [ ] Test all endpoints
- [ ] Test validation
- [ ] Test authentication

#### Day 8: Frontend Testing

**Task 8.1: Component Tests**
- [ ] Test credential form
- [ ] Test model selector
- [ ] Test preset cards
- [ ] Test validation

**Task 8.2: Integration Tests**
- [ ] Test full config flow
- [ ] Test project creation with config
- [ ] Test error scenarios

#### Day 9: Documentation

**Task 9.1: Update Guides**
- [ ] Update `WEB_INTERFACE_GUIDE.md` with config section
- [ ] Create `WEB_CONFIG_GUIDE.md` for end users
- [ ] Add screenshots and examples
- [ ] Document security best practices

**Task 9.2: Update README**
- [ ] Add configuration section
- [ ] Add screenshots of settings page
- [ ] Update quick start guide

**Task 9.3: API Documentation**
- [ ] Ensure OpenAPI docs are complete
- [ ] Add examples for all endpoints
- [ ] Test with Swagger UI

---

## Testing Strategy

### Unit Tests
```powershell
# Test security module
python -m pytest tests/unit/test_web_security.py -v

# Test storage
python -m pytest tests/unit/test_config_storage.py -v

# Test models
python -m pytest tests/unit/test_config_models.py -v
```

### Integration Tests
```powershell
# Test full API
python -m pytest tests/integration/test_config_api.py -v

# Test with real encryption
DEVUSSY_ENCRYPTION_KEY=test python -m pytest tests/integration/ -v
```

### Manual Testing
```powershell
# 1. Start backend
python -m src.web.app

# 2. Open Swagger UI
start http://localhost:8000/docs

# 3. Test credentials endpoint
# POST /api/config/credentials
{
  "name": "OpenAI Test",
  "provider": "openai",
  "api_key": "sk-test123",
  "api_base": null
}

# 4. List credentials
# GET /api/config/credentials

# 5. Start frontend
cd frontend
npm run dev
start http://localhost:3000/settings
```

---

## Common Issues & Solutions

### Issue 1: Encryption Key Not Persistent
**Problem:** Each restart generates new key, can't decrypt old credentials

**Solution:**
```powershell
# Generate key once
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in environment (permanent)
[System.Environment]::SetEnvironmentVariable('DEVUSSY_ENCRYPTION_KEY', 'YOUR_KEY_HERE', 'User')

# Or create .env file
echo "DEVUSSY_ENCRYPTION_KEY=YOUR_KEY_HERE" > .env
```

### Issue 2: API Key Validation Fails
**Problem:** Test endpoint always returns "invalid"

**Solution:**
- Check API key format (starts with 'sk-' for OpenAI)
- Verify network connectivity
- Check provider endpoint is correct
- Look at error logs for details

### Issue 3: CORS Errors in Frontend
**Problem:** Can't call API from frontend

**Solution:**
```python
# src/web/app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Verification Checklist

Before marking Phase 11.3 complete, verify:

### Backend
- [ ] Encryption works (encrypt → decrypt → same value)
- [ ] Credentials can be created, listed, updated, deleted
- [ ] API keys are masked in responses
- [ ] Global config can be saved and loaded
- [ ] Presets are available and can be applied
- [ ] Project overrides work
- [ ] All API endpoints return correct status codes
- [ ] Error messages are user-friendly

### Frontend
- [ ] Settings page loads
- [ ] Can add API key through form
- [ ] Credentials list displays correctly
- [ ] Test connection button works
- [ ] Can select models from dropdown
- [ ] Global config can be updated
- [ ] Presets can be applied
- [ ] Cost estimator shows values
- [ ] Project creation shows config options
- [ ] Validation works
- [ ] Responsive on mobile

### Integration
- [ ] Project created with custom config uses correct API key
- [ ] Per-stage configs work
- [ ] Config resolution order correct (project → global → default)
- [ ] Existing CLI config.yaml still works
- [ ] Environment variables take precedence

### Security
- [ ] API keys never logged in plaintext
- [ ] Encrypted credentials at rest
- [ ] Keys not sent to frontend
- [ ] HTTPS recommended in docs
- [ ] Encryption key securely stored

### Documentation
- [ ] WEB_CONFIG_GUIDE.md created
- [ ] WEB_INTERFACE_GUIDE.md updated
- [ ] README updated
- [ ] API docs complete (Swagger)
- [ ] Security best practices documented

---

## Next Steps After Completion

Once Phase 11.3 is complete:

1. **Update HANDOFF.md** with completion status
2. **Move to Phase 11.4** - Integration & Polish
3. **Consider publishing** v0.3.0-alpha with web UI
4. **Gather feedback** from beta testers
5. **Iterate** based on user experience

---

## Resources

### Documentation
- `WEB_CONFIG_DESIGN.md` - Complete technical spec
- `WEB_INTERFACE_GUIDE.md` - Web UI guide
- `MULTI_LLM_GUIDE.md` - Multi-LLM configuration (CLI)

### Code References
- `src/config.py` - Existing config system
- `src/clients/factory.py` - LLM client creation
- `src/web/models.py` - Existing web models
- `src/web/routes/projects.py` - Example routes

### External Resources
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Cryptography Fernet](https://cryptography.io/en/latest/fernet/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

**Ready to start? Begin with Day 1, Task 1.1: Create `src/web/security.py`**

Good luck! 🚀
