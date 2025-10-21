# Architecture Overview

This document describes the system architecture, design patterns, and key technical decisions for the DevPlan Orchestrator.

## System Overview

DevPlan Orchestrator is a Python-based tool that orchestrates multiple Large Language Models (LLMs) to automatically generate comprehensive development plans and handoff documentation. The system is designed with modularity, extensibility, and reliability as core principles.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Web Interface (React + TypeScript)              │
│                    Frontend: http://localhost:3000                 │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ REST API + WebSocket
┌─────────────────────────▼───────────────────────────────────────────┐
│                     FastAPI Web Backend                            │
│                    Backend: http://localhost:8000                  │
│   ├── Configuration API (Encrypted storage)                       │
│   ├── Projects API (CRUD + WebSocket streaming)                  │
│   └── Templates API (Import/Export)                              │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                          CLI Interface                              │
│                         (src/cli.py)                               │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                   Pipeline Orchestrator                            │
│                  (src/pipeline/compose.py)                         │
└─────┬───────────┬───────────┬───────────┬───────────────────────────┘
      │           │           │           │
      ▼           ▼           ▼           ▼
┌───────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│ Project   │ │ Basic   │ │Detailed │ │   Handoff    │
│ Design    │ │DevPlan  │ │DevPlan  │ │   Prompt     │
│Generator  │ │Generator│ │Generator│ │  Generator   │
└─────┬─────┘ └────┬────┘ └────┬────┘ └──────┬───────┘
      │            │           │              │
      └────────────┼───────────┼──────────────┘
                   │           │
                   ▼           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LLM Client Layer                              │
