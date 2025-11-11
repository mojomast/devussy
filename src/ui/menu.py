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
                            ("requesty", "Requesty"),
                        ],
                    ).run()
                    or provider_default
                )
                session.provider = provider
                continue
            if pick == "interview_model":
                selected = _requesty_model_picker(
                    config,
                    session,
                    title="Interview Model",
                    current=session.interview_model or config.llm.model,
                )
                if selected:
                    session.interview_model = selected.strip()
                continue
            if pick == "final_stage_model":
                selected = _requesty_model_picker(
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
            print("  2) Interview Model")
            print("  3) Final Stage Model")
            print("  4) Back")
            raw = (input("Enter 1-4 [4]: ").strip() or "4")
            if raw == "1":
                print("Providers: 1) OpenAI  2) Generic  3) Requesty")
                p = input("Choose provider [current]: ").strip().lower()
                mapping = {"1": "openai", "2": "generic", "3": "requesty"}
                if p in mapping:
                    session.provider = mapping[p]
            elif raw == "2":
                m = input(f"Interview model (current: {session.interview_model or config.llm.model}): ").strip()
                if m:
                    session.interview_model = m
            elif raw == "3":
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
                            ("api_key", "API Key"),
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
            if choice == "api_key":
                try:
                    try:
                        api_key_input = input_dialog(
                            title="API Key",
                            text="Enter API key (leave blank to keep current):",
                            password=True,
                        ).run()
                    except TypeError:
                        api_key_input = prompt("Enter API key (leave blank to keep current): ", is_password=True)
                    if api_key_input and api_key_input.strip():
                        session.api_key = api_key_input.strip()
                except Exception:
                    pass
                continue
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
            print("  7) Reasoning Effort (gpt-5)")
            print("  8) Back")
            try:
                raw = input("Enter 1-8 [8]: ").strip() or "8"
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
            elif raw == "7":
                val = input("Reasoning effort (low/medium/high, blank to unset): ").strip().lower()
                if val in {"low", "medium", "high"}:
                    session.reasoning_effort = val
                elif val == "":
                    session.reasoning_effort = None
            elif raw == "8":
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

    if session.api_key:
        # Set on global and per-stage configs if present
        config.llm.api_key = session.api_key
        if config.design_llm:
            config.design_llm.api_key = session.api_key
        if config.devplan_llm:
            config.devplan_llm.api_key = session.api_key
        if config.handoff_llm:
            config.handoff_llm.api_key = session.api_key

    if session.final_stage_model:
        # Ensure per-stage models are set for devplan/handoff
        if config.devplan_llm is None:
            config.devplan_llm = LLMConfig(model=session.final_stage_model, provider=config.llm.provider)
        else:
            config.devplan_llm.model = session.final_stage_model
        if config.handoff_llm is None:
            config.handoff_llm = LLMConfig(model=session.final_stage_model, provider=config.llm.provider)
        else:
            config.handoff_llm.model = session.final_stage_model

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

    if provider == "requesty":
        used_requesty = True
        api_key = (
            session.api_key
            or getattr(config.llm, "api_key", None)
            or os.getenv("REQUESTY_API_KEY")
        )
        base_url = (
            getattr(config.llm, "base_url", None)
            or os.getenv("REQUESTY_BASE_URL")
            or "https://router.requesty.ai/v1"
        )

        if not api_key:
            try:
                try:
                    api_key = input_dialog(
                        title="Requesty API Key",
                        text="Enter Requesty API key:",
                        password=True,
                    ).run()
                except TypeError:
                    api_key = prompt("Enter Requesty API key: ", is_password=True)
                if api_key and api_key.strip():
                    session.api_key = api_key.strip()
            except Exception:
                api_key = None

        if api_key:
            try:
                models = _fetch_requesty_models_sync(api_key, base_url)
            except Exception as exc:
                message_dialog(
                    title="Requesty Error",
                    text=f"Failed to fetch Requesty models.\n{exc}",
                    ok_text="OK",
                ).run()
                models = []

    if models:
        values = []
        if current:
            values.append((current, f"Keep current: {current}"))
        for m in models:
            mid = m.get("id") or m.get("name")
            if not mid:
                continue
            ctx = m.get("context_window") or m.get("max_tokens")
            label = f"{mid}" + (f" (ctx: {ctx})" if ctx else "")
            values.append((mid, label))
        values.append(("__manual__", "Manual entry..."))

        pick = radiolist_dialog(
            title=title,
            text=(
                f"Select a model (current: {current})\n"
                + ("Provider: Requesty\n" if used_requesty else "")
            ),
            values=values,
        ).run()

        if pick == "__manual__":
            return input_dialog(title=title, text="Enter model id:").run()
        return pick

    # Manual fallback
    return input_dialog(title=title, text=f"Enter model id (current: {current})").run()

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

