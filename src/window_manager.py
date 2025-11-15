"""Window management system for coordinating multiple terminal processes.

This module provides functionality to launch and coordinate multiple terminal
windows for the interactive DevUssY workflow, separating interview and
phase generation into different windows.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import threading

from .llm_interview import LLMInterviewManager
from .pipeline.compose import PipelineOrchestrator
from .terminal.phase_generator import TerminalPhaseGenerator
from .models import DevPlan, ProjectDesign
from .config import AppConfig, load_config
from .clients.factory import create_llm_client
from .concurrency import ConcurrencyManager
from .file_manager import FileManager
from .state_manager import StateManager
from .progress_reporter import PipelineProgressReporter

logger = logging.getLogger(__name__)


class WindowManager:
    """Manages multiple terminal windows for interactive DevUssY workflow."""
    
    def __init__(self, config: AppConfig):
        """Initialize window manager with configuration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.temp_dir = Path(tempfile.mkdtemp(prefix="devussy_interactive_"))
        self.devplan_file = self.temp_dir / "devplan.json"
        self.interview_log = self.temp_dir / "interview.log"
        self.phase_generation_log = self.temp_dir / "phase_generation.log"
        
        # Process tracking
        self.interview_process: Optional[subprocess.Popen] = None
        self.terminal_process: Optional[subprocess.Popen] = None
        
        logger.info(f"Window manager initialized with temp dir: {self.temp_dir}")
    
    def launch_interview_window(self) -> None:
        """Launch the LLM interview in a separate terminal window."""
        logger.info("Launching interview window...")
        
        # Create interview script
        interview_script = self._create_interview_script()
        
        # Determine terminal command based on OS
        if sys.platform == "win32":
            # Windows: use 'start' to open new terminal
            cmd = [
                "start", "cmd", "/k", 
                "python", str(interview_script),
                str(self.devplan_file),
                str(self.interview_log)
            ]
        elif sys.platform == "darwin":
            # macOS: use osascript to open new Terminal
            script = f'''
            tell application "Terminal"
                do script "python '{interview_script}' '{self.devplan_file}' '{self.interview_log}'"
                activate
            end tell
            '''
            cmd = ["osascript", "-e", script]
        else:
            # Linux: try common terminal emulators
            terminals = ["gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
            terminal_cmd = None
            
            for term in terminals:
                if shutil.which(term):
                    if term == "gnome-terminal":
                        terminal_cmd = [term, "--", "python", str(interview_script), str(self.devplan_file), str(self.interview_log)]
                    elif term == "konsole":
                        terminal_cmd = [term, "-e", "python", str(interview_script), str(self.devplan_file), str(self.interview_log)]
                    else:
                        terminal_cmd = [term, "-e", "python", str(interview_script), str(self.devplan_file), str(self.interview_log)]
                    break
            
            if not terminal_cmd:
                raise RuntimeError("No suitable terminal emulator found")
            
            cmd = terminal_cmd
        
        try:
            self.interview_process = subprocess.Popen(cmd, shell=(sys.platform == "win32"))
            logger.info(f"Interview window launched with PID: {self.interview_process.pid}")
        except Exception as e:
            logger.error(f"Failed to launch interview window: {e}")
            raise
    
    def launch_terminal_ui_window(self) -> None:
        """Launch the terminal UI for phase generation in a separate window."""
        logger.info("Launching terminal UI window...")
        
        # Create terminal UI script
        terminal_script = self._create_terminal_script()
        
        # Determine terminal command based on OS
        if sys.platform == "win32":
            cmd = [
                "start", "cmd", "/k",
                "python", str(terminal_script),
                str(self.devplan_file),
                str(self.phase_generation_log)
            ]
        elif sys.platform == "darwin":
            script = f'''
            tell application "Terminal"
                do script "python '{terminal_script}' '{self.devplan_file}' '{self.phase_generation_log}'"
                activate
            end tell
            '''
            cmd = ["osascript", "-e", script]
        else:
            terminals = ["gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
            terminal_cmd = None
            
            for term in terminals:
                if shutil.which(term):
                    if term == "gnome-terminal":
                        terminal_cmd = [term, "--", "python", str(terminal_script), str(self.devplan_file), str(self.phase_generation_log)]
                    elif term == "konsole":
                        terminal_cmd = [term, "-e", "python", str(terminal_script), str(self.devplan_file), str(self.phase_generation_log)]
                    else:
                        terminal_cmd = [term, "-e", "python", str(terminal_script), str(self.devplan_file), str(self.phase_generation_log)]
                    break
            
            if not terminal_cmd:
                raise RuntimeError("No suitable terminal emulator found")
            
            cmd = terminal_cmd
        
        try:
            self.terminal_process = subprocess.Popen(cmd, shell=(sys.platform == "win32"))
            logger.info(f"Terminal UI window launched with PID: {self.terminal_process.pid}")
        except Exception as e:
            logger.error(f"Failed to launch terminal UI window: {e}")
            raise
    
    def wait_for_devplan(self, timeout: int = 600) -> bool:
        """Wait for the devplan file to be created by the interview process.
        
        Args:
            timeout: Maximum time to wait in seconds (default: 10 minutes)
            
        Returns:
            True if devplan was created, False if timeout
        """
        logger.info(f"Waiting for devplan file at: {self.devplan_file}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.devplan_file.exists() and self.devplan_file.stat().st_size > 0:
                # Verify the file contains valid JSON
                try:
                    with open(self.devplan_file, 'r', encoding='utf-8') as f:
                        json.load(f)  # Validate JSON
                    logger.info("Devplan file detected and validated!")
                    return True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logger.info("Devplan file found but not yet complete, waiting...")
            time.sleep(2)  # Check every 2 seconds
        
        logger.warning("Timeout waiting for devplan file")
        return False
    
    def run_interactive_session(self) -> None:
        """Run the complete interactive session with both windows."""
        try:
            print("[ROCKET] Starting DevUssY Interactive Mode")
            print("=" * 50)
            print("This will open two terminal windows:")
            print("1. Interview window - For gathering project requirements")
            print("2. Phase Generation window - For generating development phases")
            print("=" * 50)
            
            input("Press Enter to launch the interview window...")
            
            # Launch interview window
            self.launch_interview_window()
            
            print("✓ Interview window launched")
            print("Waiting for interview to complete and devplan to be generated...")
            
            # Wait for devplan to be created
            if self.wait_for_devplan():
                print("✓ Interview completed successfully!")
                input("Press Enter to launch the phase generation window...")
                
                # Launch terminal UI window
                self.launch_terminal_ui_window()
                
                print("✓ Phase generation window launched")
                print("=" * 50)
                print("Both windows are now running:")
                print("- Interview window: Project requirements gathering")
                print("- Phase Generation window: Real-time phase generation")
                print("=" * 50)
                print("You can close this coordinator window anytime.")
                print("The temporary files are stored in:")
                print(f"  {self.temp_dir}")
                
                # Wait for both processes to complete
                try:
                    if self.interview_process:
                        self.interview_process.wait()
                    if self.terminal_process:
                        self.terminal_process.wait()
                except KeyboardInterrupt:
                    print("\nShutting down...")
                    self.cleanup()
                
            else:
                print("[ERROR] Interview timed out or failed to generate devplan")
                
        except Exception as e:
            logger.error(f"Error in interactive session: {e}")
            print(f"[ERROR] Error: {e}")
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up processes and temporary files."""
        logger.info("Cleaning up window manager...")
        
        # Terminate processes
        if self.interview_process:
            try:
                self.interview_process.terminate()
                self.interview_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.interview_process.kill()
            except Exception as e:
                logger.warning(f"Error terminating interview process: {e}")
        
        if self.terminal_process:
            try:
                self.terminal_process.terminate()
                self.terminal_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.terminal_process.kill()
            except Exception as e:
                logger.warning(f"Error terminating terminal process: {e}")
        
        # Clean up temp directory (with retry for file locks)
        for attempt in range(3):
            try:
                import shutil
                if self.temp_dir.exists():
                    shutil.rmtree(self.temp_dir)
                    logger.info(f"Cleaned up temp directory: {self.temp_dir}")
                break
            except Exception as e:
                if attempt == 2:  # Last attempt
                    logger.warning(f"Error cleaning up temp directory after 3 attempts: {e}")
                    logger.info(f"Temp directory left for manual cleanup: {self.temp_dir}")
                else:
                    logger.warning(f"Cleanup attempt {attempt + 1} failed, retrying in 2 seconds...")
                    time.sleep(2)
    
    def _create_interview_script(self) -> Path:
        """Create a standalone Python script for running the interview."""
        # Get the actual project directory (where this script is running from)
        project_dir = Path(__file__).parent.parent  # Goes up from src/window_manager.py to project root
        src_dir = project_dir / "src"
        
        script_content = f'''#!/usr/bin/env python3
"""Standalone interview script for interactive mode."""

import sys
import json
import logging
from pathlib import Path

# Add the actual project src directory to Python path
sys.path.insert(0, r"{src_dir}")

from src.llm_interview import LLMInterviewManager
from src.pipeline.compose import PipelineOrchestrator
from src.config import AppConfig, load_config
from src.interview import RepoAnalysis, RepositoryAnalyzer

def main():
    if len(sys.argv) != 3:
        print("Usage: python interview_script.py <devplan_output_file> <log_file>")
        sys.exit(1)
    
    devplan_file = Path(sys.argv[1])
    log_file = Path(sys.argv[2])
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Load configuration
        config = load_config()
        
        # Enable streaming for real-time feedback during generation
        config.streaming_enabled = True
        
        # Analyze current repository if in one
        repo_analysis = None
        try:
            analyzer = RepositoryAnalyzer()
            repo_analysis = analyzer.analyze_repository(Path.cwd())
        except Exception as e:
            logging.warning(f"Repository analysis failed: {{e}}")
        
        # Run interview
        interview_manager = LLMInterviewManager(
            config=config,
            verbose=False,
            repo_analysis=repo_analysis
        )
        
        print("🎵 DevUssY Interactive Interview")
        print("=" * 40)
        print("Answer the questions to gather project requirements.")
        print("Type '/done' when finished to generate the development plan.")
        print("=" * 40)
        
        # Run the interview
        interview_data = interview_manager.run()
        
        if not interview_data:
            print("[ERROR] No data collected from interview")
            sys.exit(1)
        
        # Convert to design inputs
        design_inputs = interview_manager.to_generate_design_inputs()
        
        # Create orchestrator to generate devplan
        from src.cli import _create_orchestrator
        orchestrator = _create_orchestrator(config)
        
        # Generate basic devplan structure only (no detailed phases)
        import asyncio
        print("📝 Generating project design with real-time streaming...")
        
        design = await orchestrator.project_design_gen.generate(
            project_name=design_inputs["name"],
            languages=design_inputs["languages"].split(","),
            requirements=design_inputs["requirements"],
            frameworks=design_inputs.get("frameworks", "").split(",") if design_inputs.get("frameworks") else None,
            apis=design_inputs.get("apis", "").split(",") if design_inputs.get("apis") else None,
        )
        print("[OK] Project design generated!")
        
        print("[LIST] Creating basic development plan structure with real-time streaming...")
        # Generate only basic devplan structure (this is fast)
        devplan = await orchestrator.basic_devplan_gen.generate(design)
        print("[OK] Development plan structure created!")
        
        # Save devplan immediately for the terminal UI to pick up
        devplan_file.parent.mkdir(parents=True, exist_ok=True)
        with open(devplan_file, 'w', encoding='utf-8') as f:
            json.dump(devplan.model_dump(), f, indent=2)
        
        print(f"[OK] Development plan saved to: {{devplan_file}}")
        print("[OK] Interview completed successfully!")
        print("[ROCKET] The phase generation window will open automatically and stream all phases in real-time.")
        print("You can close this interview window after the phase generation window appears.")
        
        # Keep window open for user to see results
        input("\\nPress Enter to close this window...")
        
    except Exception as e:
        logging.error(f"Interview failed: {{e}}", exc_info=True)
        print(f"[ERROR] Interview failed: {{e}}")
        input("\\nPress Enter to close this window...")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        script_file = self.temp_dir / "interview_script.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        if sys.platform != "win32":
            script_file.chmod(0o755)
        
        return script_file
    
    def _create_terminal_script(self) -> Path:
        """Create a standalone Python script for running the terminal UI."""
        # Get the actual project directory (where this script is running from)
        project_dir = Path(__file__).parent.parent  # Goes up from src/window_manager.py to project root
        src_dir = project_dir / "src"
        
        script_content = f'''#!/usr/bin/env python3
"""Standalone terminal UI script for interactive mode."""

import sys
import json
import logging
from pathlib import Path

# Add the actual project src directory to Python path
sys.path.insert(0, r"{src_dir}")

from src.terminal.terminal_ui import run_terminal_ui
from src.terminal.phase_generator import TerminalPhaseGenerator
from src.models import DevPlan
from src.config import AppConfig, load_config

def main():
    if len(sys.argv) != 3:
        print("Usage: python terminal_script.py <devplan_file> <log_file>")
        sys.exit(1)
    
    devplan_file = Path(sys.argv[1])
    log_file = Path(sys.argv[2])
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Wait for devplan file to be available
        print("🎼 DevUssY Phase Generation Terminal")
        print("=" * 40)
        print(f"Waiting for development plan at: {{devplan_file}}")
        print("This should appear automatically after the interview completes...")
        
        import time
        timeout = 120  # Wait up to 2 minutes
        start_time = time.time()
        
        while True:
            # Check if file exists and has content
            if devplan_file.exists():
                file_size = devplan_file.stat().st_size
                print(f"[FOLDER] Devplan file found! Size: {{file_size}} bytes")
                
                if file_size > 0:
                    # Try to read and validate the JSON
                    try:
                        with open(devplan_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"📖 File content preview: {{content[:100]}}...")
                            json.load(f)  # Validate JSON
                        print("[OK] Development plan file is ready!")
                        break
                    except json.JSONDecodeError as e:
                        print(f"[WARN] File found but JSON not yet complete: {{e}}")
                        print("   Waiting for interview to finish writing...")
                    except Exception as e:
                        print(f"[WARN] Error reading file: {{e}}")
                else:
                    print("[WARN] File exists but is empty, waiting...")
            else:
                print(f"⏳ Still waiting... (elapsed: {{int(time.time() - start_time)}}s)")
            
            # Check timeout
            if time.time() - start_time > timeout:
                print(f"[ERROR] Timeout waiting for development plan after {{timeout}} seconds")
                print(f"   Expected file: {{devplan_file}}")
                print(f"   File exists: {{devplan_file.exists()}}")
                if devplan_file.exists():
                    print(f"   File size: {{devplan_file.stat().st_size}} bytes")
                sys.exit(1)
            
            time.sleep(2)  # Check every 2 seconds
        
        print("✓ Development plan detected!")
        
        # Load configuration
        config = load_config()
        
        # Enable streaming for real-time phase generation
        config.streaming_enabled = True
        
        # Load devplan
        with open(devplan_file, 'r', encoding='utf-8') as f:
            devplan_data = json.load(f)
            devplan = DevPlan.model_validate(devplan_data)
        
        print(f"✓ Development plan loaded: {{devplan.project_name}}")
        print(f"  Phases: {{len(devplan.phases)}} configured")
        
        # Create phase generator with proper dependencies
        from src.clients.factory import create_llm_client
        from src.terminal.phase_state import PhaseStateManager
        
        llm_client = create_llm_client(config)
        state_manager = PhaseStateManager(["plan", "design", "implement", "test", "review"])
        phase_generator = TerminalPhaseGenerator(llm_client, state_manager)
        
        # Launch terminal UI with streaming phase generation
        print("[ROCKET] Starting real-time phase generation...")
        print("Watch as each phase is generated and streamed live!")
        run_terminal_ui(
            phase_names=["plan", "design", "implement", "test", "review"],
            phase_generator=phase_generator,
            devplan=devplan
        )
        
    except Exception as e:
        logging.error(f"Terminal UI failed: {{e}}", exc_info=True)
        print(f"[ERROR] Terminal UI failed: {{e}}")
        input("\\nPress Enter to close this window...")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        script_file = self.temp_dir / "terminal_script.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        if sys.platform != "win32":
            script_file.chmod(0o755)
        
        return script_file


def launch_interactive_mode(config: AppConfig) -> None:
    """Launch the complete interactive mode with window management.
    
    Args:
        config: Application configuration
    """
    window_manager = WindowManager(config)
    
    try:
        window_manager.run_interactive_session()
    finally:
        window_manager.cleanup()
