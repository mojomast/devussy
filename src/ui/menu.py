from __future__ import annotations

from typing import Any, Optional, Dict, Tuple
import sys
import os
import asyncio
import getpass

from pydantic import BaseModel, Field
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import (
    radiolist_dialog,
    yes_no_dialog,
    input_dialog,
    message_dialog,
)

from ..config import AppConfig, LLMConfig
from ..state_manager import StateManager
from ..logger import get_logger
import subprocess
import sys
from pathlib import Path

logger = get_logger(__name__)


class SessionSettings(BaseModel):
    provider: Optional[str] = None
    interview_model: Optional[str] = None
    final_stage_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    streaming: Optional[bool] = None  # Global streaming flag (backward compatibility)
    # Phase-specific streaming options
    streaming_design_enabled: Optional[bool] = None
    streaming_devplan_enabled: Optional[bool] = None
    streaming_handoff_enabled: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # Primarily used for generic provider endpoint
    # Always treat these as dicts at runtime to avoid Optional/None typing issues in callers.
    provider_keys: Dict[str, str] = Field(default_factory=dict)
    provider_base_urls: Dict[str, str] = Field(default_factory=dict)
    # GPT-5 reasoning level: low | medium | high
    reasoning_effort: Optional[str] = None
    last_token_usage: Optional[Dict[str, int]] = Field(default=None)
    # Timeouts (seconds)
    api_timeout: Optional[int] = None
    design_api_timeout: Optional[int] = None
    devplan_api_timeout: Optional[int] = None
    handoff_api_timeout: Optional[int] = None
    # Concurrency
    max_concurrent_requests: Optional[int] = None
    
    # Experimental Features (Development Sandbox)
    debug_ui_mode: Optional[bool] = False
    experimental_single_window: Optional[bool] = False
    color_theme_tester: Optional[bool] = False
    responsive_layout: Optional[bool] = False
    # Start as None so merge logic can distinguish "unset" from
    # "explicitly disabled"; prefer False when loading persisted prefs.
    repository_tools_enabled: Optional[bool] = None
    
    # Development & Testing Tools
    mock_api_mode: Optional[bool] = False
    api_response_logger: Optional[bool] = False
    performance_profiler: Optional[bool] = False
    token_usage_tracker: Optional[bool] = False
    
    # Pipeline Experimental Modes
    experimental_pipeline: Optional[bool] = False
    batch_generation_mode: Optional[bool] = False
    enhanced_error_recovery: Optional[bool] = False
    parallel_generation: Optional[bool] = False
    
    # Prototype Features
    ai_code_review: Optional[bool] = False
    smart_recommendations: Optional[bool] = False
    auto_documentation: Optional[bool] = False
    cross_reference_analysis: Optional[bool] = False


def get_design_streaming_status(config, session: Optional[SessionSettings]) -> bool:
    """Determine if streaming is enabled for the Design phase.
    
    Priority:
    1. session.streaming_design_enabled (if explicitly set)
    2. session.streaming (global fallback)
    3. config.streaming_enabled (config fallback)
    4. False (default)
    """
    if session and session.streaming_design_enabled is not None:
        return session.streaming_design_enabled
    elif session and session.streaming is not None:
        return session.streaming
    else:
        return getattr(config, 'streaming_enabled', False)


def get_devplan_streaming_status(config, session: Optional[SessionSettings]) -> bool:
    """Determine if streaming is enabled for the DevPlan phase.
    
    Priority:
    1. session.streaming_devplan_enabled (if explicitly set)
    2. session.streaming (global fallback)
    3. config.streaming_enabled (config fallback)
    4. False (default)
    """
    if session and session.streaming_devplan_enabled is not None:
        return session.streaming_devplan_enabled
    elif session and session.streaming is not None:
        return session.streaming
    else:
        return getattr(config, 'streaming_enabled', False)


def get_handoff_streaming_status(config, session: Optional[SessionSettings]) -> bool:
    """Determine if streaming is enabled for the Handoff phase.
    
    Priority:
    1. session.streaming_handoff_enabled (if explicitly set)
    2. session.streaming (global fallback)
    3. config.streaming_enabled (config fallback)
    4. False (default)
    """
    if session and session.streaming_handoff_enabled is not None:
        return session.streaming_handoff_enabled
    elif session and session.streaming is not None:
        return session.streaming
    else:
        return getattr(config, 'streaming_enabled', False)


def _is_tty() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _current_settings_snapshot(config: AppConfig, session: Optional[SessionSettings]) -> str:
    # Prefer session-scoped provider if set; this is what interactive settings modifies first.
    # This ensures the Settings UI and in-memory config both reflect the live provider choice.
    active_provider = (session.provider if session and session.provider else config.llm.provider)
    llm = config.llm
    lines = [
        f"Provider: {active_provider}",
        f"Interview Model: {(session.interview_model if session and session.interview_model else llm.model)}",
        f"Final Stage Model: {(session.final_stage_model if session and session.final_stage_model else (config.devplan_llm.model if config.devplan_llm else llm.model))}",
        f"Temperature: {session.temperature if session and session.temperature is not None else llm.temperature}",
        f"Max Tokens: {session.max_tokens if session and session.max_tokens is not None else llm.max_tokens}",
        f"Reasoning (gpt-5): {(session.reasoning_effort if session and session.reasoning_effort else getattr(llm, 'reasoning_effort', None) or '-')}",
        f"Global Streaming: {session.streaming if session and session.streaming is not None else getattr(config, 'streaming_enabled', False)}",
        f"Design Streaming: {get_design_streaming_status(config, session)}",
        f"DevPlan Streaming: {get_devplan_streaming_status(config, session)}",
        f"Handoff Streaming: {get_handoff_streaming_status(config, session)}",
        f"API Timeout: {session.api_timeout if session and session.api_timeout is not None else llm.api_timeout}s",
        f"Design Timeout: {(session.design_api_timeout if session and session.design_api_timeout is not None else (config.design_llm.api_timeout if config.design_llm and getattr(config.design_llm, 'api_timeout', None) is not None else '-'))}s",
        f"DevPlan Timeout: {(session.devplan_api_timeout if session and session.devplan_api_timeout is not None else (config.devplan_llm.api_timeout if config.devplan_llm and getattr(config.devplan_llm, 'api_timeout', None) is not None else '-'))}s",
        f"Handoff Timeout: {(session.handoff_api_timeout if session and session.handoff_api_timeout is not None else (config.handoff_llm.api_timeout if config.handoff_llm and getattr(config.handoff_llm, 'api_timeout', None) is not None else '-'))}s",
        f"Max Concurrent Requests: {session.max_concurrent_requests if session and session.max_concurrent_requests is not None else getattr(config, 'max_concurrent_requests', 5)}",
        f"API Key: {'set' if (session and session.api_key) or llm.api_key else 'not set'}",
        f"Base URL: {(session.base_url if session and session.base_url else llm.base_url) or 'default'}",
    ]
    if session and session.last_token_usage:
        usage = session.last_token_usage
        lines.append(
            f"Last Token Usage -> prompt: {usage.get('prompt_tokens')}, completion: {usage.get('completion_tokens')}, total: {usage.get('total_tokens')}"
        )
    return "\n".join(lines)


def _load_prefs() -> SessionSettings:
    try:
        sm = StateManager()
        data = sm.load_state("ui_prefs") or {}
        logger.debug(f"_load_prefs: Loaded data from state: {data}")
        result = SessionSettings(**data)
        # Backwards compatibility: if repository_tools_enabled was not
        # present in stored prefs, ensure it defaults to False rather than
        # None so callers can rely on a concrete boolean value.
        if getattr(result, "repository_tools_enabled", None) is None:
            result.repository_tools_enabled = False
        logger.debug(
            "_load_prefs: Created SessionSettings with repository_tools_enabled: "
            f"{getattr(result, 'repository_tools_enabled', 'NOT_SET')}"
        )
        return result
    except Exception as e:
        logger.debug(f"_load_prefs: Exception occurred: {e}")
        return SessionSettings()


def _save_prefs(session: SessionSettings) -> None:
    try:
        sm = StateManager()
        sm.save_state("ui_prefs", session.model_dump())
    except Exception:
        pass


def load_last_used_preferences() -> SessionSettings:
    """Public helper to load last-used UI/session preferences."""
    return _load_prefs()


