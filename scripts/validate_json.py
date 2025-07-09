#!/usr/bin/env python
# scripts/validate_json.py

import sys
import json

def main():
    count = 0
    for line in sys.stdin:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"INVALID JSON on line {count+1}: {e}", file=sys.stderr)
            sys.exit(1)
        count += 1
    print(f"All {count} JSON lines valid.")

if __name__ == "__main__":
    main()
