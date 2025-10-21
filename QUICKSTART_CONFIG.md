# 🚀 Quick Start - Configuration System Implementation

**👋 Welcome, Next Developer!**

You're about to implement the web-based configuration management system. This document gives you everything you need to start in **5 minutes**.

---

## ⚡ TL;DR

**What:** Build web UI for managing API keys, models, and configuration  
**Why:** Non-technical users can't edit YAML files - they need a web form  
**Time:** 6-9 days full-time  
**Start:** Day 1, Task 1 - Create `src/web/security.py`

---

## 📚 Read These First (In Order)

### 1. WEB_CONFIG_DESIGN.md (30 min)
Complete technical specification with:
- Data models (Pydantic classes)
- API endpoints (15+ routes)
- Frontend components (React)
- Security (encryption)
- User flows

**Why read:** Understand WHAT you're building

### 2. IMPLEMENTATION_GUIDE.md (15 min)
Step-by-step implementation plan with:
- Daily task checklist
- Code examples
- Testing strategy
- Troubleshooting guide

**Why read:** Know HOW to build it

### 3. SESSION_SUMMARY_CONFIG_PLANNING.md (10 min - optional)
Context and decisions behind the design.

**Why read:** Understand WHY decisions were made

---

## 🛠️ Setup (5 minutes)

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install cryptography for encryption
pip install cryptography

# 3. Generate encryption key for testing
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 4. Set environment variable (copy key from above)
$env:DEVUSSY_ENCRYPTION_KEY = "your-key-here"

# 5. Verify setup
python -c "from cryptography.fernet import Fernet; import os; print('✓ Setup OK' if os.getenv('DEVUSSY_ENCRYPTION_KEY') else '✗ Missing key')"
```

---

## 📝 Day 1: First Task (2 hours)

### Create `src/web/security.py`

```python
"""Secure storage for API keys with encryption."""

from cryptography.fernet import Fernet
import os


class SecureKeyStorage:
    """Encrypt/decrypt API keys using Fernet symmetric encryption."""
    
    def __init__(self):
        # Load encryption key from environment
        key = os.getenv("DEVUSSY_ENCRYPTION_KEY")
        if not key:
            # Generate new key if not found
            key = Fernet.generate_key()
            print(f"⚠️  Generated encryption key: {key.decode()}")
            print("Set this in environment: DEVUSSY_ENCRYPTION_KEY")
        else:
            key = key.encode() if isinstance(key, str) else key
        
        self.cipher = Fernet(key)
    
    def encrypt(self, api_key: str) -> str:
        """Encrypt an API key.
        
        Args:
            api_key: Plain text API key (e.g., "sk-...")
            
        Returns:
            Encrypted key as base64 string
        """
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """Decrypt an API key.
        
        Args:
            encrypted_key: Encrypted key from encrypt()
            
        Returns:
            Original plain text API key
        """
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    def mask_key(self, api_key: str) -> str:
        """Return masked version for display.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Masked key (e.g., "sk-t...st123")
        """
        if len(api_key) < 8:
            return "***"
        return f"{api_key[:4]}...{api_key[-6:]}"


# Test the implementation
if __name__ == "__main__":
    storage = SecureKeyStorage()
    
    # Test encryption/decryption
    original = "sk-test-api-key-123456"
    encrypted = storage.encrypt(original)
    decrypted = storage.decrypt(encrypted)
    
    print(f"Original:  {original}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Masked:    {storage.mask_key(original)}")
    print(f"✓ Test {'PASSED' if decrypted == original else 'FAILED'}")