def _submenu_models(config: AppConfig, session: SessionSettings) -> None:
    """Nested menu for provider and model selection."""
    if _is_tty():
        while True:
            pick = (
                radiolist_dialog(
                    title="Models & Provider",
                    text=_current_settings_snapshot(config, session),
                    values=[
                        ("provider", "Provider"),
                        ("api_key_current", "API Key (active provider)"),
                        ("base_url_current", "Base URL (active provider)"),
                        ("interview_model", "Interview Model"),
                        ("final_stage_model", "Final Stage Model"),
                        ("back", "Save and Return"),
                    ],
                ).run()
                or "back"
            )
            if pick == "provider":
                provider_default = (session.provider or config.llm.provider or "openai").lower()
                provider = (
                    radiolist_dialog(
                        title="Provider",
                        text="Select active provider",
                        values=[
                            ("openai", "OpenAI"),
                            ("generic", "Generic (OpenAI-compatible)"),
                            ("aether", "Aether AI"),
                            ("agentrouter", "AgentRouter"),
                            ("requesty", "Requesty"),
                        ],
                    ).run()
                    or provider_default
                )
                session.provider = provider

                # Prompt for API key for this provider if missing
                if not (session.provider_keys or {}).get(provider):
                    try:
                        try:
                            api_key_input = input_dialog(
                                title=f"{provider.capitalize()} API Key",
                                text="Enter API key (leave blank to skip, '-' to clear):",
                                password=True,
                            ).run()
                        except TypeError:
                            api_key_input = prompt("Enter API key (leave blank to skip, '-' to clear): ", is_password=True)
                        if api_key_input is not None:
                            api_key_input = api_key_input.strip()
                            if api_key_input == "-":
                                session.provider_keys.pop(provider, None)
                            elif api_key_input:
                                session.provider_keys[provider] = api_key_input
                                session.api_key = api_key_input
                    except Exception:
                        pass
                
                # If generic provider selected and no base URL is set, prompt for it
                if provider == "generic" and not session.provider_base_urls.get(provider) and not config.llm.base_url:
                    try:
                        base_url_input = input_dialog(
                            title="Base URL Required",
                            text="Generic provider requires a base URL (e.g., https://api.example.com):",
                        ).run()
                        if base_url_input and base_url_input.strip():
                            session.provider_base_urls[provider] = base_url_input.strip()
                    except Exception:
                        pass
                # For Aether/AgentRouter, auto-populate defaults silently if missing
                if provider == "aether" and not session.provider_base_urls.get(provider):
                    session.provider_base_urls[provider] = "https://api.aetherapi.dev"
                if provider == "agentrouter" and not session.provider_base_urls.get(provider):
                    session.provider_base_urls[provider] = "https://agentrouter.org/"
                
                continue
            if pick == "api_key_current":
                try:
                    active_provider = (session.provider or config.llm.provider or "openai").lower()
                    try:
                        api_key_input = input_dialog(
                            title=f"{active_provider.capitalize()} API Key",
                            text="Enter API key (leave blank to keep current, '-' to clear):",
                            password=True,
                        ).run()
                    except TypeError:
                        api_key_input = prompt("Enter API key (leave blank to keep current, '-' to clear): ", is_password=True)
                    if api_key_input is not None:
                        api_key_input = api_key_input.strip()
                        if api_key_input == "-":
                            session.provider_keys.pop(active_provider, None)
                        elif api_key_input:
                            session.provider_keys[active_provider] = api_key_input
                            session.api_key = api_key_input
                except Exception:
                    pass
                continue
            if pick == "base_url_current":
                try:
                    active_provider = (session.provider or config.llm.provider or "openai").lower()
                    base_url_input = input_dialog(
                        title="Base URL",
                        text=f"Enter base URL for current provider '{active_provider}' (leave blank to keep current, '-' to clear):",
                    ).run()
                    if base_url_input is not None:
                        base_url_input = base_url_input.strip()
                        if base_url_input == "-":
                            session.provider_base_urls.pop(active_provider, None)
                        elif base_url_input:
                            session.provider_base_urls[active_provider] = base_url_input
                except Exception:
                    pass
                continue
            if pick == "interview_model":
                selected = _combined_model_picker(
                    config,
                    session,
                    title="Interview Model",
                    current=session.interview_model or config.llm.model,
                )
                if selected:
                    session.interview_model = selected.strip()
                continue
            if pick == "final_stage_model":
                selected = _combined_model_picker(
                    config,
                    session,
                    title="Final Stage Model",
                    current=session.final_stage_model or (config.devplan_llm.model if config.devplan_llm else config.llm.model),
                )
                if selected:
                    session.final_stage_model = selected.strip()
                continue
            if pick == "back":
                return
    else:
        while True:
            print("\n=== Models & Provider ===")
            print("  1) Provider")
            print("  2) API Key (active provider)")
            print("  3) Base URL (active provider)")
            print("  4) Interview Model")
            print("  5) Final Stage Model")
            print("  6) Back")
            raw = (input("Enter 1-6 [6]: ").strip() or "6")
            if raw == "1":
                print("Providers: 1) OpenAI  2) Generic  3) Aether AI  4) AgentRouter  5) Requesty")
                p = input("Choose provider [current]: ").strip().lower()
                mapping = {"1": "openai", "2": "generic", "3": "aether", "4": "agentrouter", "5": "requesty"}
                if p in mapping:
                    session.provider = mapping[p]
                    # Prompt API key if missing
                    active = session.provider
                    if not (session.provider_keys or {}).get(active):
                        k = input("Enter API key (leave blank to skip): ")
                        if k and k.strip():
                            session.provider_keys[active] = k.strip()
                            session.api_key = k.strip()
            elif raw == "2":
                active = (session.provider or config.llm.provider or "openai").lower()
                k = input(f"Enter API key for {active} (leave blank to keep, '-' to clear): ")
                if k is not None:
                    k = k.strip()
                    if k == "-":
                        session.provider_keys.pop(active, None)
                    elif k:
                        session.provider_keys[active] = k
                        session.api_key = k
            elif raw == "3":
                active = (session.provider or config.llm.provider or "openai").lower()
                url = input(f"Enter base URL for '{active}' (leave blank to keep, '-' to clear): ")
                if url is not None:
                    url = url.strip()
                    if url == "-":
                        session.provider_base_urls.pop(active, None)
                    elif url:
                        session.provider_base_urls[active] = url
            elif raw == "4":
                m = input(f"Interview model (current: {session.interview_model or config.llm.model}): ").strip()
                if m:
                    session.interview_model = m
            elif raw == "5":
                m = input(
                    f"Final stage model (current: {session.final_stage_model or (config.devplan_llm.model if config.devplan_llm else config.llm.model)}): "
                ).strip()
                if m:
                    session.final_stage_model = m
            else:
                return


def _submenu_timeouts(config: AppConfig, session: SessionSettings) -> None:
    """Nested menu for API timeouts."""
    if _is_tty():
        while True:
            pick = (
                radiolist_dialog(
                    title="API Timeouts",
                    text=_current_settings_snapshot(config, session),
                    values=[
                        ("global", "API Timeout (Global)"),
                        ("design", "Design API Timeout"),
                        ("devplan", "DevPlan API Timeout"),
                        ("handoff", "Handoff API Timeout"),
                        ("back", "Back"),
                    ],
                ).run()
                or "back"
            )
            if pick == "global":
                val = input_dialog(
                    title="API Timeout (s)",
                    text=f"Set global API timeout in seconds (current: {session.api_timeout if session and session.api_timeout is not None else config.llm.api_timeout})",
                ).run()
                if val:
                    try:
                        session.api_timeout = max(1, int(str(val).strip()))
                    except Exception:
                        pass
                continue
            if pick == "design":
                val = input_dialog(
                    title="Design API Timeout (s)",
                    text=f"Set Design timeout (current: {(session.design_api_timeout if session and session.design_api_timeout is not None else (config.design_llm.api_timeout if config.design_llm and getattr(config.design_llm, 'api_timeout', None) is not None else '-'))}",
                ).run()
                if val:
                    try:
                        session.design_api_timeout = max(1, int(str(val).strip()))
                    except Exception:
                        pass
                continue
            if pick == "devplan":
                val = input_dialog(
                    title="DevPlan API Timeout (s)",
                    text=f"Set DevPlan timeout (current: {(session.devplan_api_timeout if session and session.devplan_api_timeout is not None else (config.devplan_llm.api_timeout if config.devplan_llm and getattr(config.devplan_llm, 'api_timeout', None) is not None else '-'))}",
                ).run()
                if val:
                    try:
                        session.devplan_api_timeout = max(1, int(str(val).strip()))
                    except Exception:
                        pass
                continue
            if pick == "handoff":
                val = input_dialog(
                    title="Handoff API Timeout (s)",
                    text=f"Set Handoff timeout (current: {(session.handoff_api_timeout if session and session.handoff_api_timeout is not None else (config.handoff_llm.api_timeout if config.handoff_llm and getattr(config.handoff_llm, 'api_timeout', None) is not None else '-'))}",
                ).run()
                if val:
                    try:
                        session.handoff_api_timeout = max(1, int(str(val).strip()))
                    except Exception:
                        pass
                continue
            if pick == "back":
                return
    else:
        while True:
            print("\n=== API Timeouts ===")
            print("  1) Global API Timeout")
            print("  2) Design API Timeout")
            print("  3) DevPlan API Timeout")
            print("  4) Handoff API Timeout")
            print("  5) Back")
            raw = (input("Enter 1-5 [5]: ").strip() or "5")
            try:
                if raw == "1":
                    session.api_timeout = max(1, int(input("Global API timeout (s): ").strip()))
                elif raw == "2":
                    session.design_api_timeout = max(1, int(input("Design API timeout (s): ").strip()))
                elif raw == "3":
                    session.devplan_api_timeout = max(1, int(input("DevPlan API timeout (s): ").strip()))
                elif raw == "4":
                    session.handoff_api_timeout = max(1, int(input("Handoff API timeout (s): ").strip()))
                else:
                    return
            except Exception:
                pass


