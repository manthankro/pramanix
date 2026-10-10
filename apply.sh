#!/usr/bin/env bash
# Usage: ./apply.sh /path/to/your/pramanix/clone
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
REPO="${1:?usage: ./apply.sh /path/to/pramanix}"
cd "$REPO"
[ -f pyproject.toml ] && [ -d app ] || { echo "Not a Pramanix repo root"; exit 1; }

git switch -c feature/gemini-github-chat 2>/dev/null || git switch feature/gemini-github-chat
cp "$SRC"/app/*.py app/
mkdir -p tests && cp "$SRC"/tests/*.py tests/
[ -f .env.example ] || cp "$SRC/.env.example" .env.example
mkdir -p frontend/src/components
if [ ! -f frontend/package.json ]; then
  echo "NOTE: frontend/ has no Vite project yet. Run:  npm create vite@latest frontend -- --template react-ts"
fi
cp "$SRC"/frontend/src/api.ts "$SRC"/frontend/src/App.tsx "$SRC"/frontend/src/styles.css frontend/src/
cp "$SRC"/frontend/src/components/*.tsx frontend/src/components/
[ -f frontend/.env.local ] || cp "$SRC/frontend/.env.local.example" frontend/.env.local

echo
echo "Applied. Still do by hand:"
echo " 1. Merge merge/pyproject.additions.toml into pyproject.toml, then: pip install -e \".[dev]\""
echo " 2. Append merge/gitignore.additions to .gitignore; create .env from .env.example"
echo " 3. In frontend/src/main.tsx use: import './styles.css' and delete index.css/App.css imports"
echo " 4. Compare merge/ci.reference.yml, Dockerfile.reference, docker-compose.reference.yml with yours"
echo " 5. Run: ruff format . && ruff check . && mypy app/ && pytest"