```

**Test it:**
```powershell
python src\web\security.py
# Should print:
# Original:  sk-test-api-key-123456
# Encrypted: gAAAAABl...
# Decrypted: sk-test-api-key-123456
# Masked:    sk-t...key-123456
# ✓ Test PASSED
```

**If it works:** ✅ Move to next task  
**If it fails:** Check environment variable is set

---

## 📋 Daily Checklist

### Week 1: Backend

**Day 1** ☐
- ☐ Create `src/web/security.py` (encryption)
- ☐ Create `src/web/config_models.py` (Pydantic models)
- ☐ Write tests for encryption
- ☐ Commit and push

**Day 2** ☐
- ☐ Create `src/web/config_storage.py` (JSON storage)
- ☐ Create `.config/` directory structure
- ☐ Create default presets
- ☐ Write storage tests
- ☐ Commit and push

**Day 3** ☐
- ☐ Create `src/web/routes/config.py` (REST API)
- ☐ Add credential CRUD endpoints
- ☐ Add testing endpoint
- ☐ Test with Swagger UI
- ☐ Commit and push

### Week 2: Frontend

**Day 4** ☐
- ☐ Create `frontend/src/services/configApi.ts` (API client)
- ☐ Create `frontend/src/pages/SettingsPage.tsx`
- ☐ Add tab navigation
- ☐ Commit and push

**Day 5** ☐
- ☐ Create `CredentialsTab.tsx` (credential management)
- ☐ Create `GlobalConfigTab.tsx` (default settings)
- ☐ Add form validation
- ☐ Commit and push

**Day 6** ☐
- ☐ Create `PresetsTab.tsx` (quick presets)
- ☐ Update project creation form
- ☐ Add cost estimator
- ☐ Commit and push

### Week 3: Testing & Docs

**Day 7-8** ☐
- ☐ Write backend tests
- ☐ Write frontend tests
- ☐ Run full test suite
- ☐ Fix any issues
- ☐ Commit and push

**Day 9** ☐
- ☐ Create `WEB_CONFIG_GUIDE.md` (user guide)
- ☐ Update `WEB_INTERFACE_GUIDE.md`
- ☐ Update `README.md`
- ☐ Update `HANDOFF.md`
- ☐ Create screenshots
- ☐ Final commit and push

---

## 🆘 Quick Help

### Common Issues

**Issue:** "No module named 'cryptography'"
```powershell
pip install cryptography
```

**Issue:** "Encryption key not found"
```powershell
$env:DEVUSSY_ENCRYPTION_KEY = "your-key-here"
```

**Issue:** "Can't decrypt old credentials"
**Cause:** Encryption key changed
**Fix:** Use same key consistently (store in .env file)

**Issue:** "CORS errors in frontend"
**Fix:** Check `src/web/app.py` has CORS middleware configured

---

## 📊 Progress Tracking

Update this as you complete tasks:

```
Backend:
├─ [✓] Security module
├─ [✓] Config models
├─ [✓] Storage layer
└─ [✓] REST API

Frontend:
├─ [ ] API client
├─ [ ] Settings page
├─ [ ] Credentials tab
├─ [ ] Global config tab
├─ [ ] Presets tab
└─ [ ] Project integration

Testing:
├─ [ ] Backend tests
├─ [ ] Frontend tests
└─ [ ] E2E tests

Documentation:
├─ [ ] User guide
├─ [ ] Developer guide
└─ [ ] Screenshots
```

---

## 🎯 Success Criteria

You're done when:

- ✅ Users can add API key through web form
- ✅ Keys are encrypted at rest
- ✅ Keys are masked in UI
- ✅ Test connection button works
- ✅ Model selector has dropdown
- ✅ Presets can be applied
- ✅ Cost estimator shows values
- ✅ Project creation uses stored credentials
- ✅ All tests pass (60%+ coverage)
- ✅ Documentation complete

---

## 🚀 Ready to Start?

1. ✅ Read WEB_CONFIG_DESIGN.md (30 min)
2. ✅ Read IMPLEMENTATION_GUIDE.md (15 min)
3. ✅ Set up environment (5 min)
4. ✅ Create `src/web/security.py` (2 hours)
5. ✅ Follow daily checklist

**Have questions?** Check IMPLEMENTATION_GUIDE.md troubleshooting section.

**Good luck!** 🎉

---

## 📞 Resources

**Design Docs:**
- WEB_CONFIG_DESIGN.md - Full specification
- IMPLEMENTATION_GUIDE.md - Step-by-step guide
- devplan.md - Project roadmap

**Code References:**
- `src/config.py` - Existing config system
- `src/web/models.py` - Existing API models
- `src/web/routes/projects.py` - Example routes

**External Docs:**
- [Cryptography Fernet](https://cryptography.io/en/latest/fernet/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [React Hook Form](https://react-hook-form.com/)

---

**Last Updated:** October 21, 2025  
**Status:** Ready for implementation  
**First Task:** Create `src/web/security.py`