def _submenu_concurrency(config: AppConfig, session: SessionSettings) -> None:
    """Nested menu for concurrency limits (parallel requests/phases)."""
    if _is_tty():
        while True:
            pick = (
                radiolist_dialog(
                    title="Concurrency",
                    text=_current_settings_snapshot(config, session),
                    values=[
                        ("max_concurrent", "Max concurrent API requests / phases"),
                        ("back", "Back"),
                    ],
                ).run()
                or "back"
            )
            if pick == "max_concurrent":
                val = input_dialog(
                    title="Max Concurrent Requests",
                    text=(
                        "Set maximum concurrent API requests (also controls how many "
                        "devplan phases are generated in parallel).\n"
                        f"Current: {session.max_concurrent_requests if session and session.max_concurrent_requests is not None else getattr(config, 'max_concurrent_requests', 5)}"
                    ),
                ).run()
                if val:
                    try:
                        # Allow at least 1; default config uses 5 for good phase parallelism.
                        session.max_concurrent_requests = max(1, int(str(val).strip()))
                    except Exception:
                        pass
                continue
            if pick == "back":
                return
    else:
        while True:
            print("\n=== Concurrency ===")
            current = session.max_concurrent_requests if session and session.max_concurrent_requests is not None else getattr(config, "max_concurrent_requests", 5)
            print(f"Current max concurrent requests/phases: {current}")
            print("  1) Set max concurrent requests")
            print("  2) Back")
            raw = (input("Enter 1-2 [2]: ").strip() or "2")
            if raw == "1":
                try:
                    val = int(input("Max concurrent requests (>=1): ").strip())
                    if val >= 1:
                        session.max_concurrent_requests = val
                except Exception:
                    pass
            else:
                return

def _submenu_streaming_options(config: AppConfig, session: SessionSettings) -> None:
    """Nested menu for phase-specific streaming configuration."""
    if _is_tty():
        while True:
            pick = (
                radiolist_dialog(
                    title="Streaming Options",
                    text=_current_settings_snapshot(config, session),
                    values=[
                        ("design", "Design Phase Streaming"),
                        ("devplan", "DevPlan Phase Streaming"),
                        ("handoff", "Handoff Phase Streaming"),
                        ("global", "Global Streaming (All Phases)"),
                        ("back", "Back"),
                    ],
                ).run()
                or "back"
            )
            if pick == "design":
                current = get_design_streaming_status(config, session)
                enabled = yes_no_dialog(
                    title="Design Phase Streaming",
                    text=f"Enable streaming for design generation? (current: {current})",
                    yes_text="Enable",
                    no_text="Disable",
                ).run()
                session.streaming_design_enabled = bool(enabled)
                continue
            if pick == "devplan":
                current = get_devplan_streaming_status(config, session)
                enabled = yes_no_dialog(
                    title="DevPlan Phase Streaming",
                    text=f"Enable streaming for devplan generation? (current: {current})",
                    yes_text="Enable",
                    no_text="Disable",
                ).run()
                session.streaming_devplan_enabled = bool(enabled)
                continue
            if pick == "handoff":
                current = get_handoff_streaming_status(config, session)
                enabled = yes_no_dialog(
                    title="Handoff Phase Streaming",
                    text=f"Enable streaming for handoff generation? (current: {current})",
                    yes_text="Enable",
                    no_text="Disable",
                ).run()
                session.streaming_handoff_enabled = bool(enabled)
                continue
            if pick == "global":
                current = session.streaming if session.streaming is not None else getattr(config, 'streaming_enabled', False)
                enabled = yes_no_dialog(
                    title="Global Streaming",
                    text=f"Enable streaming for all phases? (current: {current})",
                    yes_text="Enable",
                    no_text="Disable",
                ).run()
                session.streaming = bool(enabled)
                continue
            if pick == "back":
                return
    else:
        while True:
            print("\n=== Streaming Options ===")
            print("  1) Design Phase Streaming")
            print("  2) DevPlan Phase Streaming")
            print("  3) Handoff Phase Streaming")
            print("  4) Global Streaming (All Phases)")
            print("  5) Back")
            raw = (input("Enter 1-5 [5]: ").strip() or "5")
            try:
                if raw == "1":
                    current = get_design_streaming_status(config, session)
                    s = input(f"Enable design streaming? y/n (current: {current}): ").strip().lower()
                    if s in {"y", "yes"}:
                        session.streaming_design_enabled = True
                    elif s in {"n", "no"}:
                        session.streaming_design_enabled = False
                elif raw == "2":
                    current = get_devplan_streaming_status(config, session)
                    s = input(f"Enable devplan streaming? y/n (current: {current}): ").strip().lower()
                    if s in {"y", "yes"}:
                        session.streaming_devplan_enabled = True
                    elif s in {"n", "no"}:
                        session.streaming_devplan_enabled = False
                elif raw == "3":
                    current = get_handoff_streaming_status(config, session)
                    s = input(f"Enable handoff streaming? y/n (current: {current}): ").strip().lower()
                    if s in {"y", "yes"}:
                        session.streaming_handoff_enabled = True
                    elif s in {"n", "no"}:
                        session.streaming_handoff_enabled = False
                elif raw == "4":
                    current = session.streaming if session.streaming is not None else getattr(config, 'streaming_enabled', False)
                    s = input(f"Enable global streaming? y/n (current: {current}): ").strip().lower()
                    if s in {"y", "yes"}:
                        session.streaming = True
                    elif s in {"n", "no"}:
                        session.streaming = False
                else:
                    return
            except Exception:
                pass


