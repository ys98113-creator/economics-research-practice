#!/bin/bash
# Auto-save: commits and pushes all changes to GitHub
cd "$(dirname "$0")"
git add -A
git diff --cached --quiet && echo "Nothing new to save." && exit 0
git commit -m "auto-save: $(date '+%Y-%m-%d %H:%M')"
git push origin main
echo "Saved to GitHub."
