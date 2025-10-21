# Quick Start: Multi-LLM Setup

## 🚀 3-Minute Setup

### Option 1: Same Model, One API Key (Simplest)

```powershell
# Set one API key for everything
$env:OPENAI_API_KEY = "sk-your-key-here"

# Run interactive design
python -m src.cli interactive-design
```

---

### Option 2: Different Models, Same API Key (Cost Optimization)

**Edit `config/config.yaml`:**
```yaml
llm_provider: openai
model: gpt-4

# Use cheaper model for devplan
devplan_model: gpt-3.5-turbo
```

**Run:**
```powershell
$env:OPENAI_API_KEY = "sk-your-key-here"
python -m src.cli interactive-design
```

**Result:**
- Design uses GPT-4 (complex reasoning)
- DevPlan uses GPT-3.5-turbo (saves $$)
- Handoff uses GPT-4 (default)

---

### Option 3: Different API Keys per Stage (Tracking)

```powershell
# Set different keys for each stage
$env:DESIGN_API_KEY = "sk-design-key-here"
$env:DEVPLAN_API_KEY = "sk-devplan-key-here"
$env:HANDOFF_API_KEY = "sk-handoff-key-here"

python -m src.cli interactive-design
```

**Why?** Track usage and costs separately per stage!

---

## 🧪 Test Your Setup

```powershell
python test_multi_llm.py
```

This shows:
- ✓ What configs are loaded
- ✓ Which models will be used per stage
- ✓ Whether API keys are set

---

## 📝 Example: Full Pipeline with Different Models

**config/config.yaml:**
```yaml
llm_provider: openai
model: gpt-4
temperature: 0.7

# Override devplan to use cheaper model
devplan_model: gpt-3.5-turbo
devplan_temperature: 0.5
devplan_max_tokens: 8192
```

**PowerShell:**
```powershell
# Set API key
$env:OPENAI_API_KEY = "sk-..."

# Run full pipeline
python -m src.cli run-full-pipeline `
  --name "My API Project" `
  --languages "Python" `
  --requirements "Build a REST API with authentication"
```

**What happens:**
1. Design generation → GPT-4 @ 0.7 temp
2. DevPlan generation → GPT-3.5-turbo @ 0.5 temp
3. Handoff generation → GPT-4 @ 0.7 temp (default)

---

## 🎯 Common Scenarios

### Scenario 1: Budget-Conscious Developer
```yaml
model: gpt-3.5-turbo  # Default: cheap
design_model: gpt-4   # Only use GPT-4 where needed
```

### Scenario 2: Multiple OpenAI Accounts
```powershell
$env:DESIGN_API_KEY = "sk-account1-..."
$env:DEVPLAN_API_KEY = "sk-account2-..."
```

### Scenario 3: Testing Different Providers
```yaml
llm_provider: openai
model: gpt-4

devplan_llm_provider: generic
devplan_base_url: https://api.anthropic.com/v1
devplan_model: claude-3-opus-20240229
```

---

## ❓ FAQ

**Q: Do I need to set all three stage keys?**  
A: No! If a stage key is missing, it falls back to the global `OPENAI_API_KEY`.

**Q: Can I use different providers per stage?**  
A: Yes! Set `design_llm_provider`, `devplan_llm_provider`, etc.

**Q: How do I know which config is being used?**  
A: Run `python test_multi_llm.py` to see effective configuration.

**Q: Does this work with interactive-design?**  
A: Yes! The CLI will check for missing keys and prompt you.

---

## 🎉 You're Ready!

Pick your setup above and run:
```powershell
python -m src.cli interactive-design
```

Or see the full guide in `MULTI_LLM_GUIDE.md`.
