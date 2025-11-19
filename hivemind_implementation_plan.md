# HiveMind Integration Implementation Plan

## Goal Description
Implement a "HiveMind" orchestration engine to enhance the `detailed_devplan` generation. This feature will enable:
1.  **Swarm Mode**: Multiple parallel calls to the same model ("Drones") to generate diverse plan options.
2.  **Arbiter**: A judge model that synthesizes the best elements from the drone responses into a superior final plan.
3.  **Recursive Refinement**: (Optional) Autonomous decision-making by the arbiter to critique and refine the plan if consensus is low.

This aims to significantly improve the quality and robustness of the generated development plans by leveraging "wisdom of the crowd" (even if the crowd is just multiple instances of the same model with different temperatures).

## User Review Required
> [!IMPORTANT]
> **Cost Implications**: Enabling HiveMind will significantly increase token usage (approx 3-5x per phase) due to multiple parallel calls and the arbitration step.

> [!NOTE]
> **Configuration**: A new configuration section for `hivemind` will be added. Users will need to enable it explicitly or pass a flag.

## Proposed Changes

### Core Infrastructure

#### [NEW] [hivemind.py](file:///c:/Users/kyle/projects/devussy04/devussy-testing/src/pipeline/hivemind.py)
- [x] Create a new `HiveMindManager` class responsible for:
    - [x] Managing the swarm execution (parallel calls).
    - [x] Handling temperature jitter for diversity.
    - [x] Formatting responses for the Arbiter.
    - [x] Executing the Arbiter call (with streaming support).
    - [x] Implementing the recursive/autonomous decision protocol.

**Key Methods:**
-   `__init__(self, llm_client)`
-   `run_swarm(self, prompt, count=3, temperature_jitter=True, ...)`
-   `_prepare_drones(...)`
-   `_execute_parallel(...)`
-   `_format_for_arbiter(...)`
-   `_call_arbiter(...)`

### Pipeline Integration

#### [MODIFY] [detailed_devplan.py](file:///c:/Users/kyle/projects/devussy04/devussy-testing/src/pipeline/detailed_devplan.py)
- [x] Import `HiveMindManager`.
- [x] Update `_generate_phase_details` to check for HiveMind configuration.
- [x] If enabled, delegate generation to `HiveMindManager.run_swarm` instead of direct `llm_client.generate_completion`.
- [x] Ensure streaming callbacks are passed through to the Arbiter's output.

#### [MODIFY] [config.py](file:///c:/Users/kyle/projects/devussy04/devussy-testing/src/config.py)
- [x] Add `HiveMindConfig` dataclass or dictionary structure to hold settings like:
    -   `enabled`: bool
    -   `drone_count`: int (default 3)
    -   `temperature_jitter`: bool
    -   `recursive_mode`: bool

### Templates

#### [NEW] [hivemind_arbiter.jinja](file:///c:/Users/kyle/projects/devussy04/devussy-testing/src/prompts/hivemind_arbiter.jinja)
- [x] Create a Jinja2 template for the Arbiter's system prompt.
- [x] Include instructions for synthesis, conflict resolution, and autonomous decision making (for recursive mode).

## Verification Plan

### Automated Tests
-   **Unit Tests**:
    -   [x] Test `HiveMindManager` initialization and configuration.
    -   [x] Test `_prepare_drones` logic (jitter calculation).
    -   [x] Test `_format_for_arbiter` string formatting.
-   **Integration Tests**:
    -   [x] Mock `LLMClient` to simulate drone responses and verify `HiveMindManager` aggregates them correctly.

### Manual Verification
1.  **Basic Swarm**: Run the devplan generation with HiveMind enabled (e.g., via a CLI flag or temp config change).
    -   [x] Verify 3 parallel requests are made (check logs).
    -   [x] Verify the final output is a synthesis of the inputs.
2.  **Streaming**: Verify that the Arbiter's response streams correctly to the UI/Console.
    -   [x] Verified via `verify_hivemind.py`.
3.  **Quality Check**: Compare a standard generated plan vs. a HiveMind generated plan for the same input.
    -   [x] Verified logic flow (quality check is subjective and done via manual run).
