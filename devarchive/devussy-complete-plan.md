# Devussy Complete Terminal UI Implementation Plan

## Overview

This is the complete, integrated implementation plan that combines:
1. **Terminal-based streaming UI** - 5 concurrent phases with real-time token output
2. **Interview mode for existing projects** - Analyze codebases, ask questions, generate tailored devplans
3. **Steering workflow** - Cancel → interview → regenerate with feedback
4. **Non-blocking interruption** - User can steer one phase while others keep generating

All in the terminal, no web frontend required.

---

## Architecture Overview

```
devussy interview /path/to/project
    ↓
RepositoryAnalyzer → detects type, structure, patterns, dependencies
    ↓
InterviewEngine → asks 7 questions about goals and scope
    ↓
CodeSampleExtractor → pulls relevant code snippets
    ↓
DevPlanGenerator → creates tailored devplan with context
    ↓
devussy generate-terminal devplan-interview.json
    ↓
TerminalStreamerWithSteering → shows all 5 phases streaming
    ↓
User can: press C to cancel, answer steering questions, regenerate
    ↓
Other 4 phases keep streaming in background
    ↓
✅ Complete with integrated feedback loop
```

---

## PHASE 1: Repository Analysis Engine (Days 1-2)

### What it does:
- Scan existing project directory structure
- Detect project type (Node, Python, Go, Rust, Java, etc.)
- Parse dependencies from package.json/requirements.txt/etc
- Count lines of code and estimate complexity
- Detect test frameworks, build tools, code patterns
- Extract code samples from relevant files

### Key Files to Build:

**Python status:** A Python implementation of `RepositoryAnalyzer` exists at `src/interview/repository_analyzer.py`, with dataclasses mirroring `RepoAnalysis` and basic analysis for Python/Node projects (type detection, top-level structure, dependency manifests, metrics, patterns, and config files). The TypeScript snippets below remain the architectural reference and a potential future Node/TS implementation.

#### 1.1 RepositoryAnalyzer

```typescript
// src/interview/repository-analyzer.ts

export interface RepoAnalysis {
  rootPath: string;
  projectType: string; // 'node', 'python', 'go', 'rust', etc
  structure: DirectoryStructure;
  dependencies: DependencyInfo;
  codeMetrics: CodeMetrics;
  patterns: CodePatterns;
  config: ConfigFiles;
  errors?: string[];
}

export class RepositoryAnalyzer {
  async analyze(): Promise<RepoAnalysis> {
    return {
      rootPath: this.rootPath,
      projectType: await this.detectProjectType(),
      structure: await this.analyzeStructure(),
      dependencies: await this.analyzeDependencies(),
      codeMetrics: await this.analyzeCodeMetrics(),
      patterns: await this.detectPatterns(),
      config: await this.extractConfigFiles(),
    };
  }
  
  private async detectProjectType(): Promise<string> {
    // Check for: package.json, requirements.txt, go.mod, Cargo.toml, etc
  }
  
  private async analyzeStructure(): Promise<DirectoryStructure> {
    // Find main folders, count files, detect tests, detect CI
  }
  
  private async analyzeDependencies(): Promise<DependencyInfo> {
    // Parse package managers
  }
  
  private async analyzeCodeMetrics(): Promise<CodeMetrics> {
    // Count lines, detect languages, estimate complexity
  }
  
  private async detectPatterns(): Promise<CodePatterns> {
    // Find test framework, build tool, async patterns, code style
  }
}
```

#### 1.2 CodeSampleExtractor

```typescript
// src/interview/code-sample-extractor.ts

export class CodeSampleExtractor {
  async extractSamples(
    selectedParts: string[],
    analysis: RepoAnalysis
  ): Promise<CodeSamples> {
    return {
      architecture: await this.extractArchitectureSample(),
      patterns: await this.extractPatternSamples(),
      relevant: await this.extractRelevantCode(selectedParts),
      tests: await this.extractTestSample(),
    };
  }
}
```

### Deliverables:
- ✅ RepositoryAnalyzer class with full detection logic
- ✅ CodeSampleExtractor for pulling code snippets
- ✅ Support for 5+ project types
- ✅ Comprehensive testing on diverse projects
- ✅ Error handling for malformed projects

#### Python implementation status