def run_menu(config: AppConfig, session: Optional[SessionSettings] = None, force_show: bool = False) -> SessionSettings:
    """Run an interactive settings hub. Returns updated SessionSettings.

    Allows selecting individual options to change instead of a forced sequence.
    Falls back gracefully when no TTY is available.
    """
    # Merge last-used preferences as defaults
    saved = _load_prefs()
    base = session or SessionSettings()
    
    # Log the preference loading for debugging
    logger.debug(f"run_menu: Loaded preferences - provider: {saved.provider}, temp: {saved.temperature}")
    
    # Prefer explicit session values, else saved prefs
    for field in SessionSettings.model_fields.keys():
        if getattr(base, field, None) is None and getattr(saved, field, None) is not None:
            setattr(base, field, getattr(saved, field))
    
    # Log the final merged session
    logger.debug(f"run_menu: Final session - provider: {base.provider}, temp: {base.temperature}")
    session = base

    # TTY path (prompt_toolkit dialogs)
    if _is_tty():
        while True:
            try:
                choice = (
                    radiolist_dialog(
                        title="Settings",
                        text=_current_settings_snapshot(config, session) + "\n\nSelect a section)",
                        values=[
                            ("models", "Provider & Models"),
                            ("timeouts", "API Timeouts"),
                            ("concurrency", "Concurrency / Parallel Phases"),
                            ("temperature", "Temperature"),
                            ("max_tokens", "Max Tokens"),
                            ("reasoning", "Reasoning Effort (gpt-5)"),
                            ("streaming", "Streaming Options"),
                            ("back", "Exit Options & Save"),
                        ],
                    ).run()
                    or "back"
                )
            except (KeyboardInterrupt, EOFError):
                return session
            except Exception:
                # If the dialog cannot render, break to non-TTY fallback below
                break

            if choice == "models":
                # Persist after each settings submenu so .env stays in sync immediately
                _submenu_models(config, session)
                apply_settings_to_config(config, session)
                continue
            if choice == "timeouts":
                _submenu_timeouts(config, session)
                apply_settings_to_config(config, session)
                continue
            if choice == "concurrency":
                _submenu_concurrency(config, session)
                apply_settings_to_config(config, session)
                continue
            if choice == "temperature":
                provider_default = (session.provider or config.llm.provider or "openai").lower()
                provider = (
                    radiolist_dialog(
                        title="Temperature",
                        text=f"Set temperature 0.0-2.0 (current: {session.temperature if session.temperature is not None else config.llm.temperature})",
                        values=[("keep", "Keep current"), ("0.3", "0.3"), ("0.7", "0.7"), ("1.0", "1.0"), ("custom", "Custom...")],
                    ).run()
                    or "keep"
                )
                if provider == "custom":
                    val = input_dialog(title="Temperature", text="Enter temperature 0.0-2.0").run()
                    try:
                        t = float(val)
                        if 0.0 <= t <= 2.0:
                            session.temperature = t
                    except Exception:
                        pass
                elif provider != "keep":
                    try:
                        session.temperature = float(provider)
                    except Exception:
                        pass
                # Persist updated temperature immediately
                apply_settings_to_config(config, session)
                continue
            if choice == "max_tokens":
                max_toks_str = input_dialog(
                    title="Max Tokens",
                    text=f"Set max tokens (current: {session.max_tokens if session.max_tokens is not None else config.llm.max_tokens})",
                ).run()
                if max_toks_str:
                    try:
                        mt = int(max_toks_str)
                        if mt > 0:
                            session.max_tokens = mt
                    except ValueError:
                        pass
                # Persist updated max_tokens immediately
                apply_settings_to_config(config, session)
                continue
            if choice == "reasoning":
                pick = (
                    radiolist_dialog(
                        title="Reasoning Effort (gpt-5)",
                        text="Select reasoning effort for GPT-5 models",
                        values=[
                            ("", "Unset/Default"),
                            ("low", "low"),
                            ("medium", "medium"),
                            ("high", "high"),
                        ],
                    ).run()
                    or ""
                )
                session.reasoning_effort = (pick or None) or None
                # Persist updated reasoning_effort immediately
                apply_settings_to_config(config, session)
                continue
            if choice == "streaming":
                _submenu_streaming_options(config, session)
                # Persist updated streaming settings immediately
                apply_settings_to_config(config, session)
                continue
            # API creds editing moved into Provider & Models submenu
            if choice == "back":
                # Persist last state and return immediately
                apply_settings_to_config(config, session)
                _save_prefs(session)
                return session

    # Non-TTY fallback when explicitly forced
    if not _is_tty() and not force_show:
        return session

    while True:
        try:
            print("\n=== Settings ===")
            print(_current_settings_snapshot(config, session))
            print("\nSelect a section (or 6 to go back):")
            print("  1) Provider & Models")
            print("  2) API Timeouts")
            print("  3) Concurrency / Parallel Phases")
            print("  4) Temperature")
            print("  5) Max Tokens")
            print("  6) Streaming On/Off")
            print("  7) API Key")
            print("  8) Base URL (for Generic/Aether/AgentRouter providers)")
            print("  9) Reasoning Effort (gpt-5)")
            print(" 10) Back")
            try:
                raw = input("Enter 1-10 [10]: ").strip() or "10"
            except Exception:
                raw = "8"

            if raw == "1":
                _submenu_models(config, session)
            elif raw == "2":
                _submenu_timeouts(config, session)
            elif raw == "3":
                _submenu_concurrency(config, session)
            elif raw == "4":
                try:
                    t = float(input("Temperature 0.0-2.0: ").strip())
                    if 0.0 <= t <= 2.0:
                        session.temperature = t
                except Exception:
                    pass
            elif raw == "4":
                try:
                    t = float(input("Temperature 0.0-2.0: ").strip())
                    if 0.0 <= t <= 2.0:
                        session.temperature = t
                except Exception:
                    pass
            elif raw == "5":
                try:
                    mt = int(input("Max tokens: ").strip())
                    if mt > 0:
                        session.max_tokens = mt
                except Exception:
                    pass
            elif raw == "6":
                s = input(f"Enable streaming? y/n (current: {getattr(config, 'streaming_enabled', False)}): ").strip().lower()
                if s in {"y", "yes"}:
                    session.streaming = True
                elif s in {"n", "no"}:
                    session.streaming = False
            elif raw == "7":
                k = input("Enter API key (leave blank to keep current): ")
                if k and k.strip():
                    session.api_key = k.strip()
                    active_provider = (session.provider or config.llm.provider or "openai").lower()
                    session.provider_keys[active_provider] = session.api_key
            elif raw == "8":
                active_provider = (session.provider or config.llm.provider or "openai").lower()
                url = input(f"Enter base URL for current provider '{active_provider}' (leave blank to keep current): ")
                if url and url.strip():
                    session.provider_base_urls[active_provider] = url.strip()
            elif raw == "9":
                val = input("Reasoning effort (low/medium/high, blank to unset): ").strip().lower()
                if val in {"low", "medium", "high"}:
                    session.reasoning_effort = val
                elif val == "":
                    session.reasoning_effort = None
            elif raw == "10":
                _save_prefs(session)
                return session
        except (KeyboardInterrupt, EOFError):
            return session
action = Tuple[AppConfig, SessionSettings]


def _update_dotenv(path: str, updates: Dict[str, Optional[str]]) -> None:
    """Create or merge a .env file with the given key/value updates.

    - Ensures the file exists.
    - Rewrites only the specified keys; preserves others verbatim.
    - If a value is None or empty, the key is removed.
    """
    try:
        env_path = os.path.abspath(path)
        existing: Dict[str, str] = {}

        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        continue
                    key, val = stripped.split("=", 1)
                    existing[key.strip()] = val.strip()

        # Apply updates
        for key, value in updates.items():
            if value is None or value == "":
                existing.pop(key, None)
            else:
                existing[key] = str(value)

        # Write back
        lines = []
        for key, val in existing.items():
            lines.append(f"{key}={val}")
        content = "\n".join(lines) + ("\n" if lines else "")

        # Ensure directory exists (project root usually already does)
        os.makedirs(os.path.dirname(env_path) or ".", exist_ok=True)
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        # Never break UX due to .env persistence issues
        return


