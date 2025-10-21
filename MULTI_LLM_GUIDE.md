# Multi-LLM Configuration Guide

## 🎯 Overview

The DevPlan Orchestrator now supports **per-stage LLM configuration**, allowing you to use different API keys, models, and providers for each pipeline stage:

- **Design Stage** - Project design generation
- **DevPlan Stage** - Development plan creation
- **Handoff Stage** - Handoff prompt generation

This enables cost optimization (use cheaper models for simpler tasks) and flexibility (mix different providers).

---

## 📋 Configuration Methods

### 1. Config File (`config/config.yaml`)

```yaml
# Global LLM Configuration (fallback for all stages)
llm_provider: openai
model: gpt-4
temperature: 0.7
max_tokens: 4096

# Per-Stage Overrides (optional)
design_llm_provider: openai
design_model: gpt-4
design_temperature: 0.7
design_max_tokens: 4096

devplan_llm_provider: openai
devplan_model: gpt-3.5-turbo  # Use cheaper model
devplan_temperature: 0.5
devplan_max_tokens: 8192

handoff_llm_provider: openai
handoff_model: gpt-4
handoff_temperature: 0.8
handoff_max_tokens: 4096
```

### 2. Environment Variables

```powershell
# Global API key (fallback)
$env:OPENAI_API_KEY = "sk-..."

# Per-stage API keys (override global)
$env:DESIGN_API_KEY = "sk-design-..."
$env:DEVPLAN_API_KEY = "sk-devplan-..."
$env:HANDOFF_API_KEY = "sk-handoff-..."

# Per-stage models
$env:DESIGN_MODEL = "gpt-4"
$env:DEVPLAN_MODEL = "gpt-3.5-turbo"
$env:HANDOFF_MODEL = "gpt-4"

# Per-stage providers
$env:DESIGN_LLM_PROVIDER = "openai"
$env:DEVPLAN_LLM_PROVIDER = "openai"
$env:HANDOFF_LLM_PROVIDER = "openai"
```

### 3. Interactive Prompt

When running `interactive-design`, the CLI will:
1. Check for missing API keys across all stages
2. Prompt you to enter keys if needed
3. Apply the key to all missing stages

---

## 🚀 Usage Examples

### Example 1: Use GPT-4 for Design, GPT-3.5 for DevPlan

**config/config.yaml:**
```yaml
llm_provider: openai
model: gpt-4  # Default

devplan_model: gpt-3.5-turbo  # Override for devplan
```

**Run:**
```powershell
python -m src.cli run-full-pipeline --name "My Project" --languages "Python" --requirements "Build an API"
```

### Example 2: Different API Keys per Stage

**PowerShell:**
```powershell
$env:DESIGN_API_KEY = "sk-design-account-..."
$env:DEVPLAN_API_KEY = "sk-devplan-account-..."
$env:HANDOFF_API_KEY = "sk-handoff-account-..."

python -m src.cli interactive-design
```

### Example 3: Mix Providers

```yaml
llm_provider: openai
model: gpt-4

devplan_llm_provider: generic
devplan_base_url: https://api.anthropic.com/v1
devplan_model: claude-3-opus-20240229
```

---

## 🔧 How It Works

### 1. Config Loading (`src/config.py`)

- `AppConfig` now includes optional `design_llm`, `devplan_llm`, `handoff_llm` fields
- `get_llm_config_for_stage(stage)` merges global config with stage-specific overrides
- `LLMConfig.merge_with(override)` handles merging logic

### 2. Pipeline Orchestrator (`src/pipeline/compose.py`)

- `_initialize_stage_clients()` creates separate LLM clients for each stage
- Each generator uses its stage-specific client:
  - `project_design_gen` → `design_client`
  - `basic_devplan_gen` → `devplan_client`
  - `detailed_devplan_gen` → `devplan_client`
  - `handoff_gen` → `handoff_client` (template-based, no LLM)

### 3. Interactive CLI (`src/cli.py`)

- Checks all stage configs for missing API keys
- Prompts user to enter keys before starting questionnaire
- Applies entered key to all missing stages

---

## 🧪 Testing

Run the test script to verify your configuration:

```powershell
python test_multi_llm.py
```

**Expected Output:**
```
============================================================
Testing Multi-LLM Configuration
============================================================

✓ Config loaded successfully

📋 Global LLM Config:
   Provider: openai
   Model: gpt-4
   API Key: ✓ Set
   Temperature: 0.7
   Max Tokens: 4096

📋 Per-Stage LLM Configs:

   DESIGN Stage:
      Provider: openai
      Model: gpt-4
      API Key: ✓ Set
      Temperature: 0.7
      Max Tokens: 4096

   DEVPLAN Stage:
      Provider: openai
      Model: gpt-3.5-turbo
      API Key: ✓ Set
      Temperature: 0.5
      Max Tokens: 8192
```

---

## 💡 Best Practices

### Cost Optimization
- Use GPT-4 for design and handoff (complex reasoning)
- Use GPT-3.5-turbo for devplan (structured output)

### API Key Management
- Use environment variables for sensitive keys
- Set different keys per stage to track usage/costs separately
- Use `.env` file with `dotenv` for local development

### Model Selection
- **Design**: Needs creativity → GPT-4, Claude Opus
- **DevPlan**: Needs structure → GPT-3.5-turbo, GPT-4
- **Handoff**: Needs clarity → GPT-4, Claude Sonnet

---

## 📝 Files Modified

1. **`src/config.py`**
   - Added `design_llm`, `devplan_llm`, `handoff_llm` fields to `AppConfig`
   - Added `LLMConfig.merge_with()` method
   - Added `AppConfig.get_llm_config_for_stage()` method
   - Updated `load_config()` to parse per-stage configs from YAML and env vars

2. **`src/pipeline/compose.py`**
   - Added `_initialize_stage_clients()` method
   - Added `design_client`, `devplan_client`, `handoff_client` attributes
   - Updated `_initialize_generators()` to use stage-specific clients

3. **`src/cli.py`**
   - Updated `interactive_design` to check stage-specific API keys
   - Added per-stage API key prompting

4. **`config/config.yaml`**
   - Added commented examples for per-stage configuration

5. **`test_multi_llm.py`** (new)
   - Test script to verify multi-LLM configuration

---

## 🔍 Troubleshooting

### "No API key configured" error
- Set `OPENAI_API_KEY` environment variable
- Or set stage-specific keys: `DESIGN_API_KEY`, `DEVPLAN_API_KEY`, etc.
- Or configure in `config/config.yaml`

### "Provider must be one of..." error
- Valid providers: `openai`, `generic`, `requesty`
- Check spelling in config file

### Stage using wrong model
- Check `config/config.yaml` for stage-specific overrides
- Check environment variables (they take precedence)
- Run `python test_multi_llm.py` to see effective configuration

---

## 🎉 Summary

You can now:
✅ Use different models per pipeline stage  
✅ Use different API keys per stage  
✅ Mix different providers per stage  
✅ Optimize costs by using cheaper models where appropriate  
✅ Track usage per stage with separate API keys  

**Next Steps:**
1. Set your API keys (global or per-stage)
2. Run `python test_multi_llm.py` to verify
3. Run `python -m src.cli interactive-design` to try it out!

---

*Updated: October 19, 2025*  
*Multi-LLM Configuration - MVP Complete*