- Implemented Python `RepositoryAnalyzer` in `src/interview/repository_analyzer.py` that:
  - Detects project type via manifest presence (Node, Python, Go, Rust, Java markers).
  - Captures top-level directory structure and classifies common folders (`src`, `tests`, `config`, `.github`/CI).
  - Parses Python `requirements.txt` / `pyproject.toml` and Node `package.json` into per-ecosystem `DependencyInfo` lists.
  - Infers `CodePatterns.test_frameworks` and `CodePatterns.build_tools` from parsed dependencies (e.g., `pytest`, `jest`, `webpack`, `tox`).
  - Collects common config files (pyproject, pytest.ini, package.json, tsconfig, etc.).
- Added unit tests in `tests/unit/test_repository_analyzer.py` covering project type detection, structure, manifests, metrics, pattern hints, config discovery, dependency parsing, and directory classification.
- Remaining work for Phase 1:
  - Extend dependency parsing and pattern detection for Go/Rust/Java ecosystems.
  - Capture richer metrics (per-language file counts, simple complexity hints) and more patterns.
  - Harden error handling for malformed/mixed repos.
  - Integrate `RepositoryAnalyzer` into the CLI/LLM interview flow and eventual `devussy interview` command.

### Testing:
```bash
npm test -- src/interview/repository-analyzer.test.ts
```

---

## PHASE 2: Interview Engine (Days 3-4)

### What it does:
- Present 7 interactive questions to the user
- Ask about project goals, scope, affected parts
- Ask about development approach (TDD vs implementation-first)
- Record all answers for devplan generation

### Key Files to Build:

#### 2.1 InterviewEngine

```typescript
// src/interview/interview-engine.ts

export interface InterviewAnswers {
  scope: 'feature' | 'refactor' | 'bugfix' | 'optimization' | 'other';
  goals: string;
  relevantParts: string[];
  tddMode: 'tdd' | 'impl-first' | 'hybrid';
  followExistingPatterns: boolean;
  constraints: string;
  timeline: string;
}

export class InterviewEngine {
  async conduct(): Promise<InterviewAnswers> {
    const questions: inquirer.QuestionCollection = [
      // Question 1: Type of work
      {
        type: 'list',
        name: 'scope',
        message: 'What type of work are you doing?',
        choices: [
          { name: '✨ New feature', value: 'feature' },
          { name: '🔧 Refactoring existing code', value: 'refactor' },
          // ... etc
        ],
      },
      // Question 2: Goals
      {
        type: 'text',
        name: 'goals',
        message: 'Describe your goal in detail:',
      },
      // Question 3: Affected parts
      {
        type: 'checkbox',
        name: 'relevantParts',
        message: 'Which parts of the codebase are affected?',
        choices: this.suggestRelevantParts(),
      },
      // Question 4: TDD approach
      {
        type: 'list',
        name: 'tddMode',
        message: 'Development approach?',
        choices: [
          { name: '🧪 TDD - Write tests first', value: 'tdd' },
          { name: '⚙️ Implementation first', value: 'impl-first' },
          { name: '🔄 Hybrid', value: 'hybrid' },
        ],
      },
      // Question 5: Follow patterns
      {
        type: 'confirm',
        name: 'followExistingPatterns',
        message: `Follow existing ${this.analysis.patterns.codeStyle} patterns?`,
        default: true,
      },
      // Question 6: Constraints
      {
        type: 'text',
        name: 'constraints',
        message: 'Any constraints or requirements?',
      },
      // Question 7: Timeline
      {
        type: 'text',
        name: 'timeline',
        message: 'Expected timeline/scope?',
      },
    ];
    
    return inquirer.prompt(questions);
  }
}
```

### Deliverables:
- ✅ 7-question interview flow
- ✅ Dynamic suggestions based on project analysis
- ✅ All answers captured for devplan generation
- ✅ Natural, guided conversation feel

### Testing:
```bash
npm test -- src/interview/interview-engine.test.ts
```

---

## PHASE 3: Context-Aware DevPlan Generation (Day 5)

### What it does:
- Take analysis + interview answers + code samples
- Build comprehensive prompt for LLM
- Generate devplan that fits into existing codebase
- Output JSON ready for phase generation

### Key Files to Build:

#### 3.1 ExistingProjectDevPlanGenerator