def apply_settings_to_config(config: AppConfig, session: SessionSettings) -> AppConfig:
    """Apply session settings to AppConfig in-memory and persist to .env."""
    # Determine project root (where .env should live)
    # We infer by walking up from this file until we find pyproject.toml or config/config.yaml.
    root = os.getcwd()
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        cur = here
        for _ in range(6):
            if (
                os.path.exists(os.path.join(cur, "pyproject.toml"))
                or os.path.exists(os.path.join(cur, "config", "config.yaml"))
            ):
                root = cur
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    except Exception:
        pass

    # Apply in-memory overrides (source of truth for running process)
    if session.provider:
        config.llm.provider = session.provider

    if session.interview_model:
        config.llm.model = session.interview_model

    if session.temperature is not None:
        config.llm.temperature = session.temperature
    if session.max_tokens is not None:
        config.llm.max_tokens = session.max_tokens

    if session.streaming is not None:
        config.streaming_enabled = session.streaming

    # Phase-specific streaming settings (with backward compatibility)
    if session.streaming_design_enabled is not None:
        if config.design_llm is None:
            config.design_llm = LLMConfig(streaming_enabled=session.streaming_design_enabled,
                                        provider=config.llm.provider,
                                        model=config.llm.model)
        else:
            config.design_llm.streaming_enabled = session.streaming_design_enabled

    if session.streaming_devplan_enabled is not None:
        if config.devplan_llm is None:
            config.devplan_llm = LLMConfig(streaming_enabled=session.streaming_devplan_enabled,
                                         provider=config.llm.provider,
                                         model=config.llm.model)
        else:
            config.devplan_llm.streaming_enabled = session.streaming_devplan_enabled

    if session.streaming_handoff_enabled is not None:
        if config.handoff_llm is None:
            config.handoff_llm = LLMConfig(streaming_enabled=session.streaming_handoff_enabled,
                                         provider=config.llm.provider,
                                         model=config.llm.model)
        else:
            config.handoff_llm.streaming_enabled = session.streaming_handoff_enabled

    # Reasoning effort (gpt-5)
    if session.reasoning_effort is not None:
        config.llm.reasoning_effort = session.reasoning_effort

    # Resolve API key and base_url for the active provider from per-provider maps
    active_provider = (session.provider or config.llm.provider or "openai").lower()
    resolved_api_key = (session.provider_keys or {}).get(active_provider)
    if not resolved_api_key and session.api_key:
        # Backward-compatibility: use legacy session.api_key if available
        resolved_api_key = session.api_key
    if resolved_api_key:
        # Set on global and per-stage configs if present
        config.llm.api_key = resolved_api_key
        if config.design_llm:
            config.design_llm.api_key = resolved_api_key
        if config.devplan_llm:
            config.devplan_llm.api_key = resolved_api_key
        if config.handoff_llm:
            config.handoff_llm.api_key = resolved_api_key

    # Resolve base URL for the active provider
    resolved_base_url = (session.provider_base_urls or {}).get(active_provider)
    if resolved_base_url:
        # Set on global and per-stage configs if present
        config.llm.base_url = resolved_base_url
        if config.design_llm:
            config.design_llm.base_url = resolved_base_url
        if config.devplan_llm:
            config.devplan_llm.base_url = resolved_base_url
        if config.handoff_llm:
            config.handoff_llm.base_url = resolved_base_url
    else:
        # Clear potentially stale base_url for providers that have safe defaults
        if active_provider in {"openai", "requesty", "aether", "agentrouter"}:
            config.llm.base_url = None
            if config.design_llm:
                config.design_llm.base_url = None
            if config.devplan_llm:
                config.devplan_llm.base_url = None
            if config.handoff_llm:
                config.handoff_llm.base_url = None

    if session.final_stage_model:
        # Ensure per-stage models are set for devplan/handoff and align provider with active provider
        if config.devplan_llm is None:
            config.devplan_llm = LLMConfig(model=session.final_stage_model, provider=config.llm.provider)
        else:
            config.devplan_llm.model = session.final_stage_model
            config.devplan_llm.provider = config.llm.provider
        if config.handoff_llm is None:
            config.handoff_llm = LLMConfig(model=session.final_stage_model, provider=config.llm.provider)
        else:
            config.handoff_llm.model = session.final_stage_model
            config.handoff_llm.provider = config.llm.provider

    # Always align stage providers with active provider (prevents stale provider mismatch)
    if config.design_llm is not None:
        config.design_llm.provider = config.llm.provider
    if config.devplan_llm is not None:
        config.devplan_llm.provider = config.llm.provider
    if config.handoff_llm is not None:
        config.handoff_llm.provider = config.llm.provider

    # Timeouts
    if session.api_timeout is not None:
        config.llm.api_timeout = session.api_timeout
    if session.design_api_timeout is not None:
        if config.design_llm is None:
            config.design_llm = LLMConfig(model=config.llm.model, provider=config.llm.provider, api_timeout=session.design_api_timeout)
        else:
            config.design_llm.api_timeout = session.design_api_timeout
    if session.devplan_api_timeout is not None:
        if config.devplan_llm is None:
            config.devplan_llm = LLMConfig(model=config.llm.model, provider=config.llm.provider, api_timeout=session.devplan_api_timeout)
        else:
            config.devplan_llm.api_timeout = session.devplan_api_timeout
    if session.handoff_api_timeout is not None:
        if config.handoff_llm is None:
            config.handoff_llm = LLMConfig(model=config.llm.model, provider=config.llm.provider, api_timeout=session.handoff_api_timeout)
        else:
            config.handoff_llm.api_timeout = session.handoff_api_timeout
    
        # Persist key settings into .env so they survive new processes.
    # Only write keys that are meaningful across sessions.
    env_updates: Dict[str, Optional[str]] = {}

    active_provider = (session.provider or config.llm.provider or "openai").lower()
 
    # Provider
    env_updates["LLM_PROVIDER"] = active_provider
 
    # Base URL persistence
    #
    # Intent:
    # - Only Generic should round-trip a base URL into .env (GENERIC_BASE_URL).
    # - All other providers use internal defaults; we do NOT write their BASE_URLs to .env,
    #   to avoid polluting config and accidentally breaking endpoints on provider switches.
    if active_provider == "generic" and config.llm.base_url:
        env_updates["GENERIC_BASE_URL"] = config.llm.base_url
    else:
        # Ensure we don't leave stale provider-specific BASE_URLs lying around.
        # This is defensive cleanup; if present, they can cause subtle bugs.
        env_updates["REQUESTY_BASE_URL"] = None
        env_updates["AETHER_BASE_URL"] = None
        env_updates["AGENTROUTER_BASE_URL"] = None
        env_updates["OPENAI_BASE_URL"] = None

    # Model persistence:
    # Unified semantics:
    # - Always persist the effective primary (interview) model as MODEL.
    # - Persist the final-stage model as FINAL_MODEL when explicitly set.
    # - Loaders can then:
    #     use FINAL_MODEL for final-phase work when present/valid,
    #     otherwise fall back to MODEL.
    if config.llm.model:
        env_updates["MODEL"] = config.llm.model
        # Backward-compatibility: ensure any legacy GENERIC_MODEL is not left stale.
        env_updates["GENERIC_MODEL"] = None

    # Persist FINAL_MODEL when we have an explicit final_stage_model configured.
    # Use getattr defensively to satisfy static analysis and avoid None-attribute issues.
    final_model: Optional[str] = None

    devplan_llm = getattr(config, "devplan_llm", None)
    if devplan_llm is not None:
        fm = getattr(devplan_llm, "model", None)
        if isinstance(fm, str) and fm.strip():
            final_model = fm.strip()

    if final_model is None:
        handoff_llm = getattr(config, "handoff_llm", None)
        if handoff_llm is not None:
            fm = getattr(handoff_llm, "model", None)
            if isinstance(fm, str) and fm.strip():
                final_model = fm.strip()

    if final_model:
        env_updates["FINAL_MODEL"] = final_model
    else:
        # No explicit final model configured -> remove stale FINAL_MODEL so loaders can fall back to MODEL
        env_updates["FINAL_MODEL"] = None

    # API keys (only persist if explicitly set in session to avoid leaking from process env)
    resolved_api_key = None
    if (session.provider_keys or {}).get(active_provider):
        resolved_api_key = session.provider_keys[active_provider]
    elif session.api_key:
        resolved_api_key = session.api_key

    if resolved_api_key:
        if active_provider == "openai":
            env_updates["OPENAI_API_KEY"] = resolved_api_key
        elif active_provider == "generic":
            env_updates["GENERIC_API_KEY"] = resolved_api_key
        elif active_provider == "requesty":
            env_updates["REQUESTY_API_KEY"] = resolved_api_key
        elif active_provider == "aether":
            env_updates["AETHER_API_KEY"] = resolved_api_key
        elif active_provider == "agentrouter":
            env_updates["AGENTROUTER_API_KEY"] = resolved_api_key

    # Streaming flag
    if session.streaming is not None:
        env_updates["STREAMING_ENABLED"] = "true" if session.streaming else "false"

    # Phase-specific streaming flags
    if session.streaming_design_enabled is not None:
        env_updates["STREAMING_DESIGN_ENABLED"] = "true" if session.streaming_design_enabled else "false"
    if session.streaming_devplan_enabled is not None:
        env_updates["STREAMING_DEVPLAN_ENABLED"] = "true" if session.streaming_devplan_enabled else "false"
    if session.streaming_handoff_enabled is not None:
        env_updates["STREAMING_HANDOFF_ENABLED"] = "true" if session.streaming_handoff_enabled else "false"

    # Concurrency: allow overriding via settings (persists as MAX_CONCURRENT_REQUESTS).
    if session.max_concurrent_requests is not None:
        try:
            # Enforce minimum of 1; recommended default is 5 for good phase parallelism.
            safe_val = max(1, int(session.max_concurrent_requests))
            config.max_concurrent_requests = safe_val
            env_updates["MAX_CONCURRENT_REQUESTS"] = str(safe_val)
        except Exception:
            pass

    # Timeouts are left primarily to config.yaml or manual env config.

    # Write updates into project-root .env (create if missing).
    _update_dotenv(os.path.join(root, ".env"), env_updates)

    return config


def _fetch_requesty_models_sync(api_key: str, base_url: str) -> list:
    """Fetch available Requesty models synchronously using aiohttp."""
    import aiohttp  # lazy import

    async def _fetch() -> dict:
        endpoint = f"{base_url.rstrip('/')}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(endpoint, headers=headers) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    raise RuntimeError(
                        f"Requesty API error {resp.status}: {error_text.strip() or 'unknown error'}"
                    )
                return await resp.json()

    data = asyncio.run(_fetch())
    models = data.get("data", data.get("models", []))
    sanitized = []
    for raw in models:
        model_id = raw.get("id") or raw.get("name")
        if not model_id:
            continue
        sanitized.append(
            {
                "id": model_id,
                "name": raw.get("name", model_id),
                "description": raw.get("description", ""),
                "context_window": raw.get("context_window", raw.get("max_tokens")),
            }
        )
    return sanitized


