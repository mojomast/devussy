# DevPlan Orchestrator - Usage Examples

This guide provides real-world examples and usage scenarios for DevPlan Orchestrator.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Workflows](#basic-workflows)
- [Advanced Usage](#advanced-usage)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Example 1: Simple Web API Project

Generate a complete devplan for a REST API:

```bash
devussy run-full-pipeline \
  --name "Task Management API" \
  --languages "Python" \
  --frameworks "FastAPI" \
  --requirements "Build a REST API for task management with CRUD operations, user authentication, and PostgreSQL database"
```

**Output Files:**
- `project_design.md` - High-level architecture and technology choices
- `devplan.md` - Detailed development plan with phases and tasks
- `handoff_prompt.md` - Comprehensive handoff document for team transitions

### Example 2: Full-Stack Application

Create a devplan for a full-stack app:

```bash
devussy run-full-pipeline \
  --name "E-commerce Platform" \
  --languages "TypeScript,Python" \
  --frameworks "React,Next.js,Django" \
  --requirements "Build an e-commerce platform with product catalog, shopping cart, payment integration (Stripe), admin dashboard, and inventory management" \
  --provider openai \
  --streaming
```

---

## Basic Workflows

### Workflow 1: Step-by-Step Generation

Generate each artifact separately for more control:

```bash
# Step 1: Generate project design
devussy generate-design \
  --name "Mobile App Backend" \
  --languages "Go" \
  --frameworks "Gin,GORM" \
  --requirements "REST API for mobile app with push notifications, real-time updates via WebSocket, and Redis caching" \
  --output design.json

# Step 2: Generate basic devplan from design
devussy generate-devplan design.json \
  --output basic_devplan.json

# Step 3: Generate detailed devplan
devussy generate-detailed basic_devplan.json \
  --output detailed_devplan.json

# Step 4: Generate handoff prompt
devussy generate-handoff detailed_devplan.json \
  --name "Mobile App Backend" \
  --output handoff_prompt.md
```

### Workflow 2: Using Different Providers

Switch providers for different stages:

```bash
# Use GPT-4 for design phase (better reasoning)
devussy generate-design \
  --provider openai \
  --name "ML Pipeline" \
  --output design.json

# Use generic provider for devplan (cost-effective)
devussy generate-devplan design.json \
  --provider generic \
  --output devplan.json
```

### Workflow 2b: Multi-LLM Configuration (NEW! 🎭)

Use different models for different pipeline stages in a single run:

```yaml
# config/config.yaml
llm_provider: openai
model: gpt-4  # Default for design and handoff

# Use cheaper model for devplan
devplan_model: gpt-3.5-turbo
devplan_temperature: 0.5
devplan_max_tokens: 8192
```

```bash
# Run full pipeline with mixed models
devussy run-full-pipeline \
  --name "Cost-Optimized Project" \
  --languages "Python" \
  --requirements "Build a REST API" \
  --config config/config.yaml
```

**Or use environment variables:**

```bash
# Set different API keys per stage for billing separation
export DESIGN_API_KEY="sk-design-account-..."
export DEVPLAN_API_KEY="sk-devplan-account-..."
export HANDOFF_API_KEY="sk-handoff-account-..."

devussy run-full-pipeline \
  --name "Multi-Account Project" \
  --languages "Python" \
  --requirements "Build a web app"
```

**See [Multi-LLM Configuration Guide](../MULTI_LLM_GUIDE.md) for complete documentation.**

### Workflow 3: Custom Configuration

Use custom configuration file:

```bash
# Create custom config
cat > my_config.yaml << EOF
llm:
  default_provider: openai
  providers:
    openai:
      model: gpt-4
      temperature: 0.5
      max_tokens: 8000
      
pipeline:
  git_auto_commit: true
  enable_streaming: true
  max_concurrent_requests: 3
EOF

# Run with custom config
devussy run-full-pipeline \
  --config my_config.yaml \
  --name "Data Analytics Platform"
```

---

## Advanced Usage

### Example 3: Resumable Workflows with Checkpoints

Handle long-running pipelines with checkpoints:

```bash
# Start pipeline (might fail or be interrupted)
devussy run-full-pipeline \
  --name "Complex System" \
  --requirements "Very long and complex requirements..." \
  --checkpoint-key "complex-system-2024"

# List available checkpoints
devussy list-checkpoints

# Resume from checkpoint after interruption
devussy run-full-pipeline \
  --resume-from "complex-system-2024"

# Clean up old checkpoints
devussy cleanup-checkpoints --older-than 7  # days
```

### Example 4: Rate Limiting and Concurrency

Control API usage and performance:

```bash
# Low rate, sequential processing (for rate-limited APIs)
devussy run-full-pipeline \
  --name "Project" \
  --max-concurrent 1 \
  --rate-limit 3 \
  --rate-period 60

# High performance, parallel processing (for generous API limits)
devussy run-full-pipeline \
  --name "Project" \
  --max-concurrent 10 \
  --no-rate-limit
```

### Example 5: Streaming Output

Monitor progress in real-time:

```bash
# Enable streaming for live feedback
devussy run-full-pipeline \
  --name "Project" \
  --streaming \
  --provider openai

# Streaming with progress indicators
devussy run-full-pipeline \
  --name "Project" \
  --streaming \
  --verbose
```

### Example 6: Git Integration

Automatic version control:

```bash
# Initialize new repo with devplan generation
devussy init-repo ./my-new-project \
  --remote https://github.com/yourusername/my-project.git

cd my-new-project

# Generate devplan with auto-commits
devussy run-full-pipeline \
  --name "My Project" \
  --git-commit \
  --commit-message "feat: generate initial devplan"

# Each pipeline stage creates a commit
git log --oneline
# 5a3b9d2 feat: generate handoff prompt
# 4f8c1a6 feat: generate detailed devplan
# 3e7d9b8 feat: generate basic devplan
# 2c6a4f1 feat: generate project design
```

---

## Integration Examples

### Example 7: CI/CD Integration

Use in GitHub Actions:

```yaml
# .github/workflows/devplan.yml
name: Generate DevPlan

on:
  workflow_dispatch:
    inputs:
      project_name:
        description: 'Project name'
        required: true
      requirements:
        description: 'Project requirements'
        required: true

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install devussy
        run: pip install devussy
      
      - name: Generate devplan
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          devussy run-full-pipeline \
            --name "${{ github.event.inputs.project_name }}" \
            --requirements "${{ github.event.inputs.requirements }}" \
            --provider openai
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: "docs: generate devplan for ${{ github.event.inputs.project_name }}"
          title: "DevPlan: ${{ github.event.inputs.project_name }}"
          body: "Automatically generated development plan"
          branch: "devplan/${{ github.event.inputs.project_name }}"
```

### Example 8: Docker Integration

Run in containerized environment:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install devussy
RUN pip install devussy

# Copy config
COPY config.yaml .env ./

# Run devplan generation
CMD ["devussy", "run-full-pipeline", \
     "--name", "${PROJECT_NAME}", \
     "--requirements", "${REQUIREMENTS}"]
```

```bash
# Build and run
docker build -t devussy-runner .

docker run --rm \
  -e PROJECT_NAME="My App" \
  -e REQUIREMENTS="Build a web app" \
  -e OPENAI_API_KEY="sk-..." \
  -v $(pwd)/output:/app/output \
  devussy-runner
```

### Example 9: Python Script Integration

Programmatic usage in your Python code:

```python
"""Example script using DevPlan Orchestrator."""

import asyncio
import os
from pathlib import Path

from src.config import load_config
from src.pipeline.compose import PipelineOrchestrator
from src.models import ProjectDesignInput


async def generate_devplan():
    """Generate devplan programmatically."""
    # Load configuration
    config = load_config("config/config.yaml")
    
    # Create input
    design_input = ProjectDesignInput(
        project_name="Automated Report Generator",
        programming_languages=["Python"],
        frameworks=["Pandas", "Matplotlib"],
        project_requirements=(
            "Build a tool that automatically generates weekly "
            "reports from CSV data with charts and email delivery"
        ),
    )
    
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(
        config=config,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Run pipeline
    try:
        result = await orchestrator.run_full_pipeline(
            design_input=design_input,
            provider="openai",
            stream=True,
        )
        
        print(f"✅ Generated devplan: {result.devplan_path}")
        print(f"✅ Generated handoff: {result.handoff_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(generate_devplan())
```

### Example 10: Batch Processing

Generate devplans for multiple projects:

```python
"""Batch generate devplans for multiple projects."""

import asyncio
from pathlib import Path
from src.pipeline.compose import PipelineOrchestrator
from src.models import ProjectDesignInput

# Project definitions
PROJECTS = [
    {
        "name": "Auth Service",
        "languages": ["Go"],
        "frameworks": ["Gin", "JWT"],
        "requirements": "Microservice for user authentication with OAuth2",
    },
    {
        "name": "Payment Gateway",
        "languages": ["Python"],
        "frameworks": ["FastAPI", "Stripe"],
        "requirements": "Payment processing service with Stripe integration",
    },
    {
        "name": "Admin Dashboard",
        "languages": ["TypeScript"],
        "frameworks": ["React", "TailwindCSS"],
        "requirements": "Admin panel for managing users and transactions",
    },
]


async def generate_all():
    """Generate devplans for all projects."""
    orchestrator = PipelineOrchestrator(config=load_config())
    
    tasks = []
    for project in PROJECTS:
        design_input = ProjectDesignInput(
            project_name=project["name"],
            programming_languages=project["languages"],
            frameworks=project["frameworks"],
            project_requirements=project["requirements"],
        )
        
        # Create task for each project
        task = orchestrator.run_full_pipeline(
            design_input=design_input,
            output_dir=Path(f"output/{project['name'].lower().replace(' ', '_')}"),
        )
        tasks.append(task)
    
    # Run all in parallel (respecting rate limits)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Report results
    for project, result in zip(PROJECTS, results):
        if isinstance(result, Exception):
            print(f"❌ {project['name']}: {result}")
        else:
            print(f"✅ {project['name']}: Complete")


if __name__ == "__main__":
    asyncio.run(generate_all())
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Rate Limit Errors

```bash
# Error: "Rate limit exceeded"
# Solution: Reduce concurrency and add rate limiting

devussy run-full-pipeline \
  --name "Project" \
  --max-concurrent 1 \
  --rate-limit 3 \
  --rate-period 60
```

#### Issue 2: Timeout Errors

```bash
# Error: "Request timeout after 60s"
# Solution: Increase timeout in config

# In config.yaml:
llm:
  providers:
    openai:
      timeout: 180  # Increase to 3 minutes
```

#### Issue 3: Missing API Keys

```bash
# Error: "API key not found"
# Solution: Check .env file

# Verify environment variables
cat .env

# Or set directly in shell
export OPENAI_API_KEY="sk-..."
devussy run-full-pipeline --name "Project"
```

#### Issue 4: Checkpoint Not Found

```bash
# Error: "Checkpoint 'xyz' not found"
# Solution: List available checkpoints

devussy list-checkpoints

# Use correct checkpoint key
devussy run-full-pipeline --resume-from "correct-key-here"
```

#### Issue 5: Template Not Found

```bash
# Error: "Template 'custom.jinja' not found"
# Solution: Verify template path

# Templates should be in:
# templates/
#   project_design.jinja
#   basic_devplan.jinja
#   detailed_devplan.jinja
#   handoff_prompt.jinja

# Check current directory
ls templates/
```

### Debugging Tips

**Enable verbose logging:**
```bash
devussy run-full-pipeline \
  --name "Project" \
  --verbose \
  --log-level DEBUG
```

**Check logs:**
```bash
# Logs are in logs/ directory
cat logs/devussy_$(date +%Y%m%d).log
```

**Validate configuration:**
```bash
# Test config loading
python -c "from src.config import load_config; print(load_config())"
```

**Test API connectivity:**
```bash
# Quick test with generate-design
devussy generate-design \
  --name "Test" \
  --languages "Python" \
  --requirements "Test project" \
  --output test.json
```

---

## Best Practices

### 1. Use Checkpoints for Long Pipelines

Always use checkpoint keys for pipelines that take >5 minutes:

```bash
devussy run-full-pipeline \
  --name "Large Project" \
  --checkpoint-key "large-project-$(date +%Y%m%d)"
```

### 2. Version Control Your Devplans

Commit generated devplans to track evolution:

```bash
git add *.md
git commit -m "docs: update devplan after requirements change"
```

### 3. Use Environment-Specific Configs

Maintain separate configs for different environments:

```bash
# Development
devussy run-full-pipeline --config config/dev.yaml

# Production
devussy run-full-pipeline --config config/prod.yaml
```

### 4. Monitor API Usage

Track API calls to manage costs:

```bash
# Use rate limiting
devussy run-full-pipeline \
  --rate-limit 5 \
  --rate-period 60 \
  --verbose  # Shows API call count
```

### 5. Iterate on Requirements

Refine requirements based on initial output:

```bash
# First pass
devussy generate-design --name "App" --output v1.json

# Review v1.json, then refine
devussy generate-design \
  --name "App" \
  --requirements "Refined requirements based on v1..." \
  --output v2.json
```

---

## Additional Resources

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Testing**: See [TESTING.md](TESTING.md) for testing strategies
- **Providers**: See [PROVIDERS.md](PROVIDERS.md) for adding LLM providers
- **API Docs**: Run `python scripts/build_docs.py` to generate API documentation

---

## Support and Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/mojomast/devussy-fresh/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/mojomast/devussy-fresh/discussions)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines

---

**Happy Planning! 🚀**
