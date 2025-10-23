"""Remove is_flag from all boolean flags."""
import re

with open('src/cli.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Remove is_flag=True from boolean flags
code = re.sub(r'typer\.Option\("(--[^"]+)", is_flag=True,', r'typer.Option("\1",', code)

with open('src/cli.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Removed is_flag=True from all boolean flags")