def _requesty_model_picker(
    config: AppConfig,
    session: SessionSettings,
    title: str,
    current: str,
) -> Optional[str]:
    """Interactive model picker.

    - If provider is Requesty and API key is available (or entered), fetch models and present a list.
    - Always include a Manual entry fallback.
    - If fetching fails or provider isn't Requesty, fall back to manual entry.
    """
    provider = (session.provider or config.llm.provider or "openai").lower()
    models: list = []
    used_requesty = False

    # If not on Requesty, offer to switch for interactive listing
    if provider != "requesty":
        switch = yes_no_dialog(
            title="Requesty Models",
            text=(
                "Interactive model browsing is available with the Requesty provider.\n"
                "Switch provider to Requesty to browse available models?"
            ),
            yes_text="Switch",
            no_text="Manual",
        ).run()
        if switch:
            session.provider = "requesty"
            provider = "requesty"
        else:
            # Manual entry fallback
            return input_dialog(title=title, text=f"Enter model id (current: {current})").run()


def _fetch_openai_compatible_models_sync(api_key: str, base_url: str) -> list:
    """Fetch models from an OpenAI-compatible endpoint synchronously.

    Tries {base}/models if base ends with '/v1', else {base}/v1/models.
    Returns a list of dicts with at least {'id': str}.
    """
    import aiohttp  # lazy import

    async def _fetch() -> dict:
        base = base_url.rstrip("/")
        endpoint = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(endpoint, headers=headers) as resp:
                if resp.status >= 400:
                    # Return empty list on error
                    return {"data": []}
                return await resp.json()

    data = asyncio.run(_fetch())
    models = data.get("data", [])
    sanitized = []
    for raw in models:
        model_id = raw.get("id") or raw.get("name")
        if not model_id:
            continue
        sanitized.append({"id": model_id})
    return sanitized


def _combined_model_picker(
    config: AppConfig,
    session: SessionSettings,
    title: str,
    current: str,
) -> Optional[str]:
    """Aggregate models across all providers with configured API keys.

    - Attempts to list models for each provider that has a configured key.
    - Requesty uses its models endpoint. Others use OpenAI-compatible /models if available.
    - Falls back to manual entry if no lists can be fetched.
    """
    providers = ["openai", "generic", "aether", "agentrouter", "requesty"]
    # Before fetching, ensure active provider has credentials so we can include it
    try:
        active = (session.provider or config.llm.provider or "openai").lower()
        # Prompt API key if missing
        if _is_tty() and not (session.provider_keys or {}).get(active):
            try:
                try:
                    api_key_input = input_dialog(
                        title=f"{active.capitalize()} API Key",
                        text="Enter API key (leave blank to skip, '-' to clear):",
                        password=True,
                    ).run()
                except TypeError:
                    api_key_input = prompt("Enter API key (leave blank to skip, '-' to clear): ", is_password=True)
                if api_key_input is not None:
                    api_key_input = api_key_input.strip()
                    if api_key_input == "-":
                        session.provider_keys.pop(active, None)
                    elif api_key_input:
                        session.provider_keys[active] = api_key_input
                        session.api_key = api_key_input
            except Exception:
                pass
        # Prompt Base URL if required provider and missing
        if _is_tty() and not (session.provider_base_urls or {}).get(active) and active in {"generic"}:
            try:
                default_map = {
                    "generic": "",
                }
                base_url_input = input_dialog(
                    title=f"Base URL for {active.capitalize()}",
                    text=f"Enter base URL (default: {default_map.get(active, '')}):",
                ).run()
                if base_url_input is not None:
                    base_url_input = base_url_input.strip()
                    if base_url_input:
                        session.provider_base_urls[active] = base_url_input
            except Exception:
                pass
        # Silently set defaults for Aether/AgentRouter if missing
        if not (session.provider_base_urls or {}).get(active):
            if active == "aether":
                session.provider_base_urls.setdefault("aether", "https://api.aetherapi.dev")
            elif active == "agentrouter":
                session.provider_base_urls.setdefault("agentrouter", "https://agentrouter.org/")
    except Exception:
        pass
    items: list[tuple[str, str]] = []

    def get_key_and_base(p: str) -> tuple[Optional[str], Optional[str], str]:
        # API key resolution: per-provider map -> env -> legacy session.api_key when active
        key = (session.provider_keys or {}).get(p)
        if not key:
            if p == "openai":
                key = os.getenv("OPENAI_API_KEY")
            elif p == "generic":
                key = os.getenv("GENERIC_API_KEY")
            elif p == "aether":
                key = os.getenv("AETHER_API_KEY")
            elif p == "agentrouter":
                key = os.getenv("AGENTROUTER_API_KEY")
            elif p == "requesty":
                key = os.getenv("REQUESTY_API_KEY")
        # final fallback: if this provider is currently active and legacy session.api_key exists
        if not key:
            active = (session.provider or config.llm.provider or "openai").lower()
            if p == active and session.api_key:
                key = session.api_key
        # Base URL resolution
        base = (session.provider_base_urls or {}).get(p)
        if not base:
            if p == "openai":
                base = "https://api.openai.com/v1"
            elif p == "generic":
                base = os.getenv("GENERIC_BASE_URL")
            elif p == "aether":
                base = os.getenv("AETHER_BASE_URL") or "https://api.aetherapi.dev"
            elif p == "agentrouter":
                base = os.getenv("AGENTROUTER_BASE_URL") or "https://agentrouter.org"
            elif p == "requesty":
                base = os.getenv("REQUESTY_BASE_URL") or "https://router.requesty.ai/v1"
        return key, base, p

    # Build combined list
    for p in providers:
        api_key, base_url, provider_id = get_key_and_base(p)
        if not api_key or not base_url:
            continue
        try:
            if provider_id == "requesty":
                lst = _fetch_requesty_models_sync(api_key, base_url)
                for m in lst:
                    mid = m.get("id") or m.get("name")
                    if mid:
                        label = f"{mid}  [Requesty]"
                        # encode provider with model so we can switch provider on selection
                        items.append((f"requesty::{mid}", label))
            else:
                lst = _fetch_openai_compatible_models_sync(api_key, base_url)
                for m in lst:
                    mid = m.get("id") or m.get("name")
                    if mid:
                        pretty = provider_id.capitalize() if provider_id != "agentrouter" else "AgentRouter"
                        label = f"{mid}  [{pretty}]"
                        items.append((f"{provider_id}::{mid}", label))
        except Exception:
            continue

    # De-duplicate while preserving order (by provider::model key)
    seen = set()
    deduped: list[tuple[str, str]] = []
    for t in items:
        if t[0] in seen:
            continue
        seen.add(t[0])
        deduped.append(t)

    # Build dialog values
    values = []
    if current:
        values.append((current, f"Keep current: {current}"))
    values.extend(deduped)
    values.append(("__manual__", "Manual entry..."))

    if values and _is_tty():
        pick = radiolist_dialog(
            title=title,
            text=(f"Select a model (current: {current})\n"),
            values=values,
        ).run()
        if pick == "__manual__":
            return input_dialog(title=title, text="Enter model id:").run()
        # If the pick encodes provider, switch provider accordingly and return plain model id
        if isinstance(pick, str) and "::" in pick:
            prov, mid = pick.split("::", 1)
            if prov:
                session.provider = prov
            return mid
        return pick

    # Manual fallback
    return input_dialog(title=title, text=f"Enter model id (current: {current})").run()