│                    (src/clients/*)                                │
├─────────────────┬───────────────────┬───────────────────────────────┤
│   OpenAI Client │  Generic Client   │      Requesty Client          │
│                 │  (OpenAI-compat)  │                               │
└─────────────────┴───────────────────┴───────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Support Services                                │
├─────────────┬─────────────┬─────────────┬─────────────────────────────┤
│ Concurrency │   Retry     │ Templates   │    Git Integration          │
│   Control   │   Logic     │  & Citations│                             │
│             │             │             │                             │
└─────────────┴─────────────┴─────────────┴─────────────────────────────┘
```

## Core Components

### 1. Web Interface (Phases 11-16) ✅

**Frontend** (`frontend/` directory):
- **Technology Stack**: React 18 + TypeScript + Vite + Tailwind CSS
- **State Management**: React hooks (useState, useEffect, useMemo)
- **Routing**: React Router v6
- **API Client**: Axios for REST, native WebSocket for streaming
- **UI Components**:
  - ProjectsListPage: Grid view with search, filter, sort, pagination
  - ProjectDetailPage: Real-time monitoring with WebSocket
  - TemplatesPage: Template CRUD with search/filter/import/export
  - SettingsPage: API key management with 3-tab interface
  - HomePage: Dashboard with analytics
- **Features**:
  - Dark mode with theme persistence
  - Markdown rendering with syntax highlighting
  - Toast notifications (react-hot-toast)
  - Error boundary for graceful failures
  - Skeleton loaders for better UX
  - File operations (copy, download, ZIP)
- **Testing**: 42 component tests with Vitest + React Testing Library

**Backend** (`src/web/` directory):
- **Framework**: FastAPI with async/await
- **API Routes**:
  - `/api/config/*` - Configuration and credentials management
  - `/api/projects/*` - Project CRUD operations
  - `/api/templates/*` - Template management with import/export
  - `/ws/projects/{id}` - WebSocket for real-time streaming
- **Security**:
  - Fernet encryption for API keys at rest
  - CORS configuration for local development
  - Input validation with Pydantic models
- **Storage**: JSON file-based (config/, web_projects/)
- **Testing**: 27 tests for web components (98% coverage)

**Key Design Decisions**:
- Separate backend/frontend servers for development flexibility
- WebSocket for real-time progress updates during generation
- File-based storage (easy to migrate to database later)
- Encrypted storage for API keys using Python cryptography
- Template import/export as JSON for portability

### 2. CLI Interface

### 1. Configuration System (`src/config.py`)

**Purpose**: Centralized configuration management with environment variable support and per-stage LLM configuration.

**Key Features**:
- Pydantic-based models for type safety and validation
- YAML file loading with environment variable overrides
- Nested configuration for different subsystems
- Provider-specific settings
- **NEW: Per-stage LLM configuration** - Use different models/API keys for each pipeline stage

**Models**:
- `AppConfig`: Main configuration container with per-stage LLM support
- `LLMConfig`: LLM provider settings with merge capability
- `RetryConfig`: Retry logic parameters
- `GitConfig`: Git integration settings
- `DocumentationConfig`: Documentation generation settings
- `PipelineConfig`: Pipeline execution settings

**Per-Stage Configuration** (New in v0.2.0):
```python
class AppConfig(BaseModel):
    llm: LLMConfig  # Global/fallback config
    design_llm: Optional[LLMConfig]  # Override for design stage
    devplan_llm: Optional[LLMConfig]  # Override for devplan stage
    handoff_llm: Optional[LLMConfig]  # Override for handoff stage
    
    def get_llm_config_for_stage(self, stage: str) -> LLMConfig:
        """Get effective config with stage-specific overrides."""
        ...
```

This allows cost optimization by using different models per stage (e.g., GPT-4 for design, GPT-3.5-turbo for devplan).

### 2. LLM Client Architecture

#### Abstract Interface (`src/llm_client.py`)

```python
class LLMClient(abc.ABC):
    @abc.abstractmethod
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt."""
        pass
    
    async def generate_multiple(self, prompts: Iterable[str]) -> List[str]:
        """Generate multiple completions concurrently."""
        pass
```

#### Client Implementations

1. **OpenAI Client** (`src/clients/openai_client.py`)
   - Uses `AsyncOpenAI` SDK
   - Supports chat completions API
   - Built-in retry logic with tenacity

2. **Generic OpenAI-Compatible Client** (`src/clients/generic_client.py`)
   - Uses `aiohttp` for HTTP requests
   - Works with any OpenAI-compatible API
   - Custom base URL support

3. **Requesty Client** (`src/clients/requesty_client.py`)
   - Placeholder for Requesty API
   - Custom API format support
   - Extensible for future providers

#### Factory Pattern (`src/clients/factory.py`)

```python
def create_llm_client(config: AppConfig) -> LLMClient:
    """Create appropriate client based on configuration."""
    provider = config.llm.provider.lower()
    if provider == "openai":
        return OpenAIClient(config)
    elif provider == "generic":
        return GenericOpenAIClient(config)
    elif provider == "requesty":
        return RequestyClient(config)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
```

### 3. Pipeline Architecture (`src/pipeline/`)

The pipeline follows a multi-stage approach:

1. **Project Design Generation** (`project_design.py`)
   - Analyzes user requirements
   - Recommends technology stack
   - Identifies potential challenges

2. **Basic DevPlan Generation** (`basic_devplan.py`)
   - Creates high-level phase breakdown
   - Defines major milestones

3. **Detailed DevPlan Generation** (`detailed_devplan.py`)
   - Generates numbered, actionable steps
   - Uses concurrent API calls for efficiency
   - Creates comprehensive implementation plan

4. **Handoff Prompt Generation** (`handoff_prompt.py`)
   - Generates handoff documentation
   - Includes progress tracking
   - Provides context for next developer

5. **Pipeline Orchestration** (`compose.py`)
   - Coordinates all pipeline stages
   - Manages intermediate artifacts
   - Handles Git integration
   - **NEW: Stage-specific LLM client management** - Creates and uses different LLM clients per stage

## Multi-LLM Architecture (v0.2.0 Feature)

### Overview

The system now supports **per-stage LLM configuration**, allowing different models, providers, and API keys for each pipeline stage. This enables:
- **Cost Optimization**: Use expensive models only where needed
- **Performance Tuning**: Match model capabilities to task complexity
- **Billing Separation**: Track usage per stage with separate API keys
- **Provider Mixing**: Combine different LLM providers in one pipeline

### Implementation

**Stage-Specific Clients** (`src/pipeline/compose.py`):
```python
class PipelineOrchestrator:
    def _initialize_stage_clients(self):
        # Create separate clients for each stage
        self.design_client = create_llm_client(design_config)
        self.devplan_client = create_llm_client(devplan_config)
        self.handoff_client = create_llm_client(handoff_config)
```

**Configuration Merging** (`src/config.py`):
```python
def get_llm_config_for_stage(self, stage: str) -> LLMConfig:
    """Merge global config with stage-specific overrides."""
    stage_config = getattr(self, f"{stage}_llm", None)
    return self.llm.merge_with(stage_config)
```

### Usage Example

```yaml
# config/config.yaml
llm_provider: openai
model: gpt-4  # Default for all stages

# Override devplan to use cheaper model
devplan_model: gpt-3.5-turbo
devplan_temperature: 0.5
devplan_max_tokens: 8192
```

Or via environment variables:
```bash
export DESIGN_API_KEY="sk-design-..."
export DEVPLAN_API_KEY="sk-devplan-..."
export HANDOFF_API_KEY="sk-handoff-..."
```

See [Multi-LLM Configuration Guide](../MULTI_LLM_GUIDE.md) for complete documentation.

## Design Patterns

### 1. Factory Pattern
- **Used for**: LLM client creation, per-stage client instantiation
- **Benefits**: Easy provider switching, extensibility, stage-specific configuration
- **Implementation**: `src/clients/factory.py`

### 2. Template Method Pattern
- **Used for**: Pipeline stages
- **Benefits**: Consistent stage interface, reusable components
- **Implementation**: Base classes in `src/pipeline/`

### 3. Strategy Pattern
- **Used for**: Retry strategies, concurrency control, per-stage LLM selection
- **Benefits**: Configurable behavior, testability, flexible model selection
- **Implementation**: `src/retry.py`, `src/concurrency.py`, `src/config.py`

### 4. Observer Pattern
- **Used for**: Documentation logging, progress tracking
- **Benefits**: Decoupled logging, extensible notifications
- **Implementation**: `src/doc_logger.py`

### 5. Merge/Override Pattern (NEW)
- **Used for**: Per-stage configuration merging
- **Benefits**: DRY configuration, flexible overrides
- **Implementation**: `LLMConfig.merge_with()` in `src/config.py`

## Data Flow

### 1. Pipeline Execution Flow

```
User Input → Configuration Loading → Pipeline Orchestrator
    ↓
Project Design Generation → Template Rendering → LLM API Call
    ↓
Basic DevPlan Generation → Template Rendering → LLM API Call  
    ↓
Detailed DevPlan Generation → Concurrent Template Rendering → Multiple LLM API Calls
    ↓
Handoff Prompt Generation → Template Rendering → LLM API Call
    ↓
Git Integration → Documentation Generation → File System
```

### 2. Data Models (`src/models.py`)

```python
class ProjectDesign(BaseModel):
    """Project design with technology recommendations."""
    project_name: str
    objectives: List[str]
    technology_stack: Dict[str, Any]
    architecture_overview: str
    dependencies: List[str]
    challenges: List[str]

class DevPlan(BaseModel):
    """Complete development plan."""
    project_design: ProjectDesign
    phases: List[DevPlanPhase]
    total_steps: int
    estimated_duration: Optional[str]

class DevPlanPhase(BaseModel):
    """Individual phase in development plan."""
    phase_number: int
    title: str
    description: str
    steps: List[DevPlanStep]

class DevPlanStep(BaseModel):
    """Individual step within a phase."""
    step_number: str  # e.g., "1.1", "2.3"
    title: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str]
```

## Support Systems

### 1. Concurrency Control (`src/concurrency.py`)

**Purpose**: Manage concurrent API requests to prevent rate limiting.

**Implementation**:
```python
class ConcurrencyManager:
    def __init__(self, config: Any, max_concurrent: Optional[int] = None):
        self._limit = max_concurrent or config.max_concurrent_requests
        self._semaphore = asyncio.Semaphore(self._limit)
    
    async def run_with_limit(self, coro: Awaitable[T]) -> T:
        async with self._semaphore:
            return await coro
```

### 2. Retry Logic (`src/retry.py`)

**Purpose**: Handle transient failures with exponential backoff.

**Features**:
- Configurable retry attempts and delays
- Exponential backoff with jitter
- Custom exception handling
- Async function support

### 3. Template System (`src/templates.py`, `src/citations.py`)

**Purpose**: Consistent prompt generation and documentation formatting.

**Components**:
- **Template Loading**: Jinja2-based template system
- **Citation Embedding**: Automatic citation replacement
- **Template Caching**: LRU cache for performance

### 4. Git Integration (`src/git_manager.py`)

**Purpose**: Automatic version control and documentation tracking.

**Features**:
- Repository initialization
- Automatic commits after pipeline stages
- Branch and tag management
- Cross-platform compatibility

### 5. Documentation System

**Components**:
- **Documentation Logger** (`src/doc_logger.py`): Track documentation changes
- **Documentation Indexer** (`src/doc_index.py`): Generate documentation index
- **File Manager** (`src/file_manager.py`): Handle file operations
- **Citation Manager** (`src/citations.py`): Manage citation embedding

## Error Handling Strategy

### 1. Layered Error Handling

1. **API Level**: Retry logic with exponential backoff
2. **Client Level**: Provider-specific error translation
3. **Pipeline Level**: Stage-specific error recovery
4. **CLI Level**: User-friendly error messages

### 2. Error Types

- **Configuration Errors**: Invalid YAML, missing API keys
- **API Errors**: Rate limiting, authentication failures
- **Network Errors**: Connection timeouts, DNS issues
- **File System Errors**: Permission issues, disk space
- **Template Errors**: Missing templates, invalid context

### 3. Recovery Strategies

- **Automatic Retry**: For transient errors
- **Graceful Degradation**: Continue with reduced functionality
- **State Persistence**: Save progress for manual recovery
- **Detailed Logging**: For debugging and monitoring

## Performance Considerations

### 1. Asynchronous Execution

- **AsyncIO**: Used throughout for non-blocking operations
- **Concurrent API Calls**: Multiple LLM requests in parallel
- **Connection Pooling**: Reuse HTTP connections
- **Semaphore Limits**: Prevent overwhelming APIs

### 2. Caching Strategy

- **Template Caching**: LRU cache for compiled templates
- **Configuration Caching**: Avoid repeated YAML parsing
- **State Persistence**: Resume from checkpoints

### 3. Memory Management

- **Streaming**: Process large responses in chunks
- **Lazy Loading**: Load templates and configs on demand
- **Garbage Collection**: Explicit cleanup of temporary objects

## Security Considerations

### 1. API Key Management

- **Environment Variables**: Never hard-code API keys
- **Configuration Isolation**: Separate config from code
- **Key Rotation**: Support for updating keys without restart

### 2. Input Validation

- **Pydantic Models**: Type validation for all inputs
- **Template Sanitization**: Prevent injection attacks
- **File Path Validation**: Prevent directory traversal

### 3. Network Security

- **HTTPS Only**: All API communications encrypted
- **Certificate Validation**: Verify SSL certificates
- **Timeout Controls**: Prevent hanging connections

## Extensibility

### 1. Adding New LLM Providers

1. Implement `LLMClient` interface
2. Add provider configuration to `LLMConfig`
3. Update factory method
4. Add provider-specific tests

### 2. Adding New Pipeline Stages

1. Create new generator class
2. Add template files
3. Update pipeline orchestrator
4. Add configuration options

### 3. Adding New Documentation Formats

1. Create new template files
2. Update documentation generator
3. Add format-specific configuration

## Testing Architecture

### 1. Test Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Mock Strategy**: External dependencies mocked
- **Isolation**: Temporary files/directories for tests

### 2. Coverage Targets

- **Overall**: >80% code coverage
- **Critical Paths**: >90% coverage
- **Error Handling**: All error paths tested

## Deployment Considerations

### 1. Environment Requirements

- **Python**: 3.8+
- **Dependencies**: Listed in `requirements.txt`
- **System**: Cross-platform (Windows, macOS, Linux)

### 2. Configuration Management

- **Environment Variables**: For sensitive configuration
- **YAML Files**: For application settings
- **CLI Options**: For runtime overrides

### 3. Monitoring and Logging

- **Structured Logging**: JSON format for analysis
- **Log Levels**: Configurable verbosity
- **Error Tracking**: Detailed error reporting

## Future Architecture Considerations

### 1. Scalability

- **Horizontal Scaling**: Multiple worker processes
- **Queue System**: For large workloads
- **Database Integration**: For state persistence

### 2. Performance

- **Caching Layer**: Redis for shared cache
- **CDN Integration**: For template delivery
- **Load Balancing**: For API requests

### 3. Security

- **OAuth Integration**: For enterprise authentication
- **Audit Logging**: For compliance requirements
- **Encryption**: For sensitive data storage