```typescript
// src/interview/devplan-generator.ts

export class ExistingProjectDevPlanGenerator {
  async generate(): Promise<DevPlan> {
    const prompt = this.buildContextPrompt();
    
    const devplan = await this.llm.generateJSON<DevPlan>(prompt, {
      model: 'claude-3-5-sonnet',
      maxTokens: 8000,
    });
    
    return devplan;
  }
  
  private buildContextPrompt(): string {
    // Combine all analysis, samples, and answers into rich context
  }
}
```

#### 3.2 InterviewHandoffBuilder

```typescript
// src/interview/handoff-builder.ts

export class InterviewHandoffBuilder {
  buildHandoffPrompt(): string {
    // Create rich context for phase generation
  }
}
```

### Deliverables:
- ✅ DevPlan generation with full project context
- ✅ Integration points identified
- ✅ Risk factors noted
- ✅ Testing strategy defined
- ✅ Output ready for streaming UI

### Testing:
```bash
npm test -- src/interview/devplan-generator.test.ts
```

---

## PHASE 4: Terminal UI Core (Days 6-7)

### What it does:
- Create blessed screen with grid layout
- Initialize 5 phase boxes with status indicators
- Responsive layout based on terminal width
- Handle mouse clicks and keyboard input

### Key Files to Build:

#### 4.1 TerminalStreamer (Core)

```typescript
// src/terminal/terminal-streamer.ts

export class TerminalStreamer {
  private screen: blessed.Widgets.Screen;
  private phases: Map<string, PhaseStreamState> = new Map();
  private stateManager: PhaseStateManager;

  constructor() {
    this.screen = blessed.screen({
      mouse: true,
      keyboard: true,
      title: 'Devussy Phase Generation',
      smartCSR: true,
    });
    
    this.initializePhases();
  }
  
  private initializePhases(): void {
    const phaseNames = ['plan', 'design', 'implement', 'test', 'review'];
    const layout = this.calculateLayout();
    
    // Create 5 phase boxes with borders, scrolling, content
  }
  
  private calculateLayout(): Array<any> {
    // Responsive: 5 cols (250+), 2x3 grid (160-250), vertical (< 160)
  }
  
  private updatePhaseDisplay(phaseName: string): void {
    // Update box content, border color, status badge
  }
}
```

#### 4.2 PhaseStateManager

```typescript
// src/terminal/phase-state.ts

export interface PhaseStreamState {
  name: string;
  status: 'idle' | 'streaming' | 'complete' | 'interrupted' | 'steering' | 'regenerating' | 'error';
  content: string[];
  displayContent: string;
  outputBox: blessed.Widgets.BoxElement;
  
  // Steering context
  generationContext?: GenerationContext;
  cancelledAt?: CancellationInfo;
  steeringAnswers?: SteeringAnswers;
  abortController?: AbortController;
}

export class PhaseStateManager {
  initializePhase(name: string): PhaseStreamState { }
  updateStatus(name: string, status: string): void { }
  captureGenerationContext(name: string, prompt: string, apiRequest: any): void { }
  recordCancellation(name: string, output: string): void { }
  recordSteeringAnswers(name: string, answers: SteeringAnswers): void { }
  resetForRegeneration(name: string): void { }
}
```

### Deliverables:
- ✅ Blessed screen with grid of 5 phases
- ✅ Real-time status updates
- ✅ Color-coded borders (gray/blue/green/yellow/red)
- ✅ Responsive layout logic
- ✅ Mouse/keyboard interaction

### Testing:
```bash
npm test -- src/terminal/terminal-streamer.test.ts
```

---

## PHASE 5: Token Streaming (Day 8)

### What it does:
- Connect LLM streaming to each phase box
- Emit tokens in real-time as they arrive
- Update display every 10-20ms (debounced)
- Show last 15 lines in preview, full content available

### Key Files to Build:

#### 5.1 TerminalPhaseGenerator

```typescript
// src/phases/phase-generator-terminal.ts

export class TerminalPhaseGenerator {
  async generatePhaseWithStreaming(
    phaseName: string,
    devplan: any,
    callbacks: {
      onToken: (token: string) => void;
      onCancel?: () => void;
      signal: AbortSignal;
    }
  ): Promise<any> {
    // Build prompt and API request
    const apiRequest = { /* ... */ };
    
    // Capture context BEFORE streaming
    this.stateManager.captureGenerationContext(phaseName, prompt, apiRequest);
    
    // Stream from LLM
    for await (const chunk of stream) {
      if (callbacks.signal.aborted) {
        this.stateManager.recordCancellation(phaseName, fullContent);
        callbacks.onCancel?.();
        throw new Error('Generation cancelled by user');
      }
      
      const token = chunk.delta.text;
      fullContent += token;
      callbacks.onToken(token);
    }
  }
}
```