def _submenu_api_credentials(config: AppConfig, session: SessionSettings) -> None:
    """Manage per-provider API keys and base URLs.

    Rules:
    - Generic: requires a custom base URL (user must provide).
    - Requesty/Aether/AgentRouter/OpenAI: use known defaults; URL override is optional/advanced.
    """
    providers = [
        ("openai", "OpenAI"),
        ("generic", "Generic (OpenAI-compatible)"),
        ("aether", "Aether AI"),
        ("agentrouter", "AgentRouter"),
        ("requesty", "Requesty"),
    ]
    while True:
        pick = (
            radiolist_dialog(
                title="Provider API Keys & Endpoints",
                text="Select provider to edit API Key/Base URL",
                values=providers + [("back", "Back")],
            ).run()
            or "back"
        )
        if pick == "back":
            return
        try:
            # API Key
            try:
                key_in = input_dialog(
                    title=f"{dict(providers).get(pick, pick)} API Key",
                    text="Enter API key (leave blank to keep current, input '-' to clear):",
                    password=True,
                ).run()
            except TypeError:
                key_in = prompt(
                    "Enter API key (leave blank to keep current, '-' to clear): ",
                    is_password=True,
                )
            if key_in is not None:
                key_in = key_in.strip()
                if key_in == "-":
                    session.provider_keys.pop(pick, None)
                elif key_in:
                    session.provider_keys[pick] = key_in

            # Base URL behavior depends on provider
            label = dict(providers).get(pick, pick)
            # Generic MUST point somewhere explicit
            if pick == "generic":
                base_default = session.provider_base_urls.get(pick, "")
                base_in = input_dialog(
                    title=f"{label} Base URL (required)",
                    text=(
                        "Enter Base URL for your OpenAI-compatible endpoint "
                        "(e.g., https://api.example.com/v1). "
                        f"Leave blank to keep current ({base_default or 'none'}), '-' to clear."
                    ),
                ).run()
                if base_in is not None:
                    base_in = base_in.strip()
                    if base_in == "-":
                        session.provider_base_urls.pop(pick, None)
                    elif base_in:
                        session.provider_base_urls[pick] = base_in
            else:
                # Known providers: allow override but never require it
                base_default = (
                    session.provider_base_urls.get(pick)
                    or ("https://api.openai.com/v1" if pick == "openai" else None)
                    or ("https://api.aetherapi.dev" if pick == "aether" else None)
                    or ("https://agentrouter.org" if pick == "agentrouter" else None)
                    or ("https://router.requesty.ai/v1" if pick == "requesty" else None)
                    or ""
                )
                base_in = input_dialog(
                    title=f"{label} Base URL (advanced override)",
                    text=(
                        "Optional: Enter a custom Base URL to override the default "
                        f"(leave blank to keep current, '-' to clear). Default: {base_default}"
                    ),
                ).run()
                if base_in is not None:
                    base_in = base_in.strip()
                    if base_in == "-":
                        session.provider_base_urls.pop(pick, None)
                    elif base_in:
                        session.provider_base_urls[pick] = base_in
        except Exception:
            # Ignore UI errors, return to list
            pass

def show_readme() -> None:
    """Show a concise readme explaining circular development, DevPlan, phases, and handoff.

    Falls back to printing when not a TTY.
    """
    text = (
        "Devussy Overview\n\n"
        "What Devussy does\n"
        "• Devussy turns a short interview into a practical, phase-based development plan and a clear handoff doc.\n"
        "• It orchestrates LLM-assisted planning, keeps context between steps, and lets you tune provider, models, timeouts, and streaming.\n\n"
        "Circular development\n"
        "• Iterate between discovery → planning → execution → feedback.\n"
        "• Start with an interview, generate a DevPlan, refine phases/steps, and loop as needs evolve.\n\n"
        "DevPlan phases\n"
        "• The DevPlan groups work into phases with goals and exit criteria (e.g., Discovery, Design, Implementation, Testing, Handoff).\n"
        "• Each phase expands into detailed steps with owners, artifacts, and dependencies. Large plans can be paginated across calls.\n\n"
        "Handoff\n"
        "• The Handoff bundles intent, constraints, the DevPlan, and next actions for agents or humans.\n"
        "• It preserves continuity so you (or another tool) can resume later from the same context and re-enter the loop.\n\n"
        "Tips\n"
        "• Use Settings to pick provider/models/params (and timeouts).\n"
        "• Choose Start to begin the interview. Inside the interview, type /help for commands."
    )
    if not _is_tty():
        try:
            print("\n" + text + "\n")
        except Exception:
            pass
        return
    message_dialog(title="Devussy Readme", text=text, ok_text="Back").run()


def _toggle_repository_tools(session: SessionSettings) -> SessionSettings:
    """Toggle repository tools enabled state and return updated session."""
    current_state = session.repository_tools_enabled or False
    new_state = not current_state
    
    if _is_tty():
        state_text = "ENABLED" if new_state else "DISABLED"
        print(f"\n[TOOL] Repository Tools: {state_text}")
        if new_state:
            print("\nWhen enabled, the interview will:")
            print("  • Ask for repository path before starting")
            print("  • Prompt for project type (New vs Existing)")
            print("  • Run init_repo for new projects")
            print("  • Run analyze_repo for existing projects")
            print("  • Enhance the interview with repository context")
        print("\nThis setting affects the interview workflow.")
        
        if new_state:
            # We are enabling (new_state is True, so we want to enable)
            confirm = yes_no_dialog(
                title="Enable Repository Tools",
                text=f"Repository Tools are currently {'ENABLED' if current_state else 'DISABLED'}.\n\nEnable Repository Tools for enhanced repository-aware interviews?",
                yes_text="Enable",
                no_text="Keep Disabled",
            ).run()
            if not confirm:
                return session
        else:
            # We are disabling (new_state is False, so we want to disable)
            confirm = yes_no_dialog(
                title="Disable Repository Tools",
                text=f"Repository Tools are currently {'ENABLED' if current_state else 'DISABLED'}.\n\nDisable Repository Tools?",
                yes_text="Disable",
                no_text="Keep Enabled",
            ).run()
            if not confirm:
                return session
        
        session.repository_tools_enabled = new_state
        print(f"[OK] Repository Tools {'ENABLED' if new_state else 'DISABLED'}")
        return session
    else:
        current_state = session.repository_tools_enabled or False
        new_state = not current_state
        
        print(f"\nRepository Tools: {'ENABLED' if current_state else 'DISABLED'}")
        response = input(f"Enable Repository Tools? (y/n, current: {'ENABLED' if current_state else 'DISABLED'}): ").strip().lower()
        
        if response in ["y", "yes"]:
            session.repository_tools_enabled = True
            print("[OK] Repository Tools ENABLED")
            print("\nWhen enabled, the interview will:")
            print("  • Ask for repository path before starting")
            print("  • Prompt for project type (New vs Existing)")
            print("  • Run init_repo for new projects")
            print("  • Run analyze_repo for existing projects")
            print("  • Enhance the interview with repository context")
            return session
        elif response in ["n", "no"]:
            session.repository_tools_enabled = False
            print("[OK] Repository Tools DISABLED")
            return session
        else:
            print("No change made.")
            return session

