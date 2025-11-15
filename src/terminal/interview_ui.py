"""Terminal UI-based interview interface for interactive requirements gathering.

This module provides a Textual-based UI for conducting LLM-driven interviews
within the terminal, replacing the console-based interview with a rich interface.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import (
    Header,
    Footer,
    Static,
    Input,
    TextArea,
    Button,
    Label,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.dom import NoMatches
from rich.text import Text

from ..llm_interview import LLMInterviewManager
from ..interview import RepoAnalysis
from ..config import AppConfig


def _find_project_root(start: Path) -> Path:
    """Find project root by looking for markers like pyproject.toml or .git.

    Falls back to provided start directory.
    """
    markers = {"pyproject.toml", ".git", "requirements.txt"}
    cur = start
    for _ in range(6):
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start


def _load_logo_text() -> str:
    """Load ASCII logo from DEVUSSYLOGO.MD near project root.

    Returns a best-effort string; falls back to a simple title when not found.
    """
    try:
        here = Path(__file__).resolve()
        root = _find_project_root(here.parent)
        logo_path = root / "DEVUSSYLOGO.MD"
        if logo_path.exists():
            return logo_path.read_text(encoding="utf-8").rstrip("\n")
    except Exception:
        pass
    return "DEVUSSY"


class InterviewScreen(App):
    """Terminal UI app for conducting LLM interviews."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .interview-container {
        padding: 1;
        height: 100%;
    }
    
    .banner {
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
        margin: 0 0 1 0;
        text-style: bold;
        min-height: 7;
    }
    
    .conversation-area {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .input-area {
        height: auto;
        padding: 1;
        margin-top: 1;
    }
    
    .status-bar {
        height: 3;
        background: $boost;
        padding: 0 1;
        text-align: center;
    }
    
    .user-message {
        background: $accent;
        padding: 1;
        margin: 1 0;
        border: solid $accent;
        text-style: bold;
    }
    
    .assistant-message {
        background: $surface;
        padding: 1;
        margin: 1 0;
        border: solid $surface;
    }
    
    .system-message {
        background: $warning;
        padding: 1;
        margin: 1 0;
        border: solid $warning;
        text-style: italic;
    }
    
    Input {
        width: 100%;
        height: 3;
    }
    
    Button {
        margin: 0 1;
    }
    
    .help-text {
        color: $text-muted;
        text-style: italic;
    }
    
    .settings-panel {
        background: $surface;
        border: solid $primary;
        padding: 1;
        height: 20;
        width: 60;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+d", "done", "Done"),
        Binding("f1", "help", "Help"),
        Binding("f2", "settings", "Settings"),
        Binding("ctrl+s", "settings", "Settings"),
    ]
    
    interview_complete = reactive(False)
    interview_data = reactive(None)
    
    def __init__(
        self,
        interview_manager: LLMInterviewManager,
        repo_analysis: Optional[RepoAnalysis] = None,
    ):
        """Initialize the interview UI."""
        super().__init__()
        self.interview_manager = interview_manager
        self.repo_analysis = repo_analysis
        self.conversation_history: list[tuple[str, str]] = []
        self.interview_complete = False
        self.interview_data = None
        self._logo_text = _load_logo_text()
        self._conversation_display: Optional[Static] = None
    
    def on_mount(self) -> None:
        """Initialize the interview when UI is mounted."""
        # Enable mouse support if available
        try:
            self.screen.mouse_enabled = True  # type: ignore[assignment]
        except Exception:
            pass

        self._add_system_message("🎵 Starting DevUssY interview...")
        if self.repo_analysis:
            self._add_system_message(
                f"📁 Repository analyzed: {self.repo_analysis.project_type}"
            )

        # Start the interview with an initial message
        asyncio.create_task(self._start_interview())

        # Focus the input
        try:
            self.query_one("#user-input", Input).focus()
        except Exception:
            pass

        # Cache the conversation display widget and ensure something is visible
        try:
            self._conversation_display = self.query_one("#conversation-log", Static)
            if self.conversation_history:
                self._update_conversation_display()
            else:
                self._conversation_display.update(
                    "🔧 System: DevUssY interview ready. Type your message below or press Help."
                )
        except NoMatches:
            # If the widget isn't mounted yet, we'll update on the next message
            pass
    
    def compose(self) -> ComposeResult:
        """Compose the interview UI."""
        yield Header()
        
        with Container(classes="interview-container"):
            # Devussy Banner loaded from DEVUSSYLOGO.MD
            yield Static(self._logo_text or "DEVUSSY", classes="banner")

            yield Static("🤖 DevUssY Interactive Interview", classes="status-bar")

            # Conversation area using a Static widget for compatibility
            yield Static("", id="conversation-log", classes="conversation-area")
            
            with Container(classes="input-area"):
                yield Input(
                    placeholder="Type your message here (or '/done' to finish)...",
                    id="user-input"
                )
                # Add a simple test button to verify input handling works
                yield Button("Test Input", variant="default", id="test-input-btn")
                with Horizontal():
                    yield Button("Send", variant="primary", id="send-btn")
                    yield Button("Done", variant="success", id="done-btn")
                    yield Button("Help", variant="default", id="help-btn")
                    yield Button("Settings", variant="default", id="settings-btn")
                    yield Button("Quit", variant="error", id="quit-btn")
        
        yield Footer()
    
    async def _start_interview(self) -> None:
        """Start the interview with initial message from LLM."""
        try:
            # Get initial message from interview manager
            initial_prompt = self._build_initial_prompt()
            response = await self._get_llm_response(initial_prompt)
            # Don't add assistant message here - streaming already handled it
        except Exception as e:
            self._add_system_message(f"❌ Error starting interview: {e}")
    
    def _build_initial_prompt(self) -> str:
        """Build the initial prompt for the LLM."""
        prompt = "Start a friendly conversation to gather project requirements for a development plan. "
        
        if self.repo_analysis:
            prompt += f"The user is working in a {self.repo_analysis.project_type} project. "
            if self.repo_analysis.dependencies:
                deps = ", ".join(list(self.repo_analysis.dependencies.keys())[:5])
                prompt += f"I can see they're using: {deps}. "
        
        prompt += "Ask about their project naturally, one question at a time."
        return prompt
    
    async def _get_llm_response(self, user_input: str) -> str:
        """Get response from LLM with streaming."""
        try:
            # Add a placeholder for the streaming response
            self.conversation_history.append(("assistant", ""))
            
            # Create streaming callback
            response_parts = []
            
            def stream_callback(token: str) -> None:
                response_parts.append(token)
                # Update the last assistant message in real-time
                partial = "".join(response_parts)
                self.conversation_history[-1] = ("assistant", partial)
                # Call the UI update from the main thread
                self.call_after_refresh(self._update_conversation_display)
            
            # Get streaming response from LLM
            full_response = await self.interview_manager._send_to_llm_streaming(
                user_input, 
                callback=stream_callback
            )
            
            # Ensure the final response is set
            self.conversation_history[-1] = ("assistant", full_response)
            self._update_conversation_display()
            
            return full_response
            
        except Exception as e:
            # Remove the placeholder if there was an error
            if self.conversation_history and self.conversation_history[-1][0] == "assistant":
                self.conversation_history.pop()
            return f"❌ Error getting response: {e}"
    
    def _add_system_message(self, message: str) -> None:
        """Add a system message to the conversation."""
        self.conversation_history.append(("system", message))
        self._update_conversation_display()
    
    def _add_user_message(self, message: str) -> None:
        """Add a user message to the conversation."""
        self.conversation_history.append(("user", message))
        self._update_conversation_display()
    
    def _add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the conversation."""
        self.conversation_history.append(("assistant", message))
        self._update_conversation_display()
    
    def _update_conversation_display(self) -> None:
        """Update the conversation display widget."""
        display = self._conversation_display
        if display is None:
            # Try to resolve it lazily if we don't have it yet
            try:
                display = self.query_one("#conversation-log", Static)
                self._conversation_display = display
            except NoMatches:
                return

        # Build conversation text
        lines: list[str] = []
        for msg_type, content in self.conversation_history:
            if msg_type == "user":
                prefix = "👤 You: "
            elif msg_type == "assistant":
                prefix = "🤖 Assistant: "
            elif msg_type == "system":
                prefix = "🔧 System: "
            else:
                prefix = ""

            lines.append(f"{prefix}{content}" if content else prefix)

        conversation_text = "\n".join(lines) if lines else ""
        display.update(conversation_text)

        # Best-effort scroll to bottom if supported
        try:
            display.scroll_end()
        except Exception:
            pass
    
    # Explicit event wiring for compatibility with different Textual versions
    @on(Input.Submitted)
    def _handle_input_submitted_event(self, event: Input.Submitted) -> None:
        """Route Input.Submitted events to our handler."""
        self.on_input_submitted(event)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        print(f"Debug: on_input_submitted called with: {user_input}")
        if not user_input:
            return
        
        # Clear the input
        event.input.value = ""
        
        # Handle special commands
        if user_input.lower() == "/done":
            self.action_done()
            return
        elif user_input.lower() == "/help":
            self.action_help()
            return
        elif user_input.lower() == "/quit":
            self.action_quit()
            return
        
        # Add user message and get response
        self._add_user_message(user_input)
        asyncio.create_task(self._handle_user_input(user_input))
    
    async def _handle_user_input(self, user_input: str) -> None:
        """Handle user input and get LLM response."""
        print(f"Debug: _handle_user_input called with: {user_input}")
        try:
            print(f"Debug: Getting LLM response...")
            response = await self._get_llm_response(user_input)
            print(f"Debug: Got LLM response: {repr(response[:100])}")
            # Don't add assistant message here - streaming already handled it
            
            # Check if interview should be complete
            if self._should_complete_interview(response):
                await asyncio.sleep(1)  # Brief pause
                self.action_done()
                
        except Exception as e:
            print(f"Debug: Error in _handle_user_input: {e}")
            self._add_system_message(f"❌ Error: {e}")
    
    def _should_complete_interview(self, response: str) -> bool:
        """Check if the interview should be marked as complete."""
        # Look for completion indicators in the response
        completion_indicators = [
            "type '/done' to finalize",
            "ready to create your development plan",
            "have all the information"
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in completion_indicators)
    
    def _handle_input_direct(self, user_input: str) -> None:
        """Handle user input directly without event."""
        print(f"Debug: _handle_input_direct called with: {user_input}")
        # Handle special commands
        if user_input.lower() == "/done":
            self.action_done()
            return
        elif user_input.lower() == "/help":
            self.action_help()
            return
        elif user_input.lower() == "/quit":
            self.action_quit()
            return
        
        # Add user message and get response
        self._add_user_message(user_input)
        asyncio.create_task(self._handle_user_input(user_input))
    
    @on(Button.Pressed)
    def _handle_button_pressed_event(self, event: Button.Pressed) -> None:
        """Route Button.Pressed events to our handler."""
        self.on_button_pressed(event)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        print(f"Debug: Button pressed: {button_id}")
        
        if button_id == "send-btn":
            input_widget = self.query_one("#user-input", Input)
            user_input = input_widget.value.strip()
            if user_input:
                # Clear the input
                input_widget.value = ""
                # Handle the input directly
                self._handle_input_direct(user_input)
        elif button_id == "test-input-btn":
            # Test input handling
            input_widget = self.query_one("#user-input", Input)
            user_input = input_widget.value.strip()
            print(f"Debug: Test button - current input: '{user_input}'")
            self._add_system_message(f"🧪 Test: Current input is '{user_input}'")
        elif button_id == "done-btn":
            self.action_done()
        elif button_id == "help-btn":
            self.action_help()
        elif button_id == "settings-btn":
            self.action_settings()
        elif button_id == "quit-btn":
            self.action_quit()
    
    def action_done(self) -> None:
        """Complete the interview and extract data."""
        if self.interview_complete:
            return
        
        try:
            # Extract interview data
            self.interview_data = self.interview_manager.to_generate_design_inputs()
            self.interview_complete = True
            
            self._add_system_message("✅ Interview complete! Generating development plan...")
            
            # Exit the app with success
            self.exit(self.interview_data)
            
        except Exception as e:
            self._add_system_message(f"❌ Error completing interview: {e}")
    
    def action_help(self) -> None:
        """Show help information."""
        help_text = """
🤖 DevUssY Interview Help:

Commands:
  /done  - Complete the interview and generate plan
  /help  - Show this help message  
  /quit  - Exit the interview

Tips:
  • Answer questions naturally about your project
  • Provide details about technologies, requirements, and goals
  • I'll ask follow-up questions as needed
  • When ready, I'll prompt you to type '/done'

Keyboard Shortcuts:
  Ctrl+C - Quit
  Ctrl+D - Done
  F1     - Help
  F2     - Settings
  Ctrl+S - Settings
  Mouse Wheel - Scroll conversation

Features:
  • Real-time streaming responses
  • Mouse scrolling support
  • Settings panel (F2)
  • Rich conversation history
        """
        self._add_system_message(help_text)
    
    def action_quit(self) -> None:
        """Quit the interview."""
        self._add_system_message("👋 Interview cancelled. Goodbye!")
        self.exit(None)
    
    def action_settings(self) -> None:
        """Show settings panel."""
        self.push_screen(SettingsScreen())


class SettingsScreen(ModalScreen):
    """Interactive settings screen for interview UI."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("s", "save_settings", "Save"),
    ]
    
    def __init__(self):
        super().__init__()
        self.streaming_enabled = True
        self.mouse_enabled = True
        self.verbose_mode = False
    
    def compose(self) -> ComposeResult:
        """Compose settings screen."""
        yield Header()
        
        with Container(classes="settings-panel"):
            yield Static("⚙️ DevUssY Interview Settings", classes="status-bar")
            
            with Vertical():
                yield Static("🎵 Current Configuration:")
                
                # Streaming toggle
                yield Static("Streaming: ✅ Enabled" if self.streaming_enabled else "Streaming: ❌ Disabled")
                yield Button("Toggle Streaming", id="streaming-toggle", variant="default")
                
                # Mouse toggle
                yield Static("Mouse Support: ✅ Enabled" if self.mouse_enabled else "Mouse Support: ❌ Disabled")
                yield Button("Toggle Mouse", id="mouse-toggle", variant="default")
                
                # Verbose toggle
                yield Static("Verbose Mode: ✅ Enabled" if self.verbose_mode else "Verbose Mode: ❌ Disabled")
                yield Button("Toggle Verbose", id="verbose-toggle", variant="default")
                
                yield Static("")
                yield Static("📋 Provider Info:")
                yield Static("• Provider: Requesty AI")
                yield Static("• Model: GPT-5 Mini")
                yield Static("• API: Streaming SSE")
                
                yield Static("")
                yield Static("⌨️ Keyboard Shortcuts:")
                yield Static("• F1: Help")
                yield Static("• F2/Ctrl+S: Settings")
                yield Static("• Ctrl+D: Done/Finish")
                yield Static("• Ctrl+C: Quit")
                yield Static("• Mouse Wheel: Scroll conversation")
                
                yield Static("")
                yield Static("💬 Commands:")
                yield Static("• /done - Finish interview")
                yield Static("• /help - Show help")
                yield Static("• /quit - Exit interview")
                
                yield Static("")
                with Horizontal():
                    yield Button("Save", variant="success", id="save-btn")
                    yield Button("Reset", variant="warning", id="reset-btn")
                    yield Button("Close", variant="primary", id="close-btn")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id
        
        if button_id == "streaming-toggle":
            self.streaming_enabled = not self.streaming_enabled
            # Update the status text
            status_statics = self.query("Static")
            for static in status_statics:
                try:
                    text = str(static.renderable) if hasattr(static, 'renderable') else str(static._nodes[0]) if hasattr(static, '_nodes') and static._nodes else ""
                    if "Streaming:" in text:
                        static.update("Streaming: ✅ Enabled" if self.streaming_enabled else "Streaming: ❌ Disabled")
                        break
                except:
                    continue
        elif button_id == "mouse-toggle":
            self.mouse_enabled = not self.mouse_enabled
            # Update the status text
            status_statics = self.query("Static")
            for static in status_statics:
                try:
                    text = str(static.renderable) if hasattr(static, 'renderable') else str(static._nodes[0]) if hasattr(static, '_nodes') and static._nodes else ""
                    if "Mouse Support:" in text:
                        static.update("Mouse Support: ✅ Enabled" if self.mouse_enabled else "Mouse Support: ❌ Disabled")
                        break
                except:
                    continue
        elif button_id == "verbose-toggle":
            self.verbose_mode = not self.verbose_mode
            # Update the status text
            status_statics = self.query("Static")
            for static in status_statics:
                try:
                    text = str(static.renderable) if hasattr(static, 'renderable') else str(static._nodes[0]) if hasattr(static, '_nodes') and static._nodes else ""
                    if "Verbose Mode:" in text:
                        static.update("Verbose Mode: ✅ Enabled" if self.verbose_mode else "Verbose Mode: ❌ Disabled")
                        break
                except:
                    continue
        elif button_id == "save-btn":
            self.action_save_settings()
        elif button_id == "reset-btn":
            self.action_reset_settings()
        elif button_id == "close-btn":
            self.dismiss()
    
    def action_save_settings(self) -> None:
        """Save settings."""
        # Here you would save to a config file
        self._add_temp_message("✅ Settings saved!")
    
    def action_reset_settings(self) -> None:
        """Reset settings to defaults."""
        self.streaming_enabled = True
        self.mouse_enabled = True
        self.verbose_mode = False
        
        # Update all status text
        status_statics = self.query("Static")
        for static in status_statics:
            try:
                text = str(static.renderable) if hasattr(static, 'renderable') else str(static._nodes[0]) if hasattr(static, '_nodes') and static._nodes else ""
                if "Streaming:" in text:
                    static.update("Streaming: ✅ Enabled")
                elif "Mouse Support:" in text:
                    static.update("Mouse Support: ✅ Enabled")
                elif "Verbose Mode:" in text:
                    static.update("Verbose Mode: ❌ Disabled")
            except:
                continue
        
        self._add_temp_message("🔄 Settings reset to defaults")
    
    def _add_temp_message(self, message: str) -> None:
        """Add a temporary message that disappears after 2 seconds."""
        # This would require a more complex implementation with timers
        # For now, just print to console
        print(message)


async def run_interview_ui(
    config: AppConfig,
    repo_analysis: Optional[RepoAnalysis] = None,
) -> Optional[Dict[str, Any]]:
    """Run the interview UI and return collected data.
    
    Args:
        config: Application configuration
        repo_analysis: Optional repository analysis for context
        
    Returns:
        Interview data dictionary or None if cancelled
    """
    # Create interview manager
    interview_manager = LLMInterviewManager(
        config=config,
        verbose=False,
        repo_analysis=repo_analysis
    )
    
    # Create and run the interview UI
    app = InterviewScreen(interview_manager, repo_analysis)
    
    try:
        interview_data = await app.run_async()
        return interview_data
    except Exception as e:
        print(f"❌ Interview UI error: {e}")
        return None


if __name__ == "__main__":
    # Demo mode
    import asyncio
    from ..config import load_config
    
    async def demo():
        config = load_config()
        config.streaming_enabled = True
        data = await run_interview_ui(config)
        if data:
            print("✅ Interview completed successfully!")
            print(f"Project: {data.get('name', 'Unknown')}")
        else:
            print("❌ Interview was cancelled")
    
    asyncio.run(demo())
