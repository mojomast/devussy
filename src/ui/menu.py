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


class SessionSettings(BaseModel):
    provider: Optional[str] = None
    interview_model: Optional[str] = None
    final_stage_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    streaming: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # Added for generic provider endpoint
    provider_keys: Optional[Dict[str, str]] = Field(default_factory=dict)
    provider_base_urls: Optional[Dict[str, str]] = Field(default_factory=dict)
    # GPT-5 reasoning level: low | medium | high
    reasoning_effort: Optional[str] = None
    last_token_usage: Optional[Dict[str, int]] = Field(default=None)
    # Timeouts (seconds)
    api_timeout: Optional[int] = None
    design_api_timeout: Optional[int] = None
    devplan_api_timeout: Optional[int] = None
    handoff_api_timeout: Optional[int] = None


def _is_tty() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _current_settings_snapshot(config: AppConfig, session: Optional[SessionSettings]) -> str:
    llm = config.llm
    lines = [
        f"Provider: {llm.provider}",
        f"Interview Model: {(session.interview_model if session and session.interview_model else llm.model)}",
        f"Final Stage Model: {(session.final_stage_model if session and session.final_stage_model else (config.devplan_llm.model if config.devplan_llm else llm.model))}",
        f"Temperature: {session.temperature if session and session.temperature is not None else llm.temperature}",
        f"Max Tokens: {session.max_tokens if session and session.max_tokens is not None else llm.max_tokens}",
        f"Reasoning (gpt-5): {(session.reasoning_effort if session and session.reasoning_effort else getattr(llm, 'reasoning_effort', None) or '-')}",
        f"Streaming: {session.streaming if session and session.streaming is not None else getattr(config, 'streaming_enabled', False)}",
        f"API Timeout: {session.api_timeout if session and session.api_timeout is not None else llm.api_timeout}s",
        f"Design Timeout: {(session.design_api_timeout if session and session.design_api_timeout is not None else (config.design_llm.api_timeout if config.design_llm and getattr(config.design_llm, 'api_timeout', None) is not None else '-'))}s",
        f"DevPlan Timeout: {(session.devplan_api_timeout if session and session.devplan_api_timeout is not None else (config.devplan_llm.api_timeout if config.devplan_llm and getattr(config.devplan_llm, 'api_timeout', None) is not None else '-'))}s",
        f"Handoff Timeout: {(session.handoff_api_timeout if session and session.handoff_api_timeout is not None else (config.handoff_llm.api_timeout if config.handoff_llm and getattr(config.handoff_llm, 'api_timeout', None) is not None else '-'))}s",
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
        return SessionSettings(**data)
    except Exception:
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
                        ("back", "Back"),
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


def run_menu(config: AppConfig, session: Optional[SessionSettings] = None, force_show: bool = False) -> SessionSettings:
    """Run an interactive settings hub. Returns updated SessionSettings.

    Allows selecting individual options to change instead of a forced sequence.
    Falls back gracefully when no TTY is available.
    """
    # Merge last-used preferences as defaults
    saved = _load_prefs()
    base = session or SessionSettings()
    # Prefer explicit session values, else saved prefs
    for field in SessionSettings.model_fields.keys():
        if getattr(base, field, None) is None and getattr(saved, field, None) is not None:
            setattr(base, field, getattr(saved, field))
    session = base

    # TTY path (prompt_toolkit dialogs)
    if _is_tty():
        while True:
            try:
                choice = (
                    radiolist_dialog(
                        title="Settings",
                        text=_current_settings_snapshot(config, session) + "\n\nSelect a section (or Back)",
                        values=[
                            ("models", "Provider & Models"),
                            ("timeouts", "API Timeouts"),
                            ("temperature", "Temperature"),
                            ("max_tokens", "Max Tokens"),
                            ("reasoning", "Reasoning Effort (gpt-5)"),
                            ("streaming", "Streaming On/Off"),
                            ("back", "Back"),
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
                _submenu_models(config, session)
                continue
            if choice == "timeouts":
                _submenu_timeouts(config, session)
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
                continue
            if choice == "streaming":
                streaming_choice = yes_no_dialog(
                    title="Streaming",
                    text=f"Enable streaming? (current: {getattr(config, 'streaming_enabled', False)})",
                    yes_text="Enable",
                    no_text="Disable",
                ).run()
                session.streaming = bool(streaming_choice)
                continue
            # API creds editing moved into Provider & Models submenu
            if choice == "back":
                # Final summary before returning
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
            print("  3) Temperature")
            print("  4) Max Tokens")
            print("  5) Streaming On/Off")
            print("  6) API Key")
            print("  7) Base URL (for Generic/Aether/AgentRouter providers)")
            print("  8) Reasoning Effort (gpt-5)")
            print("  9) Back")
            try:
                raw = input("Enter 1-9 [9]: ").strip() or "9"
            except Exception:
                raw = "8"

            if raw == "1":
                _submenu_models(config, session)
            elif raw == "2":
                _submenu_timeouts(config, session)
            elif raw == "3":
                try:
                    t = float(input("Temperature 0.0-2.0: ").strip())
                    if 0.0 <= t <= 2.0:
                        session.temperature = t
                except Exception:
                    pass
            elif raw == "4":
                try:
                    mt = int(input("Max tokens: ").strip())
                    if mt > 0:
                        session.max_tokens = mt
                except Exception:
                    pass
            elif raw == "5":
                s = input(f"Enable streaming? y/n (current: {getattr(config, 'streaming_enabled', False)}): ").strip().lower()
                if s in {"y", "yes"}:
                    session.streaming = True
                elif s in {"n", "no"}:
                    session.streaming = False
            elif raw == "6":
                k = input("Enter API key (leave blank to keep current): ")
                if k and k.strip():
                    session.api_key = k.strip()
                    active_provider = (session.provider or config.llm.provider or "openai").lower()
                    session.provider_keys[active_provider] = session.api_key
            elif raw == "7":
                active_provider = (session.provider or config.llm.provider or "openai").lower()
                url = input(f"Enter base URL for current provider '{active_provider}' (leave blank to keep current): ")
                if url and url.strip():
                    session.provider_base_urls[active_provider] = url.strip()
            elif raw == "8":
                val = input("Reasoning effort (low/medium/high, blank to unset): ").strip().lower()
                if val in {"low", "medium", "high"}:
                    session.reasoning_effort = val
                elif val == "":
                    session.reasoning_effort = None
            elif raw == "9":
                _save_prefs(session)
                return session
        except (KeyboardInterrupt, EOFError):
            return session
action = Tuple[AppConfig, SessionSettings]


def apply_settings_to_config(config: AppConfig, session: SessionSettings) -> AppConfig:
    """Apply session settings to AppConfig in-memory without persisting to disk."""
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
    """Manage per-provider API keys and base URLs to avoid overlap."""
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
        # Edit credentials for selected provider
        try:
            # API Key
            try:
                key_in = input_dialog(
                    title=f"{dict(providers).get(pick, pick)} API Key",
                    text="Enter API key (leave blank to keep current, input '-' to clear):",
                    password=True,
                ).run()
            except TypeError:
                key_in = prompt("Enter API key (leave blank to keep current, '-' to clear): ", is_password=True)
            if key_in is not None:
                key_in = key_in.strip()
                if key_in == "-":
                    session.provider_keys.pop(pick, None)
                elif key_in:
                    session.provider_keys[pick] = key_in

            # Base URL
            base_default = (
                session.provider_base_urls.get(pick)
                or ("https://api.openai.com/v1" if pick == "openai" else None)
                or ("https://api.aetherapi.dev" if pick == "aether" else None)
                or ("https://agentrouter.org" if pick == "agentrouter" else None)
                or ("https://router.requesty.ai/v1" if pick == "requesty" else None)
                or ""
            )
            base_in = input_dialog(
                title=f"{dict(providers).get(pick, pick)} Base URL",
                text=f"Enter Base URL (leave blank to keep current, input '-' to clear). Default: {base_default}",
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
            print("  4) Quit")

            try:
                choice = input("Enter 1-4 [1]: ").strip()
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
                return "quit"

            print("Please enter a number between 1 and 4.")
        except (KeyboardInterrupt, EOFError):
            return "quit"

