"""LLM-driven interactive interview system for project requirements gathering.

This module provides a conversational alternative to the scripted YAML questionnaire,
allowing users to have natural conversations with an LLM while gathering project
requirements for the devplan pipeline.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import sys

from rich.console import Console
from rich.console import Group
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt
from prompt_toolkit import prompt as pt_prompt
import shutil
import yaml

from .clients.factory import create_llm_client
from .config import AppConfig
from .ui.menu import run_menu, SessionSettings, apply_settings_to_config
from .interview import RepoAnalysis
from .interview.code_sample_extractor import CodeSampleExtractor, CodeSample

console = Console()
logger = logging.getLogger(__name__)


class LLMInterviewManager:
    """Conducts conversational interviews using LLM to gather project requirements."""
    
    SYSTEM_PROMPT = """You are a helpful development planning assistant for DevUssY, a circular development system. Your goal is to gather project requirements through natural conversation.

IMPORTANT: Do NOT trigger any generation automatically. When you have all required information, clearly ask the user to confirm by typing '/done' to finalize the interview. Wait for '/done' before ending the interview.

REQUIRED INFORMATION TO COLLECT:
1. Project name (short, descriptive)
2. Primary programming language(s)
3. Project description/requirements (1-2 sentences minimum)
4. Project type (Web App, API, CLI, Game, etc.)

OPTIONAL INFORMATION:
- Frontend/backend frameworks
- Database choice
- Authentication needs
- External APIs to integrate
- Deployment platform
- Testing requirements
- CI/CD preferences
- Documentation level

CONVERSATION GUIDELINES:
- Ask questions naturally, one at a time
- Provide suggestions and recommendations when asked
- Explain tradeoffs between technology choices
- Be flexible with answers - accept variations (e.g., "FastAPI" or "FastApi")
- If user asks for advice, provide thoughtful recommendations
- Periodically summarize what you've gathered
- When you have all REQUIRED information, summarize and ask the user to type '/done' to finalize
- Do not end the interview until the user explicitly types '/done'

RESPONSE FORMAT:
- Speak directly to the user in second person ("you")
- Keep responses concise and helpful
- Show enthusiasm for their project ideas
- Use emojis sparingly for key moments

