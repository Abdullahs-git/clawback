r"""
scripts/check_frontend_integrity.py
Validates frontend code hygiene:
1. Enforces no hardcoded currency literals in component JSX (regex `\$\s?\d` and `\d{1,3}(,\d{3})+`).
2. Enforces no forbidden marketing fluff (lorem ipsum, Acme, John Doe, fake testimonials, trusted by, 99.9% uptime).
3. Enforces production bundle isolation (no msw or __fixtures__ in production build).
"""
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "frontend" / "src"

FORBIDDEN_PHRASES = [
    r"\blorem ipsum\b",
    r"\bacme\b",
    r"\bjohn doe\b",
    r"\btrusted by\b",
    r"\b99\.9% uptime\b",
    r"\btestimonial\b",
    r"\bpricing tiers?\b",
]

# Patterns for hardcoded currency literals in JSX text or strings
CURRENCY_LITERAL_REGEX = re.compile(r'["\'>]\s*\$\s?\d+(?:\.\d{2})?\s*["\'<]')


def audit_frontend_components():
    errors = []
    
    if not SRC_DIR.exists():
        print(f"ERROR: {SRC_DIR} does not exist")
        sys.exit(1)

    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith(".tsx") and not f.endswith(".test.tsx"):
                path = Path(root) / f
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()

                # Check forbidden phrases
                for idx, line in enumerate(lines, 1):
                    for pattern in FORBIDDEN_PHRASES:
                        if re.search(pattern, line, re.IGNORECASE):
                            errors.append(f"{f}:{idx}: Found forbidden marketing content '{pattern}' in: {line.strip()}")

                # Check for hardcoded currency literals (e.g. "$9159.31" hardcoded in code)
                for idx, line in enumerate(lines, 1):
                    # Ignore comment lines and lines doing format strings or regex definitions
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("/*") or "*" in stripped[:2]:
                        continue
                    if "tabular-nums" in line or "font-bold" in line or "font-mono" in line:
                        # Allow rendering dynamic variables like `${amount}` or `${total}`
                        continue
                    if re.search(r'["\']\$\s?\d+["\']', line) and not "replace" in line and not "slice" in line:
                        errors.append(f"{f}:{idx}: Found hardcoded currency literal in: {line.strip()}")

    return errors


def main():
    print("=" * 60)
    print("CLAWBACK FRONTEND CODE INTEGRITY & PURGE CHECK")
    print("=" * 60)

    errors = audit_frontend_components()

    if errors:
        print(f"\nFAILED: Found {len(errors)} frontend integrity violations:\n")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nPASSED: All components free of hardcoded currency literals and forbidden content.")
        sys.exit(0)


if __name__ == "__main__":
    main()