### Deliverables:
- ✅ Real-time token streaming from LLM
- ✅ AbortSignal support for cancellation
- ✅ Context capture before generation
- ✅ Token emission for UI updates

### Testing:
```bash
npm test -- src/phases/phase-generator-terminal.test.ts
```

---

## PHASE 6: Fullscreen Viewer (Day 9)

### What it does:
- Allow user to click on phase box to fullscreen
- Show full content with scrolling
- Vim-style navigation (j/k or arrow keys)
- Show character count at bottom
- ESC to return to grid

### Key Files to Build:

#### 6.1 Fullscreen Viewer

```typescript
// src/terminal/fullscreen-viewer.ts

private showFullscreenPhase(phaseName: string): void {
  const state = this.stateManager.getState(phaseName);
  
  // Clear screen and create fullscreen view
  this.phases.forEach(s => this.screen.remove(s.outputBox));
  
  // Header with title
  // Content box with scrolling
  // Footer with char count
  // ESC key to return to grid
}
```

### Deliverables:
- ✅ Fullscreen toggle for each phase
- ✅ Vim-style scrolling (j/k, arrows)
- ✅ Character count display
- ✅ Smooth return to grid view

### Testing:
```bash
npm test -- src/terminal/fullscreen-viewer.test.ts
```

---

## PHASE 7: Steering Workflow (Days 10-11)

### What it does:
- User presses 'C' during streaming to cancel
- Capture partial output + API request + original prompt
- Show overlay with steering interview questions:
  - "What's the issue?"
  - "What should it do instead?"
  - "Any constraints?"
- User submits answers
- Phase regenerates with steering context

### Key Files to Build:

#### 7.1 Steering Interview UI

```typescript
// src/terminal/steering-interview.ts

private showSteeringInterview(phaseName: string): void {
  // Create overlay form
  // Show partial output preview
  // 3 text input fields for questions
  // Regenerate and Cancel buttons
  // Handle form submission
}

private async handlePhaseCancel(phaseName: string): Promise<void> {
  const state = this.stateManager.getState(phaseName);
  state.abortController?.abort();
  
  this.stateManager.updateStatus(phaseName, 'interrupted');
  this.updatePhaseDisplay(phaseName);
  this.showSteeringInterview(phaseName);
}
```

#### 7.2 Steering + Regeneration

```typescript
// src/terminal/steering-orchestrator.ts

export class SteeringOrchestrator {
  async steerPhase(
    phaseName: string,
    devplan: any
  ): Promise<void> {
    const state = this.stateManager.getState(phaseName);
    
    // Record steering answers
    this.stateManager.recordSteeringAnswers(phaseName, answers);
    
    // Close steering box
    this.screen.remove(this.steeringBox);
    
    // Regenerate phase with context
    await this.regeneratePhase(phaseName, devplan);
  }
  
  private async regeneratePhase(
    phaseName: string,
    devplan: any
  ): Promise<void> {
    const controller = new AbortController();
    const state = this.stateManager.getState(phaseName);
    state.abortController = controller;
    
    await this.phaseGenerator.regeneratePhaseWithSteering(
      phaseName,
      devplan,
      {
        onToken: (token) => {
          state.content.push(token);
          this.updatePhaseDisplay(phaseName);
        },
        signal: controller.signal
      }
    );
  }
}
```

#### 7.3 Steering-Aware Phase Generator

