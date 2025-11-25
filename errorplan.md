# Error Plan – Test Failures

_Last updated from `pytest tests/unit tests/integration` on 2025-11-24._

Summary from latest run:

- **Status**: 41 failed, 440 passed, 1 skipped
- **Command**: `python -m pytest tests/unit tests/integration`

> Note: Several failures share the same root cause (e.g. stricter `AppConfig` validation); those are grouped below. Where pytest output was truncated, tests are described by class/category.

---

## 1. Config loading (`tests/unit/test_config.py`)

All failing tests here raise:

- **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`

Known failing tests:

- **tests/unit/test_config.py::TestLoadConfig::test_config_path_from_env**  
  Error: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **tests/unit/test_config.py::TestLoadConfig::test_empty_config_file**  
  Error: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **tests/unit/test_config.py::TestLoadConfig::test_boolean_string_conversion**  
  Error: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **tests/unit/test_config.py::TestLoadConfig::test_path_conversion**  
  Error: `ValueError: Invalid configuration: 1 validation error for AppConfig`

(Additional `TestLoadConfig` tests may also be failing with the same `AppConfig` validation error.)

---

## 2. Documentation indexing (`tests/unit/test_documentation.py`)

- **tests/unit/test_documentation.py::TestDocumentationIndexer::test_generate_index_with_documents**  
  **Error**: `AssertionError: assert '[LIST] Project Design Documents' in '# Documen...'`

---

## 3. LLM clients (`tests/unit/test_llm_clients.py`)

- **tests/unit/test_llm_clients.py::TestOpenAIClient::test_generate_completion_success**  
  **Error**: `AssertionError: expected call not found.`

---

## 4. Project design generator (`TestProjectDesignGenerator`)

All of these stem from the same change in `ProjectDesignGenerator` (now async and/or returning a coroutine that tests treat as an iterable string).

- **tests/unit/test_pipeline_generators.py::TestProjectDesignGenerator::test_generate_basic_design**  
  **Error**: `TypeError: 'coroutine' object is not iterable`
- **...::test_generate_with_optional_params**  
  **Error**: `TypeError: 'coroutine' object is not iterable`
- **...::test_parse_response_with_valid_markdown**  
  **Error**: `TypeError: 'coroutine' object is not iterable`
- **...::test_parse_response_with_empty_sections**  
  **Error**: `TypeError: 'coroutine' object is not iterable`
- **...::test_generate_with_llm_kwargs**  
  **Error**: `TypeError: 'coroutine' object is not iterable`
- **...::test_generate_handles_llm_error**  
  **Error**: `AssertionError: Regex pattern did not match.`

---

## 5. Basic DevPlan generator (`TestBasicDevPlanGenerator`)

These tests are now hitting a mocked streaming handler / file writer that receives an `AsyncMock` instead of a plain string.

- **tests/unit/test_pipeline_generators.py::TestBasicDevPlanGenerator::test_generate_basic_devplan**  
  **Error**: `TypeError: write() argument must be str, not AsyncMock`
- **...::test_generate_with_feedback_manager**  
  **Error**: `TypeError: write() argument must be str, not AsyncMock`
- **...::test_parse_response_various_formats**  
  **Error**: `TypeError: write() argument must be str, not AsyncMock`
- **...::test_parse_response_no_phases**  
  **Error**: `TypeError: write() argument must be str, not AsyncMock`
- **...::test_generate_with_llm_kwargs**  
  **Error**: `TypeError: write() argument must be str, not AsyncMock`

---

## 6. Detailed DevPlan generator (`TestDetailedDevPlanGenerator`)

All these tests are failing due to `AppConfig` validation when constructing the detailed devplan generator / config.

- **tests/unit/test_pipeline_generators.py::TestDetailedDevPlanGenerator::test_generate_detailed_devplan**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **...::test_generate_multiple_phases**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **...::test_generate_with_tech_stack**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **...::test_generate_with_feedback_manager**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **...::test_parse_steps_various_formats**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **...::test_parse_steps_no_steps_found**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`
- **...::test_concurrent_execution**  
  **Error**: `ValueError: Invalid configuration: 1 validation error for AppConfig`

---

## 7. Event bus contracts (`tests/integration/test_event_bus_notifications.py`)

- **tests/integration/test_event_bus_notifications.py::TestEventBusContracts::test_all_typed_events_have_emit_or_subscribe_sites**  
  **Error**: `AssertionError: assert 'interviewCompleted' in ['planGenerated', 'proj...']`

Indicates that the `EventBus` typed events include `interviewCompleted`, but the scan of emit/subscribe sites did not find that event wired up.

---

## 8. Interactive CLI integration (`tests/integration/test_interactive_command_integration.py`)

These all come from changes in `src.cli` and its interactive command wiring.

- **tests/integration/test_interactive_command_integration.py::TestInteractiveCommandWorkflow::test_complete_workflow_after_interview**  
  **Error**: `AttributeError` on `src.cli` (module no longer exposing expected attributes used by the test).
- **...::TestInteractiveCommandWorkflow::test_interactive_workflow_sequence**  
  **Error**: `AttributeError` on `src.cli`.
- **...::TestInteractiveCommandErrorHandling::test_handles_interview_failure**  
  **Error**: `AttributeError` on `src.cli`.

---

## 9. Share links flow (`tests/integration/test_share_links_flow.py`)

All three tests hit the same underlying problem – expected sample files/paths are missing.

- **tests/integration/test_share_links_flow.py::TestShareLinksRoundTrip::test_generate_and_decode_share_link_roundtrip_design**  
  **Error**: `FileNotFoundError: [WinError 2] The system cannot find the file specified`
- **...::test_decode_invalid_payload_returns_null**  
  **Error**: `FileNotFoundError: [WinError 2] The system cannot find the file specified`
- **...::test_decode_payload_missing_stage_returns_null**  
  **Error**: `FileNotFoundError: [WinError 2] The system cannot find the file specified`

---

## 10. UI preferences integration (`tests/integration/test_ui_preferences_integration.py`)

These tests assume a preferences file path and certain merge semantics.

- **tests/integration/test_ui_preferences_integration.py::TestUIPreferencesPersistence::test_preference_saving**  
  **Error**: `AssertionError: Preferences file should be created`
- **...::TestUIPreferencesPersistence::test_menu_merge_logic**  
  **Error**: `AssertionError: assert False == True`
- **...::TestUIPreferencesBugReproduction::test_full_user_scenario**  
  **Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\kyle\\...'`
- **...::TestUIPreferencesEdgeCases::test_partial_preferences**  
  **Error**: `AssertionError: assert 'full_scenario_provider' == 'partial_provider'`

---

## 11. Window manager registry (`tests/integration/test_window_manager_registry.py`)

- **tests/integration/test_window_manager_registry.py::TestWindowManagerRegistryInvariants::test_app_registry_includes_expected_apps**  
  **Error**: `AssertionError: Expected app id 'model-settings' to appear in AppRegistry...`

---

## 12. Next steps (high level)

- **Config/AppConfig**: Decide whether tests or `AppConfig` validation should change (e.g. default values for missing fields vs. hard failures).
- **Pipeline generators**: Align tests with new async/streaming behavior (`ProjectDesignGenerator`, `BasicDevPlanGenerator`, `DetailedDevPlanGenerator`).
- **Interactive CLI & EventBus**: Update tests to the new CLI entry points and ensure `interviewCompleted` (and other events) are wired up in `EventBus`.
- **Share links & UI prefs**: Provide stable test fixtures/paths for share-link files and preferences storage.
- **AppRegistry**: Ensure `model-settings` app id is present or tests are updated to the new registry contents.