def _submenu_testing(config: AppConfig, session: SessionSettings) -> SessionSettings:
    """Testing menu for accessing dead CLI commands that aren't reachable through python -m src.entry."""
    
    def _run_cli_command(command: str, args: Optional[list] = None) -> bool:
        """Run a CLI command and return success status."""
        try:
            cmd = [sys.executable, "-m", "src.entry", command]
            if args:
                cmd.extend(args)
            
            print(f"\n[TOOL] Running: {' '.join(cmd)}")
            print("=" * 50)
            
            result = subprocess.run(cmd, cwd=Path.cwd())
            
            if result.returncode == 0:
                print(f"[OK] Command completed successfully")
            else:
                print(f"[ERROR] Command failed with exit code {result.returncode}")
            
            return result.returncode == 0
        except Exception as e:
            print(f"[ERROR] Failed to run command: {e}")
            return False
    
    def _submenu_repository_management() -> None:
        """Repository management tools."""
        while True:
            if _is_tty():
                choice = (
                    radiolist_dialog(
                        title="Repository Management",
                        text="Repository initialization and analysis tools",
                        values=[
                            ("init-repo", "Initialize Repository"),
                            ("analyze-repo", "Analyze Repository"),
                            ("back", "Back"),
                        ],
                    ).run()
                    or "back"
                )
            else:
                print("\n=== Repository Management ===")
                print("1) Initialize Repository")
                print("2) Analyze Repository")
                print("3) Back")
                choice = input("Enter 1-3 [3]: ").strip() or "3"
                choice_map = {"1": "init-repo", "2": "analyze-repo", "3": "back"}
                choice = choice_map.get(choice, "back")
            
            if choice == "back":
                return
            elif choice in ["init-repo", "analyze-repo"]:
                args = None
                if choice == "init-repo":
                    repo_path = input("Repository path (current directory): ").strip()
                    if repo_path:
                        args = [repo_path]
                elif choice == "analyze-repo":
                    repo_path = input("Repository path (current directory): ").strip()
                    if repo_path:
                        args = [repo_path]
                
                _run_cli_command(choice, args)
            else:
                print("Please enter a valid option.")
    
    def _submenu_pipeline_tools() -> None:
        """Pipeline generation tools."""
        while True:
            if _is_tty():
                choice = (
                    radiolist_dialog(
                        title="Pipeline Tools",
                        text="Generate designs, devplans, and handoffs",
                        values=[
                            ("generate-design", "Generate Design"),
                            ("generate-devplan", "Generate DevPlan"),
                            ("generate-handoff", "Generate Handoff"),
                            ("run-full-pipeline", "Run Full Pipeline"),
                            ("launch", "Launch"),
                            ("back", "Back"),
                        ],
                    ).run()
                    or "back"
                )
            else:
                print("\n=== Pipeline Tools ===")
                print("1) Generate Design")
                print("2) Generate DevPlan")
                print("3) Generate Handoff")
                print("4) Run Full Pipeline")
                print("5) Launch")
                print("6) Back")
                choice = input("Enter 1-6 [6]: ").strip() or "6"
                choice_map = {
                    "1": "generate-design",
                    "2": "generate-devplan",
                    "3": "generate-handoff",
                    "4": "run-full-pipeline",
                    "5": "launch",
                    "6": "back"
                }
                choice = choice_map.get(choice, "back")
            
            if choice == "back":
                return
            elif choice in ["generate-design", "generate-devplan", "generate-handoff", "run-full-pipeline", "launch"]:
                _run_cli_command(choice)
            else:
                print("Please enter a valid option.")
    
    def _submenu_terminal_ui_tools() -> None:
        """Terminal and UI tools."""
        while True:
            if _is_tty():
                choice = (
                    radiolist_dialog(
                        title="Terminal & UI Tools",
                        text="Different UI modes and terminal interfaces",
                        values=[
                            ("generate-terminal", "Generate Terminal"),
                            ("interactive", "Interactive Mode"),
                            ("interview", "Interview Mode"),
                            ("back", "Back"),
                        ],
                    ).run()
                    or "back"
                )
            else:
                print("\n=== Terminal & UI Tools ===")
                print("1) Generate Terminal")
                print("2) Interactive Mode")
                print("3) Interview Mode")
                print("4) Back")
                choice = input("Enter 1-4 [4]: ").strip() or "4"
                choice_map = {
                    "1": "generate-terminal",
                    "2": "interactive",
                    "3": "interview",
                    "4": "back"
                }
                choice = choice_map.get(choice, "back")
            
            if choice == "back":
                return
            elif choice in ["generate-terminal", "interactive", "interview"]:
                _run_cli_command(choice)
            else:
                print("Please enter a valid option.")
    
    def _submenu_checkpoint_management() -> None:
        """Checkpoint management tools."""
        while True:
            if _is_tty():
                choice = (
                    radiolist_dialog(
                        title="Checkpoint Management",
                        text="Manage development session checkpoints",
                        values=[
                            ("list-checkpoints", "List Checkpoints"),
                            ("delete-checkpoint", "Delete Checkpoint"),
                            ("cleanup-checkpoints", "Cleanup Checkpoints"),
                            ("back", "Back"),
                        ],
                    ).run()
                    or "back"
                )
            else:
                print("\n=== Checkpoint Management ===")
                print("1) List Checkpoints")
                print("2) Delete Checkpoint")
                print("3) Cleanup Checkpoints")
                print("4) Back")
                choice = input("Enter 1-4 [4]: ").strip() or "4"
                choice_map = {
                    "1": "list-checkpoints",
                    "2": "delete-checkpoint",
                    "3": "cleanup-checkpoints",
                    "4": "back"
                }
                choice = choice_map.get(choice, "back")
            
            if choice == "back":
                return
            elif choice in ["list-checkpoints", "cleanup-checkpoints"]:
                _run_cli_command(choice)
            elif choice == "delete-checkpoint":
                checkpoint_id = input("Checkpoint ID to delete: ").strip()
                if checkpoint_id:
                    _run_cli_command(choice, [checkpoint_id])
            else:
                print("Please enter a valid option.")
    
    def _submenu_utilities() -> None:
        """Utility commands."""
        while True:
            if _is_tty():
                choice = (
                    radiolist_dialog(
                        title="Utilities",
                        text="Utility commands and tools",
                        values=[
                            ("version", "Show Version"),
                            ("back", "Back"),
                        ],
                    ).run()
                    or "back"
                )
            else:
                print("\n=== Utilities ===")
                print("1) Show Version")
                print("2) Back")
                choice = input("Enter 1-2 [2]: ").strip() or "2"
                choice_map = {"1": "version", "2": "back"}
                choice = choice_map.get(choice, "back")
            
            if choice == "back":
                return
            elif choice == "version":
                _run_cli_command(choice)
            else:
                print("Please enter a valid option.")
    
    # Main testing menu loop
    while True:
        try:
            print("\n=== Testing Menu - Dead CLI Commands ===")
            print("[WARN] ADVANCED FEATURES - NOT ACCESSIBLE VIA MAIN ENTRY [WARN]")
            print("")
            print("These CLI commands exist but aren't reachable through 'python -m src.entry'")
            print("They are accessible here for development and testing purposes.")
            print("")
            # Get current repository tools status for display
            repo_status = "ENABLED" if (session.repository_tools_enabled or False) else "DISABLED"
            
            print("Select a category:")
            print(f"  1) Repository Tools (<{repo_status}>)")
            print("  2) Pipeline Tools")
            print("  3) Terminal & UI Tools")
            print("  4) Checkpoint Management")
            print("  5) Utilities")
            print("  6) Back to Main Menu")
            
            if _is_tty():
                choice = (
                    radiolist_dialog(
                        title="Testing Menu",
                        text="Choose a category for dead CLI commands",
                        values=[
                            ("repo_tools", f"Repository Tools ({repo_status})"),
                            ("pipeline", "Pipeline Tools"),
                            ("terminal_ui", "Terminal & UI Tools"),
                            ("checkpoint", "Checkpoint Management"),
                            ("utilities", "Utilities"),
                            ("back", "Back to Main Menu"),
                        ],
                    ).run()
                    or "back"
                )
            else:
                raw = input("Enter 1-6 [6]: ").strip() or "6"
                choice_map = {
                    "1": "repo_tools",
                    "2": "pipeline",
                    "3": "terminal_ui",
                    "4": "checkpoint",
                    "5": "utilities",
                    "6": "back"
                }
                choice = choice_map.get(raw, "back")
            
            if choice == "repo_tools":
                session = _toggle_repository_tools(session)
                apply_settings_to_config(config, session)
                _save_prefs(session)
                continue
            elif choice == "pipeline":
                _submenu_pipeline_tools()
                continue
            elif choice == "terminal_ui":
                _submenu_terminal_ui_tools()
                continue
            elif choice == "checkpoint":
                _submenu_checkpoint_management()
                continue
            elif choice == "utilities":
                _submenu_utilities()
                continue
            elif choice == "back":
                return session
        except (KeyboardInterrupt, EOFError):
            return session
        except Exception as e:
            print(f"Error in testing menu: {e}")
            return session


def run_main_menu(config: AppConfig, force_show: bool = False) -> str:
    """Display a minimal start menu beneath the splash banner.

    Options: Start, Modify Options, Readme, Quit.
    Provider/Model selection remains available under Modify Options.
    """
    # Always use a lightweight numeric menu so the splash banner remains visible
    while True:
        try:
            print("\n=== devussy ===")
            print("Select an option:")
            print("  1) Start Devussy Workflow")
            print("  2) Modify Options")
            print("  3) Readme: Circular Development, DevPlan & Handoff")
            print("  4) Testing (Experimental Features)")
            print("  5) Quit")

            try:
                choice = input("Enter 1-5 [1]: ").strip()
            except Exception:
                # Fallback when stdin isn't interactive
                choice = "1"

            if choice == "":
                choice = "1"

            if choice == "1":
                return "start"
            if choice == "2":
                sess = SessionSettings()
                sess = run_menu(config, sess)
                apply_settings_to_config(config, sess)
                # After modifying options, loop back to main menu
                continue
            if choice == "3":
                show_readme()
                continue
            if choice == "4":
                sess = SessionSettings()
                # Load saved preferences for testing menu display
                saved = _load_prefs()
                for field in SessionSettings.model_fields.keys():
                    if getattr(sess, field, None) is None and getattr(saved, field, None) is not None:
                        setattr(sess, field, getattr(saved, field))
                sess = _submenu_testing(config, sess)
                apply_settings_to_config(config, sess)
                # After testing, loop back to main menu
                continue
            if choice == "5":
                return "quit"

            print("Please enter a number between 1 and 5.")
        except (KeyboardInterrupt, EOFError):
            return "quit"