```typescript
// src/phases/phase-generator-terminal.ts (addition)

async regeneratePhaseWithSteering(
  phaseName: string,
  devplan: any,
  callbacks: { onToken: (token: string) => void; signal: AbortSignal }
): Promise<any> {
  const state = this.stateManager.getState(phaseName);
  
  if (!state.generationContext || !state.steeringAnswers) {
    throw new Error('No steering context');
  }
  
  // Build steering prompt with context
  const steeringPrompt = this.buildSteeringPrompt(
    phaseName,
    state.generationContext.originalPrompt,
    state.cancelledAt!.partialOutput,
    state.steeringAnswers
  );
  
  // Regenerate with steering context
  const apiRequest = {
    ...state.generationContext.apiRequest,
    messages: [{ role: 'user', content: steeringPrompt }]
  };
  
  // Stream new generation
  for await (const chunk of stream) {
    if (callbacks.signal.aborted) break;
    const token = chunk.delta.text;
    fullContent += token;
    callbacks.onToken(token);
  }
}

private buildSteeringPrompt(
  phaseName: string,
  originalPrompt: string,
  partialOutput: string,
  answers: SteeringAnswers
): string {
  return `
You are regenerating the ${phaseName} phase based on user feedback.

## ORIGINAL TASK
${originalPrompt}

## WHAT WAS GENERATED (INCOMPLETE)
\`\`\`
${partialOutput.slice(0, 2000)}
\`\`\`

## USER FEEDBACK
Issue: ${answers.issue}
Desired Change: ${answers.desiredChange}
${answers.constraints ? `Constraints: ${answers.constraints}` : ''}

## YOUR TASK
Regenerate this phase addressing the user's feedback.
  `;
}
```

### Deliverables:
- ✅ Cancellation handler with 'C' key
- ✅ Steering interview overlay form
- ✅ 3-question feedback collection
- ✅ Context capture on cancellation
- ✅ Regeneration with steering context
- ✅ Live updates to UI as regeneration streams
- ✅ Non-blocking: Other phases continue

### Testing:
```bash
npm test -- src/terminal/steering-orchestrator.test.ts
```

---

## PHASE 8: Integration & CLI (Day 12)

### What it does:
- Wire all components together
- Create CLI commands
- Handle full workflow from interview to generation
- Connect error handling

### Key Files to Build:

#### 8.1 Interview Command

```typescript
// src/cli/commands/interview.ts

export const interviewCommand = new Command('interview')
  .description('Generate a devplan for an existing project')
  .argument('[directory]', 'Project directory', '.')
  .option('--output <path>', 'Output file for devplan')
  .action(async (directory, options) => {
    // Step 1: Analyze repository
    const analyzer = new RepositoryAnalyzer(directory);
    const analysis = await analyzer.analyze();
    
    // Step 2: Show project summary
    const interview = new InterviewEngine(analysis);
    interview.printProjectSummary();
    
    // Step 3: Conduct interview
    const answers = await interview.conduct();
    
    // Step 4: Extract code samples
    const extractor = new CodeSampleExtractor(directory);
    const codeSamples = await extractor.extractSamples(answers.relevantParts, analysis);
    
    // Step 5: Generate devplan
    const generator = new ExistingProjectDevPlanGenerator(
      llmProvider,
      analysis,
      codeSamples,
      answers
    );
    const devplan = await generator.generate();
    
    // Step 6: Save devplan
    const outputPath = options.output || 'devplan-interview.json';
    fs.writeFileSync(outputPath, JSON.stringify(devplan, null, 2));
    
    console.log(`✅ Devplan saved to ${outputPath}`);
    
    // Step 7: Ask to generate phases
    const startGeneration = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'proceed',
        message: 'Generate phases now?',
        default: false,
      }
    ]);
    
    if (startGeneration.proceed) {
      // Launch terminal streaming
      const orchestrator = new GenerationOrchestrator(devplan, llmProvider);
      await orchestrator.start();
    }
  });
```

#### 8.2 Generate Terminal Command

```typescript
// src/cli/commands/generate-terminal.ts

export const generateTerminalCommand = new Command('generate-terminal')
  .alias('gen-term')
  .description('Generate phases with terminal streaming UI')
  .argument('<devplan>', 'Path to devplan.json')
  .action(async (devplanPath) => {
    const devplan = JSON.parse(fs.readFileSync(devplanPath, 'utf-8'));
    
    console.log('🚀 Starting terminal streaming UI...\n');
    
    const orchestrator = new GenerationOrchestrator(devplan, llmProvider);
    await orchestrator.start();
  });
```

#### 8.3 Generation Orchestrator

```typescript
// src/terminal/generation-orchestrator.ts

export class GenerationOrchestrator {
  private stateManager: PhaseStateManager;
  private phaseGenerator: TerminalPhaseGenerator;
  private terminalStreamer: TerminalStreamerWithSteering;

