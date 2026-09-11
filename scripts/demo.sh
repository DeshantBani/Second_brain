#!/usr/bin/env bash
# Convenience wrapper around `make demo` - resets the stack, reseeds the demo corpus,
# and opens the app. Run from the repo root: ./scripts/demo.sh
set -e
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found - copying .env.example. Add your OPENAI_API_KEY before continuing." >&2
  cp .env.example .env
  exit 1
fi

make demo
