"""Test regex patterns for phase parsing."""

import re

# Test strings that might come from LLM
test_strings = [
    "**Phase 1: Project Initialization**",
    "Phase 1: Project Initialization",
    "## Phase 1: Project Initialization",
    "**Phase 1 - Project Initialization**",
    "Phase 1 - Project Initialization",
    "1. Project Initialization",
    "## 1. Project Initialization",
]

# Current pattern from code
pattern1 = re.compile(
    r"^(?:#{1,6}\s*)?\*{0,2}\s*Phase\s+0*(\d+)\s*[:\-–—]?\s*(.+?)(?:\*{0,2})?$",
    re.IGNORECASE,
)

pattern2 = re.compile(r"^(?:#{1,6}\s*)?(\d+)\s*[\.)]\s*(.+)$", re.IGNORECASE)

print("Testing Pattern 1 (Phase N: Title):")
print("=" * 60)
for test in test_strings:
    match = pattern1.match(test)
    if match:
        print(f"✓ '{test}'")
        print(f"  -> Phase {match.group(1)}: {match.group(2)}")
    else:
        print(f"✗ '{test}'")
print()

print("Testing Pattern 2 (N. Title):")
print("=" * 60)
for test in test_strings:
    match = pattern2.match(test)
    if match:
        print(f"✓ '{test}'")
        print(f"  -> Phase {match.group(1)}: {match.group(2)}")
    else:
        print(f"✗ '{test}'")