  constructor(private devplan: any, private llmProvider: LLMProvider) {
    this.stateManager = new PhaseStateManager();
    this.phaseGenerator = new TerminalPhaseGenerator(
      this.stateManager,
      this.llmProvider
    );
    this.terminalStreamer = new TerminalStreamerWithSteering(
      this.stateManager,
      this.phaseGenerator
    );
  }

  async start(): Promise<void> {
    await this.terminalStreamer.generateAllPhases(this.devplan);
  }
}
```

### Deliverables:
- ✅ `devussy interview` command
- ✅ `devussy generate-terminal` command
- ✅ Full workflow integration
- ✅ Error handling throughout

---

## PHASE 9: Complete Terminal UI with Steering (Day 13)

### What it does:
- Combine all terminal features: streaming, fullscreen, steering
- Non-blocking steering while other phases continue
- Smooth UX with status updates

### Key Files to Build:

#### 9.1 TerminalStreamerWithSteering

```typescript
// src/terminal/terminal-streamer-steering.ts

export class TerminalStreamerWithSteering extends TerminalStreamer {
  private currentSteeringPhase: string | null = null;
  private steeringBox: blessed.Widgets.BoxElement | null = null;
  private steeringOrchestrator: SteeringOrchestrator;

  async generateAllPhases(devplan: any): Promise<void> {
    const phaseNames = ['plan', 'design', 'implement', 'test', 'review'];

    const promises = phaseNames.map(name => {
      const controller = new AbortController();
      const state = this.stateManager.getState(name);
      state.abortController = controller;

      return this.phaseGenerator.generatePhaseWithStreaming(
        name,
        devplan,
        {
          onToken: (token) => {
            const state = this.stateManager.getState(name);
            state.content.push(token);
            this.updatePhaseDisplay(name);
          },
          onCancel: () => {
            this.updatePhaseDisplay(name);
          },
          signal: controller.signal
        }
      ).catch(error => {
        if (error.message === 'Generation cancelled by user') {
          return null; // Expected - user cancelled via steering
        }
        throw error;
      });
    });

    await Promise.allSettled(promises);
  }

  private async handlePhaseCancel(phaseName: string): Promise<void> {
    const state = this.stateManager.getState(phaseName);
    
    if (state.abortController) {
      state.abortController.abort();
    }

    this.stateManager.updateStatus(phaseName, 'interrupted');
    this.updatePhaseDisplay(phaseName);
    this.showSteeringInterview(phaseName);
  }

  private showSteeringInterview(phaseName: string): void {
    // Full steering interview implementation
    // (See devussy-terminal-steering.md for complete code)
  }

  private async regeneratePhase(phaseName: string): Promise<void> {
    // Full regeneration implementation
    // (See devussy-terminal-steering.md for complete code)
  }
}
```

### Deliverables:
- ✅ Full terminal UI with all features
- ✅ Streaming + fullscreen + steering working together
- ✅ Non-blocking cancellation & regeneration
- ✅ Smooth UX with status indicators

---

## PHASE 10: Testing & Polish (Day 14)

### What it does:
- Write comprehensive tests
- Test all features on real projects
- Improve error handling and edge cases
- Add documentation and help text

### Tests to Write:

```typescript
// tests/interview/repository-analyzer.test.ts
- Test detection of 5+ project types
- Test dependency parsing
- Test code metrics calculation
- Test pattern detection

// tests/interview/interview-engine.test.ts
- Test all 7 questions
- Test answer validation
- Test suggestion generation

// tests/interview/devplan-generator.test.ts
- Test prompt building
- Test devplan generation
- Test context integration

// tests/terminal/terminal-streamer.test.ts
- Test grid layout responsiveness
- Test phase initialization
- Test status updates

// tests/terminal/steering-orchestrator.test.ts
- Test cancellation flow
- Test steering interview
- Test regeneration
- Test non-blocking behavior

// tests/integration/full-workflow.test.ts
- Test interview → generation workflow
- Test cancel → steer → regenerate flow
- Test with real LLM
```

### Deliverables:
- ✅ 80%+ test coverage
- ✅ Integration tests passing
- ✅ Real project testing
- ✅ Error handling for edge cases
- ✅ Performance optimized

---

## PHASE 11: Documentation & Help (Day 15)

### What it does:
- Add help text and keyboard shortcuts
- Document all CLI commands
- Create user guide
- Add troubleshooting

### Key Files to Build:

#### 11.1 In-App Help

```typescript
// src/terminal/help.ts

