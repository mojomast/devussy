"""Find all typer.Option with potential secondary flags."""
import re

with open('src/cli.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Find all Option declarations
pattern = r'typer\.Option\(([^)]+)\)'
matches = re.findall(pattern, code)

print("Checking all typer.Option declarations for secondary flags...")
print("=" * 60)

for i, match in enumerate(matches, 1):
    # Count quoted strings in the match
    quoted_strings = re.findall(r'"([^"]+)"', match)
    
    # If there are multiple strings and the first two look like flags
    if len(quoted_strings) >= 2:
        first = quoted_strings[0]
        second = quoted_strings[1]
        
        # Check if they're both flags (start with --)
        if first.startswith('--') and second.startswith('-'):
            # Check if this is likely a boolean (has bool type nearby)
            lines_before = code[:code.find(match)].split('\n')
            context = '\n'.join(lines_before[-5:])
            
            is_bool = 'bool,' in context or 'bool ' in context
            
            print(f"\n{i}. Found flags: {first}, {second}")
            print(f"   Boolean: {is_bool}")
            if not is_bool:
                print(f"   ⚠️  NON-BOOLEAN WITH SECONDARY FLAG!")
                print(f"   Context: {context[-100:]}")

print("\n" + "=" * 60)
print("Search complete!")
