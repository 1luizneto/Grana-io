#!/bin/sh
# Roda a suíte completa do Grana.io com um único comando (constituição, Princípio IV; RNF-05):
# backend (pytest) e interface (Vitest), ambos dentro do Docker.
#   sh testar.sh
set -e

echo "== Backend (pytest) =="
docker compose run --rm backend pytest

echo "== Interface (Vitest) =="
docker compose run --rm frontend npm test

echo "Backend e interface: todos os testes passaram."