export function showHelp(): void {
  const helpContent = `
{bold}{cyan}Devussy Terminal Streaming UI Help{/cyan}{/bold}

{bold}Interview Mode:{/bold}
  devussy interview /path/to/project
  → Analyzes your existing codebase
  → Asks 7 questions about your goals
  → Generates tailored devplan

{bold}Generation Mode:{/bold}
  devussy generate-terminal devplan.json
  → Shows 5 concurrent phases streaming
  → Press C on any phase to cancel & steer
  → Answer steering questions to regenerate

{bold}Keyboard Shortcuts:{/bold}
  • C - Cancel current phase (while streaming)
  • ESC - Close fullscreen view
  • TAB - Move between form fields
  • ENTER - Submit form / Regenerate
  • ? - Show this help
  • Q - Quit

{bold}Status Colors:{/bold}
  • {blue}Blue{/blue} - Streaming in progress
  • {green}Green{/green} - Phase completed
  • {yellow}Yellow{/yellow} - Interrupted/Steering
  • {red}Red{/red} - Error occurred
  • {gray}Gray{/gray} - Idle/Not started
  `;
}
```

### Deliverables:
- ✅ In-app help system
- ✅ CLI command documentation
- ✅ User guide
- ✅ Troubleshooting guide

---

## File Structure

```
src/
├── cli/
│   ├── commands/
│   │   ├── interview.ts                    ← Interview command
│   │   ├── generate-terminal.ts             ← Generate command
│   │   └── index.ts
│   └── index.ts
├── interview/
│   ├── repository-analyzer.ts              ← Analyze existing projects
│   ├── code-sample-extractor.ts            ← Extract code samples
│   ├── interview-engine.ts                 ← 7-question interview
│   ├── devplan-generator.ts                ← Generate devplan
│   ├── handoff-builder.ts                  ← Context for phases
│   └── index.ts
├── phases/
│   ├── phase-generator-terminal.ts         ← Streaming + steering
│   └── index.ts
└── terminal/
    ├── terminal-streamer.ts                ← Core UI
    ├── terminal-streamer-steering.ts       ← Add steering
    ├── phase-state.ts                      ← State management
    ├── fullscreen-viewer.ts                ← Fullscreen logic
    ├── steering-orchestrator.ts            ← Steering workflow
    ├── generation-orchestrator.ts          ← Orchestration
    ├── help.ts                             ← Help system
    └── index.ts

tests/
├── interview/
│   ├── repository-analyzer.test.ts
│   ├── interview-engine.test.ts
│   └── devplan-generator.test.ts
├── terminal/
│   ├── terminal-streamer.test.ts
│   ├── steering-orchestrator.test.ts
│   └── fullscreen-viewer.test.ts
└── integration/
    └── full-workflow.test.ts
```

---

## Complete User Journey

### Step 1: Interview Mode
```bash
$ devussy interview /home/user/my-project

🔍 Analyzing /home/user/my-project...

📊 Project Summary:
  Project Type: Node.js
  Main Language: TypeScript
  Complexity: moderate
  Test Framework: jest
  Build Tool: tsc
  Architecture: single

🎯 Let's understand your project and goals

? What type of work are you doing?
  ✨ New feature
  
? Describe your goal in detail:
  Add user authentication with OAuth2

? Which parts of the codebase are affected?
  ❯◉ src
   ◉ services
   ◉ utils
   
? Development approach?
  ✅ TDD - Write tests first

? Follow existing TypeScript patterns?
  ✅ Yes

? Any constraints?
  Must be backward compatible

? Expected timeline?
  1-2 days

✅ Devplan generated and saved to devplan-interview.json

? Generate phases now?
  ❯ Yes
  