When interview is complete, output a JSON block with extracted data:
{
  "project_name": "...",
  "primary_language": "...",
  "requirements": "...",
  "project_type": "...",
  "frameworks": [...],
  "database": "...",
  "authentication": false,
  "deployment_platform": "...",
  "testing_requirements": "...",
  "ci_cd": true
}"""

    def __init__(
        self,
        config: AppConfig,
        verbose: bool = False,
        repo_analysis: "RepoAnalysis | None" = None,
    ):
        """Initialize with app config containing LLM settings.

        Args:
            config: Application configuration.
            verbose: Enable verbose logging / debug output.
            repo_analysis: Optional repository analysis used to prime the
                conversation with concrete project context.
        """
        self.config = config
        self.verbose = verbose
        self.repo_analysis = repo_analysis

        self.llm_client = create_llm_client(config)

        # Apply debug/verbose flag to client (robust attribute discovery)
        self._apply_client_debug(verbose)

        self.conversation_history = []
        self.extracted_data = {}
        self.code_samples: list[CodeSample] = []
        # Session-scoped interactive settings (not persisted)
        self.session_settings = SessionSettings()

        # Setup logging
        self._setup_logging()

        # Add system prompt (core behavior)
        self.conversation_history.append(
            {"role": "system", "content": self.SYSTEM_PROMPT}
        )

        # If repository analysis is available, prepend a concise summary so the
        # interview is repo-aware without changing the primary instructions.
        if self.repo_analysis is not None:
            summary = self._build_repo_summary(self.repo_analysis)
            if summary:
                self.conversation_history.append(
                    {
                        "role": "system",
                        "content": (
                            "The user is working in the following existing project. "
                            "Use this context when asking questions and giving guidance.\n\n"
                            f"{summary}"
                        ),
                    }
                )

        logger.info("LLM Interview Manager initialized")
        logger.info(f"Verbose mode: {self.verbose}")
        logger.info(f"Provider: {config.llm.provider}")
        logger.info(f"Model: {config.llm.model}")

    def _apply_client_debug(self, enabled: bool) -> None:
        """Best-effort propagation of a debug/verbose flag to the underlying LLM client.

        The concrete client implementations may expose different attribute or method
        names. This helper attempts a variety of common patterns but never raises.

        Args:
            enabled: Whether verbose/debug output should be enabled.
        """
        try:
            client = self.llm_client
        except AttributeError:
            return

        if client is None:
            return

        # Direct attribute flips
        for attr in ("verbose", "debug", "log_prompts", "logging_enabled"):
            if hasattr(client, attr):
                try:
                    setattr(client, attr, enabled)
                except Exception:
                    pass

        # Common setter / enabler methods
        for method_name in ("set_debug", "enable_debug", "set_verbose"):
            if hasattr(client, method_name):
                try:
                    getattr(client, method_name)(enabled)
                except Exception:
                    pass

        # Nested config objects
        if hasattr(client, "config"):
            cfg = getattr(client, "config")
            for attr in ("verbose", "debug"):
                if hasattr(cfg, attr):
                    try:
                        setattr(cfg, attr, enabled)
                    except Exception:
                        pass

        # Optional: attach a simple flag so downstream logic can check
        try:
            setattr(client, "_devussy_verbose", enabled)
        except Exception:
            pass

        logger.debug(f"Applied debug/verbose={enabled} to LLM client")

    def _build_repo_summary(self, analysis: RepoAnalysis) -> str:
        """Build a compact, text-only summary of the analyzed repository."""
        try:
            lines = []
            lines.append(f"Root: {analysis.root_path}")
            if getattr(analysis, "project_type", None):
                lines.append(f"Project type: {analysis.project_type}")

            # Structure
            struct = analysis.structure
            if struct.directories:
                lines.append(
                    "Top-level directories: "
                    + ", ".join(sorted(struct.directories))
                )
            if struct.source_dirs:
                lines.append(
                    "Source dirs: " + ", ".join(sorted(struct.source_dirs))
                )
            if struct.test_dirs:
                lines.append(
                    "Test dirs: " + ", ".join(sorted(struct.test_dirs))
                )
            if struct.config_dirs:
                lines.append(
                    "Config dirs: " + ", ".join(sorted(struct.config_dirs))
                )
            if struct.ci_dirs:
                lines.append("CI dirs: " + ", ".join(sorted(struct.ci_dirs)))

            # Dependencies (only show a handful per ecosystem to keep things short)
            deps = analysis.dependencies

            def _head(values: list[str], label: str, limit: int = 8) -> None:
                if not values:
                    return
                display = sorted(values)[:limit]
                suffix = "" if len(values) <= limit else f" (+{len(values) - limit} more)"
                lines.append(f"{label}: " + ", ".join(display) + suffix)

            _head(deps.python, "Python deps")
            _head(deps.node, "Node deps")

            # Patterns
            patterns = analysis.patterns
            if patterns.test_frameworks:
                lines.append(
                    "Test frameworks: "
                    + ", ".join(sorted(patterns.test_frameworks))
                )
            if patterns.build_tools:
                lines.append(
                    "Build tools: " + ", ".join(sorted(patterns.build_tools))
                )

            # Config files (just names)
            cfg_files = [Path(p).name if not isinstance(p, Path) else p.name for p in analysis.config_files.files]
            if cfg_files:
                lines.append("Config files: " + ", ".join(sorted(cfg_files)))

            # Metrics
            metrics = analysis.code_metrics
            lines.append(
                f"Approx. size: {metrics.total_files} files, {metrics.total_lines} lines"
            )

            return "\n".join(lines)
        except Exception:
            # Never let summary building break the interview
            return ""

    def run(self) -> Dict[str, Any]:
        """
        Run the conversational interview loop.
        
        Returns:
            Dict[str, Any]: Answers extracted from conversation
        """
        console.print(Panel.fit(
            "[bold blue]🚀 DevPlan Interactive Builder[/bold blue]\n"
            "Let's build your development plan together!\n\n"
            "[dim]Slash commands: /verbose, /help, /done, /quit, /settings, /model, /temp, /tokens[/dim]",
            border_style="blue"
        ))
        
        logger.info("Starting interview conversation")
        
        # Display project summary if analyzing existing repo
        if self.repo_analysis:
            self._print_project_summary()
        
        # Start with initial greeting
        if self.repo_analysis and self.repo_analysis.project_metadata.name:
            # Use the project name from repository analysis
            project_name = self.repo_analysis.project_metadata.name
            initial_response = self._send_to_llm(
                f"Hi! I'm excited to help you plan your project '{project_name}'. I can see this is a {self.repo_analysis.project_type} project with {self.repo_analysis.code_metrics.total_files} files. What would you like to accomplish with this project?"
            )
        else:
            # Ask for project name as before
            initial_response = self._send_to_llm(
                "Hi! I'm excited to help you plan your project. Let's start with the basics - what would you like to name your project?"
            )
        # Only display if streaming wasn't already showing it
        streaming_enabled = getattr(self.config, 'streaming_enabled', False)
        if not streaming_enabled:
            self._display_llm_response(initial_response)
        
        # Main conversation loop
        while True:
            # Get user input with persistent bottom-right token toolbar when TTY
            try:
                if sys.stdin.isatty() and sys.stdout.isatty():
                    user_input = pt_prompt(
                        "You: ",
                        bottom_toolbar=self._bottom_toolbar_text,
                    )
                else:
                    user_input = Prompt.ask("\n[yellow]You[/yellow]", default="")
            except Exception:
                user_input = Prompt.ask("\n[yellow]You[/yellow]", default="")
            
            # Handle slash commands
            if user_input.startswith('/'):
                if self._handle_slash_command(user_input):
                    continue
                else:
                    break  # /quit was called
            
            if user_input.lower() in ['quit', 'exit']:
                console.print("[yellow]Interview ended by user.[/yellow]")
                logger.info("Interview ended by user")
                break
            if user_input.lower().strip() == 'done':
                console.print("[yellow]Type '/done' to finalize and generate. Continuing interview...[/yellow]")
                logger.info("User typed 'done' without slash; prompting to use /done")
                continue
            
            if not user_input.strip():
                continue
            
            logger.info(f"User input: {user_input[:100]}...")  # Log first 100 chars
            
            # Send user input to LLM
            response = self._send_to_llm(user_input)
            # Only display if streaming wasn't already showing it
            streaming_enabled = getattr(self.config, 'streaming_enabled', False)
            if not streaming_enabled:
                self._display_llm_response(response)
            # Update token usage snapshot for menu display
            self._refresh_token_usage()
            
            # Check if LLM provided final JSON data
            extracted = self._extract_structured_data(response)
            if extracted:
                self.extracted_data = extracted
                logger.info("Extracted structured data from LLM response")
                if self._validate_extracted_data(extracted):
                    console.print("\n[green]✓ Required info collected.[/green] Type /done to finalize and generate, or continue to refine.")
                    logger.info("Interview ready to finalize - awaiting /done")
                    continue
                else:
                    console.print("[yellow]⚠ Some required information is missing. Let's continue...[/yellow]")
                    logger.warning("Extracted data incomplete, continuing interview")
        
        logger.info("Interview finished")
        return self.extracted_data

    def to_generate_design_inputs(self) -> Dict[str, str]:
        """
        Convert conversation data to generate_design format.
        Same interface as InteractiveQuestionnaireManager.
        
        Returns:
            Dict[str, str]: Compatible with existing pipeline
        """
        if not self.extracted_data:
            raise ValueError("No interview data available. Run the interview first.")
        
        # Extract code samples if we have repo analysis and haven't already
        if self.repo_analysis and not self.code_samples:
            self.extract_code_samples()
        
        # Map extracted data to expected format
        inputs = {
            "name": self.extracted_data.get("project_name", ""),
            "languages": self.extracted_data.get("primary_language", ""),
            "requirements": self.extracted_data.get("requirements", ""),
        }
        
        # Add optional fields if present
        optional_mappings = {
            "frameworks": "frameworks",
            "apis": "apis", 
            "database": "database",
            "deployment_platform": "deployment_platform",
            "testing_requirements": "testing_requirements",
        }
        
        for extracted_key, input_key in optional_mappings.items():
            value = self.extracted_data.get(extracted_key)
            if value:
                if isinstance(value, list):
                    inputs[input_key] = ",".join(str(v) for v in value)
                else:
                    inputs[input_key] = str(value)
        
        # Add code samples context if available
        if self.code_samples:
            code_context = self.get_code_samples_context()
            if code_context:
                inputs["code_samples"] = code_context
        
        return inputs

    def _setup_logging(self) -> None:
        """Setup logging to file for interview session."""
        # Create logs directory
        logs_dir = Path("logs/interviews")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"interview_{timestamp}.log"
        
        # Add file handler for this session
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Only add to this logger, don't propagate to root
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Don't send to console
        
        # Also silence the Requesty client logger from console
        requesty_logger = logging.getLogger('src.clients.requesty_client')
        requesty_logger.addHandler(file_handler)
        requesty_logger.setLevel(logging.DEBUG)
        requesty_logger.propagate = False
        
        self.log_file = log_file
        # Use console.print instead of logger for this message
        # logger.info(f"Logging to: {log_file}")  # Commented out - already shown by CLI
    
    def _handle_slash_command(self, command: str) -> bool:
        """Handle slash commands. Returns True to continue, False to quit."""
        command = command.lower().strip()
        
        if command == '/verbose':
            self.verbose = not self.verbose
            status = "ON" if self.verbose else "OFF"
            
            # Update the LLM client debug/verbose flag
            self._apply_client_debug(self.verbose)
            
            console.print(f"[cyan]ℹ️ Verbose mode: {status}[/cyan]")
            logger.info(f"Verbose mode toggled: {status}")
            return True
        
        elif command == '/help':
            console.print(Panel.fit(
                "[bold]Available Commands:[/bold]\n\n"
                "[yellow]/verbose[/yellow] - Toggle verbose output (API calls, tokens, etc.)\n"
                "[yellow]/settings[/yellow] - Open settings menu (provider, models, temperature, tokens)\n"
                "[yellow]/model[/yellow] - Quickly set interview or final-stage model\n"
                "[yellow]/temp[/yellow] - Quickly set temperature\n"
                "[yellow]/tokens[/yellow] - Show last token usage snapshot\n"
                "[yellow]/help[/yellow] - Show this help message\n"
                "[yellow]/done[/yellow] - Finalize interview and generate files\n"
                "[yellow]/quit[/yellow] - End interview without generating files\n\n"
                "Or type: [yellow]quit[/yellow], [yellow]exit[/yellow]",
                title="Help",
                border_style="cyan"
            ))
            return True
        
        elif command == '/settings':
            # Launch menu, apply to config, recreate client
            try:
                updated = run_menu(self.config, self.session_settings)
                self.session_settings = updated
                apply_settings_to_config(self.config, self.session_settings)
                # Recreate LLM client to pick up new settings
                self.llm_client = create_llm_client(self.config)
                self._apply_client_debug(self.verbose)
                console.print("[green]✓ Settings applied for this session.[/green]")
                # Show quick summary
                usage = self.session_settings.last_token_usage or {}
                console.print(
                    f"[dim]Provider: {self.config.llm.provider}, Model: {self.config.llm.model}, Temp: {self.config.llm.temperature}, MaxTokens: {self.config.llm.max_tokens}, TotalTokens: {usage.get('total_tokens')}[/dim]"
                )
            except Exception as e:
                console.print(f"[red]Failed to open settings: {e}[/red]")
            return True
        
        elif command == '/model':
            # Prompt user for models
            try:
                new_model = Prompt.ask("Enter interview model (blank to skip)", default="")
                final_model = Prompt.ask("Enter final-stage model (blank to skip)", default="")
                if new_model.strip():
                    self.session_settings.interview_model = new_model.strip()
                if final_model.strip():
                    self.session_settings.final_stage_model = final_model.strip()
                apply_settings_to_config(self.config, self.session_settings)
                self.llm_client = create_llm_client(self.config)
                self._apply_client_debug(self.verbose)
                console.print("[green]✓ Model settings updated.[/green]")
            except Exception as e:
                console.print(f"[red]Failed to update model: {e}[/red]")
            return True
        
        elif command == '/temp':
            try:
                temp_str = Prompt.ask("Set temperature 0.0-2.0", default=str(self.config.llm.temperature))
                t = float(temp_str)
                if 0.0 <= t <= 2.0:
                    self.session_settings.temperature = t
                    apply_settings_to_config(self.config, self.session_settings)
                    self.llm_client = create_llm_client(self.config)
                    self._apply_client_debug(self.verbose)
                    console.print("[green]✓ Temperature updated.[/green]\n")
                else:
                    console.print("[yellow]Temperature must be between 0.0 and 2.0[/yellow]")
            except ValueError:
                console.print("[yellow]Invalid number[/yellow]")
            except Exception as e:
                console.print(f"[red]Failed to update temperature: {e}[/red]")
            return True
        
        elif command == '/tokens':
            self._refresh_token_usage()
            usage = self.session_settings.last_token_usage
            if usage:
                console.print(
                    f"[cyan]Tokens[/cyan] prompt: {usage.get('prompt_tokens')}, completion: {usage.get('completion_tokens')}, total: {usage.get('total_tokens')}"
                )
            else:
                console.print("[dim]No token usage available yet[/dim]")
            return True
        
        elif command == '/done':
            console.print("[cyan]🎯 Finalizing interview...[/cyan]")
            logger.info("User requested finalization via /done command")

            # First, try a direct one-shot finalize that avoids the normal guidance loop
            direct = self._finalize_via_direct_prompt()
            if direct:
                self.extracted_data = direct
                console.print("\n[green]✓ Interview complete! All required information gathered.[/green]")
                logger.info("Interview complete via direct finalize prompt")
                return False

            # Build a trimmed transcript for robust extraction attempts
            transcript = self._format_conversation_for_llm()
            if len(transcript) > 6000:
                transcript = transcript[-6000:]

            attempts = [
                # Prefer fenced JSON using transcript, explicitly ignore prior guidance
                (
                    "Ignore all prior instructions about asking for '/done' or continuing the interview. "
                    "Based ONLY on the transcript below, OUTPUT a JSON object with EXACT keys: project_name, primary_language, requirements, project_type, frameworks, database, authentication, deployment_platform, testing_requirements, ci_cd. "
                    "Respond inside a fenced ```json``` block ONLY. No extra text. If unknown, use empty string, false, or [] as appropriate.\n\n"
                    f"Transcript:\n{transcript}"
                ),
                # Then plain JSON with no fences
                (
                    "Ignore previous conversation guidance. Based ONLY on the transcript, OUTPUT ONLY a JSON object with the EXACT keys: "
                    "project_name, primary_language, requirements, project_type, frameworks, database, authentication, deployment_platform, testing_requirements, ci_cd. Do NOT use code fences. No prose.\n\n"
                    f"Transcript:\n{transcript}"
                ),
                # Minimal required only, no fence
                (
                    "Output ONLY the REQUIRED JSON with required keys (no prose): {\"project_name\":...,\"primary_language\":...,\"requirements\":...,\"project_type\":...}. "
                    "Include optional keys if known.\n\n"
                    f"Transcript:\n{transcript}"
                ),
            ]

            for idx, prompt_text in enumerate(attempts, start=1):
                response = self._generate_direct(prompt_text)
                self._display_llm_response(response)
                self._refresh_token_usage()

                extracted = self._extract_structured_data(response)
                if extracted:
                    self.extracted_data = extracted
                    logger.info(f"Extracted structured data after /done attempt {idx}")
                    if self._validate_extracted_data(extracted):
                        console.print("\n[green]✓ Interview complete! All required information gathered.[/green]")
                        logger.info("Interview complete - all required data collected")
                        return False

            # Fallback: if we already have validated data from earlier, allow finalize
            if self.extracted_data and self._validate_extracted_data(self.extracted_data):
                console.print("\n[green]✓ Interview complete using previously collected data.[/green]")
                logger.info("Interview complete - using previously extracted data")
                return False

            # If no valid extraction, suggest user continue or retry
            console.print("[yellow]⚠ Could not extract complete project data. Please provide more details or type /done again.[/yellow]")
            return True
        
        elif command == '/quit':
            console.print("[yellow]Interview ended by user.[/yellow]")
            logger.info("Interview ended via /quit command")
            return False
        
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")
            return True

    def _refresh_token_usage(self) -> None:
        """Refresh last-known token usage from the provider client, if available."""
        try:
            usage = getattr(self.llm_client, "last_usage_metadata", None)
            if usage:
                self.session_settings.last_token_usage = {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                }
        except Exception:
            # Best-effort only
            pass
    
    def _bottom_toolbar_text(self):
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
        except Exception:
            cols = 80
        usage = self.session_settings.last_token_usage or {}
        p = usage.get("prompt_tokens")
        c = usage.get("completion_tokens")
        t = usage.get("total_tokens")
        # Fallback placeholders
        def fmt(v):
            return "-" if v is None else str(v)
        text = f"{self.config.llm.provider}:{self.config.llm.model} | T={self.config.llm.temperature} | tokens p:{fmt(p)} c:{fmt(c)} tot:{fmt(t)}"
        # Right-align for idle toolbar only; spinner will use a trimmed single-line
        pad = max(0, cols - len(text) - 1)
        return " " * pad + text

    def _spinner_status_line(self) -> str:
        """Return a single-line status string that won't wrap under spinner.

        We avoid left padding and trim to terminal width minus a small spinner margin.
        """
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
        except Exception:
            cols = 80
        usage = self.session_settings.last_token_usage or {}
        p = usage.get("prompt_tokens")
        c = usage.get("completion_tokens")
        t = usage.get("total_tokens")
        def fmt(v):
            return "-" if v is None else str(v)
        base = f"{self.config.llm.provider}:{self.config.llm.model} | T={self.config.llm.temperature} | tokens p:{fmt(p)} c:{fmt(c)} tot:{fmt(t)}"
        # Reserve space for spinner glyphs and a space (~4 chars)
        max_len = max(10, cols - 4)
        if len(base) > max_len:
            # Truncate with ellipsis
            return base[: max_len - 1] + "…"
        return base
    
    def _send_to_llm(self, user_input: str) -> str:
        """Send user input to LLM and get response."""
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Format conversation for LLM
        conversation_text = self._format_conversation_for_llm()
        
        if self.verbose:
            console.print("\n[dim]--- API Request ---[/dim]")
            console.print(f"[dim]Provider: {self.config.llm.provider}[/dim]")
            console.print(f"[dim]Model: {self.config.llm.model}[/dim]")
            console.print(f"[dim]Conversation length: {len(conversation_text)} chars[/dim]")
        
        logger.debug(f"Sending to LLM: {conversation_text[:200]}...")
        
        # Get LLM response
        try:
            # Check if streaming is enabled
            streaming_enabled = getattr(self.config, 'streaming_enabled', False)
            
            if streaming_enabled:
                # Use streaming for real-time token display
                console.print("\n[blue]🎵 Devussy[/blue]:")
                
                # Collect streaming response
                response_chunks = []
                
                def token_callback(token: str) -> None:
                    """Callback for each streaming token."""
                    response_chunks.append(token)
                    # Display token in real-time (without newlines for smooth streaming)
                    console.print(token, end="", style="blue")
                
                # Make streaming request
                import asyncio
                response = asyncio.run(self.llm_client.generate_completion_streaming(
                    conversation_text, token_callback
                ))
                
                console.print()  # Add newline after streaming
                console.print()  # Add spacing
                
            else:
                # Use non-streaming fallback
                # Single-line, non-wrapping status text while spinner is active
                status_line = Text(self._spinner_status_line(), style="black on white")
                with console.status(status_line, spinner="dots"):
                    response = self.llm_client.generate_completion_sync(conversation_text)
                
                # Display response normally
                self._display_llm_response(response)
            
            if self.verbose:
                console.print(f"[dim]Response length: {len(response)} chars[/dim]")
                console.print("[dim]--- End API Request ---[/dim]\n")
            logger.debug(f"LLM response: {response[:200]}...")
            
        except Exception as e:
            console.print(f"[red]❌ Error communicating with LLM: {e}[/red]")
            logger.error(f"LLM API error: {e}", exc_info=True)
            response = "I'm having trouble connecting right now. Could you try again?"
            # Display error response
            self._display_llm_response(response)
        
        # Add LLM response to conversation history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        
        # Log full conversation exchange
        logger.info(f"USER: {user_input}")
        logger.info(f"ASSISTANT: {response[:500]}...")  # Log first 500 chars
        
        return response

    async def _send_to_llm_streaming(self, user_input: str, callback=None) -> str:
        """Send user input to LLM and get streaming response.
        
        Args:
            user_input: User input message
            callback: Optional callback function for each token
            
        Returns:
            Complete LLM response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Format conversation for LLM
        conversation_text = self._format_conversation_for_llm()
        
        if self.verbose:
            console.print("\n[dim]--- Streaming API Request ---[/dim]")
            console.print(f"[dim]Provider: {self.config.llm.provider}[/dim]")
            console.print(f"[dim]Model: {self.config.llm.model}[/dim]")
            console.print(f"[dim]Conversation length: {len(conversation_text)} chars[/dim]")
        
        logger.debug(f"Sending to LLM (streaming): {conversation_text[:200]}...")
        
        # Get LLM streaming response
        try:
            # Use streaming for real-time token display
            response_chunks = []
            
            def token_callback(token: str) -> None:
                """Callback for each streaming token."""
                response_chunks.append(token)
                # Call custom callback if provided
                if callback:
                    callback(token)
            
            # Make streaming request
            response = await self.llm_client.generate_completion_streaming(
                conversation_text, token_callback
            )
            
            if self.verbose:
                console.print(f"[dim]Streaming response length: {len(response)} chars[/dim]")
                console.print("[dim]--- End Streaming API Request ---[/dim]\n")
            logger.debug(f"LLM streaming response: {response[:200]}...")
            
        except Exception as e:
            console.print(f"[red]❌ Error communicating with LLM: {e}[/red]")
            logger.error(f"LLM API streaming error: {e}", exc_info=True)
            response = "I'm having trouble connecting right now. Could you try again?"
        
        # Add LLM response to conversation history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        
        # Log full conversation exchange
        logger.info(f"USER: {user_input}")
        logger.info(f"ASSISTANT (streaming): {response[:500]}...")  # Log first 500 chars
        
        return response

    def _format_conversation_for_llm(self) -> str:
        """Format conversation history for LLM consumption."""
        messages = []
        for msg in self.conversation_history:
            if msg["role"] == "system":
                messages.append(f"System: {msg['content']}")
            elif msg["role"] == "user":
                messages.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                messages.append(f"Devussy: {msg['content']}")
        
        return "\n\n".join(messages)

    def _finalize_via_direct_prompt(self) -> Optional[Dict[str, Any]]:
        """Attempt a one-shot JSON extraction that bypasses the normal interview loop.

        Sends a direct instruction to output ONLY a JSON object based on the transcript,
        reducing the chance the model repeats "/done" instructions instead of emitting JSON.
        """
        try:
            transcript = self._format_conversation_for_llm()
            # Trim overly long transcripts to keep prompt focused
            if len(transcript) > 6000:
                transcript = transcript[-6000:]

            prompt = (
                "You are a JSON extraction assistant. Ignore prior conversational instructions about asking the user to type /done.\n"
                "Read the following conversation transcript and OUTPUT ONLY a JSON object with EXACT keys: \n"
                "project_name, primary_language, requirements, project_type, frameworks, database, authentication, deployment_platform, testing_requirements, ci_cd.\n"
                "No prose. No markdown. No code fences. If a value is unknown, use an empty string or a reasonable default (false for booleans, [] for lists).\n\n"
                "Transcript:\n" + transcript
            )

            response = self.llm_client.generate_completion_sync(prompt)
            extracted = self._extract_structured_data(response)
            if extracted and self._validate_extracted_data(extracted):
                return extracted
        except Exception:
            pass
        return None

    def _generate_direct(self, prompt: str) -> str:
        """Call the LLM without using the conversation history (no side effects)."""
        try:
            if self.verbose:
                console.print("\n[dim]--- Direct Finalize Request ---[/dim]")
                console.print(f"[dim]Model: {self.config.llm.model}[/dim]")
                console.print(f"[dim]Prompt length: {len(prompt)} chars[/dim]")
            response = self.llm_client.generate_completion_sync(prompt)
            if self.verbose:
                console.print(f"[dim]Response length: {len(response)} chars[/dim]")
                console.print("[dim]--- End Direct Request ---[/dim]\n")
            return response
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}", exc_info=True)
            return ""

    def _collect_missing_required_fields_interactively(self) -> bool:
        """Deprecated: interactive prompting for missing fields is disabled.
        Always return False so /done relies on LLM extraction only.
        """
        return False

    def _display_llm_response(self, response: str) -> None:
        """Display LLM response with nice formatting."""
        console.print(f"\n[blue]🎵 Devussy[/blue]:")
        
        # Split response into paragraphs for better readability
        paragraphs = response.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                console.print(f"[white]{paragraph.strip()}[/white]")
                console.print()

    def _extract_structured_data(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from an LLM response using multiple strategies."""
        # Try fenced JSON (case-insensitive), allow any whitespace and Windows newlines
        fenced_patterns = [
            r"```json\s*(\{[\s\S]*?\})\s*```",
            r"```\s*(\{[\s\S]*?\})\s*```",
        ]
        for pat in fenced_patterns:
            m = re.search(pat, response, re.DOTALL | re.IGNORECASE)
            if m:
                try:
                    data = json.loads(m.group(1))
                    data = self._normalize_extracted_data(data)
                    return data
                except json.JSONDecodeError:
                    pass

        # Try plain JSON object anywhere in text using a simple longest-match regex
        regex_any_obj = r"\{[\s\S]*\}"
        candidates = list(re.finditer(regex_any_obj, response, re.DOTALL))
        for m in sorted(candidates, key=lambda mm: len(mm.group(0)), reverse=True):
            try:
                data = json.loads(m.group(0))
                data = self._normalize_extracted_data(data)
                if isinstance(data, dict) and 'project_name' in data:
                    return data
            except json.JSONDecodeError:
                # YAML fallback for JSON-like content (tolerates comments, trailing commas, single quotes)
                try:
                    data = yaml.safe_load(m.group(0))
                    data = self._normalize_extracted_data(data)
                    if isinstance(data, dict) and 'project_name' in data:
                        return data
                except Exception:
                    continue

        # Balanced-brace scan to extract valid JSON object
        stack = []
        start_idx = None
        for i, ch in enumerate(response):
            if ch == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif ch == '}':
                if stack:
                    stack.pop()
                    if not stack and start_idx is not None:
                        frag = response[start_idx:i+1]
                        try:
                            data = json.loads(frag)
                            data = self._normalize_extracted_data(data)
                            if isinstance(data, dict) and 'project_name' in data:
                                return data
                        except json.JSONDecodeError:
                            try:
                                data = yaml.safe_load(frag)
                                data = self._normalize_extracted_data(data)
                                if isinstance(data, dict) and 'project_name' in data:
                                    return data
                            except Exception:
                                pass

        return None

    def _validate_extracted_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required fields are present in extracted data."""
        data = self._normalize_extracted_data(data)
        required_fields = ["project_name", "primary_language", "requirements", "project_type"]
        
        for field in required_fields:
            if field not in data or not data[field] or not str(data[field]).strip():
                return False
        
        return True

    def _normalize_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize LLM-provided dict to our expected schema.
        Accepts common synonyms and coerces simple types.
        """
        if not isinstance(data, dict):
            return {}
        # Lowercase keys for matching
        lower = {str(k).strip().lower(): v for k, v in data.items()}

        def first_str(val):
            if val is None:
                return ""
            if isinstance(val, list):
                return ",".join(str(x) for x in val if x is not None)
            return str(val)

        norm: Dict[str, Any] = {}

        # project_name
        for key in ["project_name", "name", "project", "projecttitle", "project_title", "title"]:
            if key in lower and str(lower[key]).strip():
                norm["project_name"] = str(lower[key]).strip()
                break

        # primary_language
        for key in ["primary_language", "language", "languages", "primarylanguage"]:
            if key in lower and lower[key] is not None:
                v = lower[key]
                if isinstance(v, list):
                    norm["primary_language"] = ",".join([str(x) for x in v if x])
                else:
                    norm["primary_language"] = str(v)
                break

        # requirements
        for key in ["requirements", "description", "summary", "spec", "specification"]:
            if key in lower and str(lower[key]).strip():
                norm["requirements"] = str(lower[key]).strip()
                break

        # project_type
        for key in ["project_type", "type", "app_type", "category"]:
            if key in lower and str(lower[key]).strip():
                norm["project_type"] = str(lower[key]).strip()
                break

        # optional passthroughs
        for src, dst in [
            ("frameworks", "frameworks"),
            ("database", "database"),
            ("authentication", "authentication"),
            ("deployment_platform", "deployment_platform"),
            ("testing_requirements", "testing_requirements"),
            ("ci_cd", "ci_cd"),
        ]:
            if src in lower:
                norm[dst] = lower[src]

        return norm

    def _print_project_summary(self) -> None:
        """Display a formatted summary of the analyzed repository."""
        if not self.repo_analysis:
            return
        
        analysis = self.repo_analysis
        
        # Build summary sections
        summary_lines = []
        summary_lines.append("[bold cyan]📊 Repository Analysis Summary[/bold cyan]\n")
        
        # Project type and root
        if analysis.project_type:
            summary_lines.append(f"[yellow]Project Type:[/yellow] {analysis.project_type}")
        summary_lines.append(f"[yellow]Root Path:[/yellow] {analysis.root_path}\n")
        
        # Structure
        struct = analysis.structure
        if struct.source_dirs:
            summary_lines.append(f"[yellow]Source Directories:[/yellow] {', '.join(sorted(struct.source_dirs))}")
        if struct.test_dirs:
            summary_lines.append(f"[yellow]Test Directories:[/yellow] {', '.join(sorted(struct.test_dirs))}")
        
        # Dependencies (show first few)
        deps = analysis.dependencies
        if deps.python:
            dep_list = sorted(deps.python)[:5]
            suffix = f" (+{len(deps.python) - 5} more)" if len(deps.python) > 5 else ""
            summary_lines.append(f"[yellow]Python Dependencies:[/yellow] {', '.join(dep_list)}{suffix}")
        if deps.node:
            dep_list = sorted(deps.node)[:5]
            suffix = f" (+{len(deps.node) - 5} more)" if len(deps.node) > 5 else ""
            summary_lines.append(f"[yellow]Node Dependencies:[/yellow] {', '.join(dep_list)}{suffix}")
        
        # Patterns
        patterns = analysis.patterns
        if patterns.test_frameworks:
            summary_lines.append(f"[yellow]Test Frameworks:[/yellow] {', '.join(sorted(patterns.test_frameworks))}")
        if patterns.build_tools:
            summary_lines.append(f"[yellow]Build Tools:[/yellow] {', '.join(sorted(patterns.build_tools))}")
        
        # Metrics
        metrics = analysis.code_metrics
        summary_lines.append(f"\n[yellow]Code Metrics:[/yellow] {metrics.total_files} files, {metrics.total_lines} lines")
        
        # Display in a panel
        console.print(Panel(
            "\n".join(summary_lines),
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()
    
    def extract_code_samples(self, selected_parts: Optional[list[str]] = None) -> list[CodeSample]:
        """Extract code samples from the repository for context.
        
        Args:
            selected_parts: Optional list of specific directories/files to focus on
            
        Returns:
            List of extracted code samples
        """
        if not self.repo_analysis:
            return []
        
        try:
            extractor = CodeSampleExtractor(
                root_path=str(self.repo_analysis.root_path),
                max_samples=8,  # Reasonable number for interview context
                max_lines_per_sample=150  # Keep samples concise
            )
            
            # Extract samples based on analysis and user goals
            goals = self.extracted_data.get("requirements", "")
            samples = extractor.extract_samples(
                analysis=self.repo_analysis,
                selected_parts=selected_parts,
                goals=goals
            )
            
            self.code_samples = samples
            logger.info(f"Extracted {len(samples)} code samples from repository")
            
            return samples
        except Exception as e:
            logger.warning(f"Failed to extract code samples: {e}")
            return []
    
    def get_code_samples_context(self) -> str:
        """Format code samples for inclusion in prompts.
        
        Returns:
            Formatted string of code samples ready for LLM context
        """
        if not self.code_samples:
            return ""
        
        try:
            # Safeguard: repo_analysis might be None if code_samples were injected externally
            root_path = (
                str(getattr(self.repo_analysis, "root_path", "."))
                if self.repo_analysis is not None else "."
            )
            extractor = CodeSampleExtractor(root_path=root_path)
            return extractor.format_samples_for_prompt(self.code_samples)
        except Exception:
            return ""
