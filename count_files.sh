#!/bin/bash

echo "🔥 DEVIL TRADING AGENT - FILE COUNT REPORT"
echo "=========================================="
echo ""

echo "📁 MAIN FOLDERS:"
for dir in analytics ml execution strategies portfolio bridge examples backtest; do
    if [ -d "$dir" ]; then
        py_count=$(find "$dir" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
        total_count=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo "  $dir: $py_count Python files, $total_count total files"
    fi
done

echo ""
echo "📊 TOTAL SUMMARY:"
echo "  Total Python files: $(find . -name '*.py' -not -path '*/venv/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' 2>/dev/null | wc -l | tr -d ' ')"
echo "  Total files (all): $(find . -type f -not -path '*/venv/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' 2>/dev/null | wc -l | tr -d ' ')"
echo "  Total folders: $(find . -type d -not -path '*/venv/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' 2>/dev/null | wc -l | tr -d ' ')"

echo ""
echo "📦 GITHUB UPLOADED:"
echo "  Files in repo: $(git ls-tree -r main --name-only 2>/dev/null | wc -l | tr -d ' ')"

echo ""
echo "⚠️  IGNORED FILES (not on GitHub):"
echo "  .env files: $(find . -name '.env' -not -path '*/venv/*' 2>/dev/null | wc -l | tr -d ' ')"
echo "  .db files: $(find . -name '*.db' -not -path '*/venv/*' 2>/dev/null | wc -l | tr -d ' ')"
echo "  .log files: $(find . -name '*.log' -not -path '*/venv/*' 2>/dev/null | wc -l | tr -d ' ')"

echo ""
echo "=========================================="
