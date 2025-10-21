# Web Configuration Directory

This directory contains configuration files for the DevPlan Orchestrator web interface.

## ⚠️ Security Notice

**DO NOT commit credentials to version control!**

The following files contain sensitive data and are excluded from git:
- `credentials/*.json` - Encrypted API keys (still sensitive!)
- `projects/*_override.json` - Project-specific configurations
- `global_config.json` - Your default settings

## Directory Structure

```
.config/
├── global_config.json          # Your default settings (gitignored)
├── credentials/                # API credentials (gitignored)
│   ├── cred_abc123.json       # OpenAI credentials
│   └── cred_def456.json       # Anthropic credentials
├── presets/                    # Configuration templates (included in git)
│   ├── cost_optimized.json    # GPT-4 + GPT-3.5 preset
│   ├── max_quality.json       # GPT-4 Turbo preset
│   ├── anthropic_claude.json  # Claude 3 preset
│   └── balanced.json          # Balanced GPT-4 preset
└── projects/                   # Project overrides (gitignored)
    └── proj_xyz_override.json
```

## Presets Explained

### 🎯 cost_optimized.json
- **Use case:** Minimize costs while maintaining quality
- **Configuration:** GPT-4 for design, GPT-3.5 Turbo for devplan/handoff
- **Estimated cost:** $0.40-0.60 per project
- **Best for:** Regular use, budget-conscious projects

### 🏆 max_quality.json
- **Use case:** Maximum output quality
- **Configuration:** GPT-4 Turbo for all stages
- **Estimated cost:** $1.00-1.50 per project
- **Best for:** Critical projects, complex requirements

### 🤖 anthropic_claude.json
- **Use case:** Alternative to OpenAI with strong reasoning
- **Configuration:** Claude 3 Opus for all stages
- **Estimated cost:** $0.80-1.20 per project
- **Best for:** Creative projects, nuanced development plans

### ⚖️ balanced.json
- **Use case:** Good middle ground
- **Configuration:** GPT-4 for all stages
- **Estimated cost:** $0.70-0.90 per project
- **Best for:** General use when quality matters

## How Configuration Works

### 1. Add API Credentials (Web UI)
```
POST /api/config/credentials
{
  "name": "OpenAI Production",
  "provider": "openai",
  "api_key": "sk-..."
}
```

API keys are encrypted with Fernet before storage. The encrypted key is saved in `credentials/cred_xxx.json`.

### 2. Set Global Configuration
```
PUT /api/config/global
{
  "default_model_config": {
    "provider_credential_id": "cred_abc123",
    "model_name": "gpt-4",
    ...
  },
  "stage_overrides": { ... }
}
```

This configuration applies to all projects unless overridden.

### 3. Apply a Preset (Optional)
```
POST /api/config/presets/apply/cost_optimized
```

Instantly configure your system with proven settings.

### 4. Create Project-Specific Override (Optional)
```
PUT /api/config/projects/proj_123
{
  "override_global": true,
  "llm_config": { ... }
}
```

Use different settings for specific projects.

## Configuration Priority

When running a project, configuration is resolved in this order:

1. **Project Override** (if exists) → highest priority
2. **Global Configuration** → default for all projects
3. **Environment Variables** → fallback (CLI compatibility)

## Encryption Key

The encryption key is stored in the `DEVUSSY_ENCRYPTION_KEY` environment variable.

**First Run:**
If not set, the system will generate a new key and display it. You should save this key:

```powershell
# Save the key permanently (Windows)
[System.Environment]::SetEnvironmentVariable('DEVUSSY_ENCRYPTION_KEY', 'YOUR_KEY_HERE', 'User')
```

**⚠️ Important:** If you lose this key, you cannot decrypt your stored API keys!

## API Endpoints

All configuration is managed through REST API endpoints:

- **Credentials:** `/api/config/credentials/*`
- **Global Config:** `/api/config/global`
- **Presets:** `/api/config/presets/*`
- **Project Overrides:** `/api/config/projects/{id}`
- **Cost Estimation:** `/api/config/estimate-cost`
- **Model Discovery:** `/api/config/models/{provider}`

See the Swagger UI documentation at `http://localhost:8000/docs` for details.

## Migration from CLI

If you're migrating from the CLI configuration (`config/config.yaml`):

1. The CLI config still works and takes precedence if environment variables are set
2. Use the web UI to create credentials matching your existing API keys
3. Set up global configuration matching your `config.yaml` settings
4. Both systems can coexist - web UI for new projects, CLI for existing workflows

## Backup and Recovery

### Backup Your Configuration
```powershell
# Backup the entire config directory
Copy-Item -Recurse web_projects/.config web_projects/.config.backup
```

### Restore Configuration
```powershell
# Restore from backup
Copy-Item -Recurse web_projects/.config.backup web_projects/.config
```

**Note:** You must have the same `DEVUSSY_ENCRYPTION_KEY` to decrypt credentials after restore.

## Troubleshooting

### "Failed to decrypt API key"
- Encryption key changed or not set
- Set `DEVUSSY_ENCRYPTION_KEY` to your original key

### "No credentials found"
- No credentials created yet
- Use the web UI or API to add credentials

### "Permission denied" errors
- File lock timeout
- Another process is accessing the config files
- Wait a few seconds and try again

---

**For more information:**
- See `WEB_CONFIG_DESIGN.md` for technical details
- See `IMPLEMENTATION_GUIDE.md` for development guide
- See API documentation at `/docs` when running the web server
