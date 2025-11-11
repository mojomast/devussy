#!/usr/bin/env python3
"""Build script for generating API documentation using pdoc.

This script generates API documentation for the DevPlan Orchestrator project
and outputs it to the docs/api/ directory.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    """Generate API documentation using pdoc."""
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    src_dir = project_root / "src"
    docs_dir = project_root / "docs"
    api_docs_dir = docs_dir / "api"

    print("🔧 Building API Documentation")
    print(f"Project root: {project_root}")
    print(f"Source directory: {src_dir}")
    print(f"API docs output: {api_docs_dir}")
    print("-" * 50)

    # Ensure source directory exists
    if not src_dir.exists():
        print(f"❌ Error: Source directory not found: {src_dir}")
        sys.exit(1)

    # Create docs directory if it doesn't exist
    docs_dir.mkdir(exist_ok=True)

    # Clean existing API docs
    if api_docs_dir.exists():
        print(f"🧹 Cleaning existing API docs: {api_docs_dir}")
        shutil.rmtree(api_docs_dir)

    # Check if pdoc is available
    try:
        result = subprocess.run(
            ["pdoc", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ pdoc version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: pdoc is not installed or not in PATH")
        print("Install with: pip install pdoc")
        sys.exit(1)

    # Change to project root to ensure proper imports
    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Build API documentation
        print("📚 Generating API documentation...")

        # pdoc command to generate HTML documentation
        cmd = [
            "pdoc",
            "--html",  # Generate HTML output
            "--output-dir",
            str(docs_dir),  # Output to docs/
            "--force",  # Overwrite existing files
            "--config",
            "show_source_code=True",  # Include source code
            "src",  # Document the src package
        ]

        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            # Move generated docs from docs/src/ to docs/api/
            generated_dir = docs_dir / "src"
            if generated_dir.exists():
                generated_dir.rename(api_docs_dir)
                print(f"✅ API documentation generated successfully in {api_docs_dir}")

                # List generated files
                print("\n📄 Generated files:")
                for html_file in api_docs_dir.rglob("*.html"):
                    relative_path = html_file.relative_to(api_docs_dir)
                    print(f"  - {relative_path}")

            else:
                print("⚠️  Warning: Expected generated directory not found")
                print("Documentation may have been generated in a different location")
        else:
            print("❌ Error generating documentation:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            sys.exit(1)

    finally:
        # Restore original working directory
        os.chdir(original_cwd)

    # Create a simple index.html for the API docs
    create_api_index(api_docs_dir)

    print("\n🎉 API documentation build complete!")
    print(f"📖 Open {api_docs_dir / 'index.html'} in your browser to view the docs")


def create_api_index(api_docs_dir: Path):
    """Create a simple index.html for the API documentation.

    Args:
        api_docs_dir: Path to the API documentation directory
    """
    if not api_docs_dir.exists():
        return

    # Find the main module HTML file
    main_html = api_docs_dir / "index.html"
    src_html = None

    # Look for main entry point
    for html_file in api_docs_dir.glob("*.html"):
        if html_file.name in ["src.html", "index.html"]:
            src_html = html_file
            break

    # If we found a main HTML file and no index exists, create a redirect
    if src_html and not main_html.exists():
        index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>DevPlan Orchestrator API Documentation</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url=./{src_html.name}">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }}
        .logo {{
            font-size: 2em;
            margin-bottom: 20px;
        }}
        .redirect-link {{
            display: inline-block;
            background: #007acc;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 20px;
        }}
        .redirect-link:hover {{
            background: #005999;
        }}
    </style>
</head>
<body>
    <div class="logo">🚀</div>
    <h1>DevPlan Orchestrator</h1>
    <h2>API Documentation</h2>
    <p>Redirecting to API documentation...</p>
    <p>If you are not redirected automatically,
       <a href="./{src_html.name}" class="redirect-link">
         click here to view the documentation</a>
    </p>
    <script>
        // Redirect after 1 second if meta refresh doesn't work
        setTimeout(function() {{
            window.location.href = './{src_html.name}';
        }}, 1000);
    </script>
</body>
</html>"""

        main_html.write_text(index_content, encoding="utf-8")
        print(f"📝 Created API index: {main_html}")


if __name__ == "__main__":
    main()
