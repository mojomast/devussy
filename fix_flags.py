"""Update all boolean flags to use is_flag=True."""
import re

with open('src/cli.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace --flag/--no-flag with --flag, is_flag=True
pattern = r'bool, typer\.Option\("(--[^/"]+)/--no-[^"]+",'
replacement = r'bool, typer.Option("\1", is_flag=True,'

code = re.sub(pattern, replacement, code)

with open('src/cli.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated all boolean flags to use is_flag=True")
