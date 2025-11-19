import sys
import os
from pathlib import Path

def setup_path():
    """Add the project root to sys.path to allow importing from src."""
    # Get the directory containing this file (api/)
    current_dir = Path(__file__).parent.resolve()
    
    # Go up two levels to reach the project root (devussy-testing/)
    # api/ -> devussy-web/ -> devussy-testing/
    project_root = current_dir.parent.parent
    
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
        print(f"Added {project_root} to sys.path")