🚀 Starting terminal streaming UI...
```

### Step 2: Streaming UI with Steering
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│   PLAN (blue)   │  DESIGN (blue)  │ IMPLEMENT (blue)│   TEST (blue)   │  REVIEW (gray)  │
│ ▊ streaming     │ ▊ streaming     │ ▊ streaming     │ ▊ streaming     │ (idle)          │
│ Phase 1 output  │ Phase 2 output  │ Phase 3 output  │ Phase 4 output  │                 │
│ streaming here  │ streaming here  │ streaming here  │ streaming here  │                 │
│ ...             │ ...             │ ...             │ ...             │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┘

User sees IMPLEMENT phase is missing error handling → Presses C

┌───────────────────────────────────────────────────────────────────────────────────┐
│                      🟡 STEERING INTERVIEW: IMPLEMENT 🟡                         │
│                                                                                   │
│  Partial Output (1,234 tokens)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │ The implementation covers the basic OAuth2 flow...                         │ │
│  │ However, it doesn't include error handling for edge cases...               │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  1. What's the issue?                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │ Missing error handling for failed OAuth2 responses                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  2. What should it do instead?                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │ Add try-catch blocks and proper error logging for OAuth2 failures,        │ │
│  │ invalid tokens, and network errors                                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  3. Any constraints?                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │ Follow existing error handling patterns in the codebase                    │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│                {GREEN}Regenerate Phase{/GREEN}                 {RED}Cancel{/RED}              │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘

User submits steering answers

┌─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│   PLAN (green)  │  DESIGN (green) │ IMPLEMENT (blue)│   TEST (blue)   │  REVIEW (blue)  │
│ ✓ complete      │ ✓ complete      │ ▊ regenerating  │ ▊ streaming     │ ▊ streaming     │
│                 │                 │ NEW output with │ Phase 4 output  │ Phase 5 output  │
│                 │                 │ error handling  │ streaming here  │ streaming here  │
│                 │                 │ included        │ ...             │ ...             │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┘

All phases complete!

✅ All phases generated!
📁 Output saved to ./phases/

What's next?
  • Review output in fullscreen (press EXPAND on any phase)
  • Make another change (ESC and repeat)
  • Export to handoff document
```

---

## Implementation Timeline

| Phase | Days | Deliverables |
|-------|------|--------------|
| 1 | 1-2 | Repository analysis engine |
| 2 | 3-4 | Interview engine (7 questions) |
| 3 | 5 | Context-aware devplan generation |
| 4 | 6-7 | Terminal UI core (grid + streaming) |
| 5 | 8 | Token streaming integration |
| 6 | 9 | Fullscreen viewer |
| 7 | 10-11 | Steering workflow (cancel → interview → regenerate) |
| 8 | 12 | CLI integration & commands |
| 9 | 13 | Full terminal UI with steering |
| 10 | 14 | Testing & optimization |
| 11 | 15 | Documentation & polish |

**Total: ~15 days of focused development**

---

## Success Criteria

✅ **Interview Mode**
- [ ] Can analyze any project directory
- [ ] Detects project type, dependencies, patterns
- [ ] 7-question interview flows naturally
- [ ] Generated devplans fit existing code
- [ ] Works with Node, Python, Go, Rust, Java

✅ **Terminal Streaming UI**
- [ ] All 5 phases stream tokens in parallel
- [ ] Real-time status updates
- [ ] Color-coded borders by status
- [ ] Responsive layout (5 cols → 2x3 → vertical)
- [ ] No performance degradation

✅ **Fullscreen Viewer**
- [ ] Click to fullscreen any phase
- [ ] Scroll with vim keys or arrows
- [ ] Character count shown
- [ ] ESC returns to grid

✅ **Steering Workflow**
- [ ] Press 'C' to cancel mid-generation
- [ ] Steering interview appears
- [ ] Partial output shown for context
- [ ] 3 questions + regenerate/cancel buttons
- [ ] Other 4 phases continue uninterrupted
- [ ] Regenerated output replaces cancelled content
- [ ] Full context (original prompt + API request + feedback) sent to LLM

✅ **Integration**
- [ ] `devussy interview` command works end-to-end
- [ ] `devussy generate-terminal` works with interview output
- [ ] Smooth workflow: interview → generation
- [ ] Error handling throughout
- [ ] Help system and keyboard shortcuts

---

## Key Technical Decisions

1. **Blessed over Ink**: Better performance for high-frequency token updates
2. **Terminal-only**: No web server overhead, perfect for dev workflow
3. **Non-blocking steering**: Other phases continue while one is steered
4. **Context capture**: Full API request + original prompt sent on regeneration
5. **Responsive layout**: Adapts to terminal width automatically

This is a complete, production-ready plan combining interview mode + streaming UI + steering workflow all in the terminal!