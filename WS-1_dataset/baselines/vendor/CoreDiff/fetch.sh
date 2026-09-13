#!/usr/bin/env bash
# Fetch CoreDiff from upstream into this directory. See README.md for why it is
# not vendored. Optional argument: a commit SHA to pin.
set -euo pipefail
cd "$(dirname "$0")"
UPSTREAM=https://github.com/qgao21/CoreDiff
PIN="${1:-}"

if [ -d models ]; then echo "already present; delete models/ to refetch"; exit 0; fi
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
git clone --quiet "$UPSTREAM" "$tmp/CoreDiff"
[ -n "$PIN" ] && git -C "$tmp/CoreDiff" checkout --quiet "$PIN"
SHA=$(git -C "$tmp/CoreDiff" rev-parse HEAD)
rm -rf "$tmp/CoreDiff/.git"
cp -r "$tmp/CoreDiff/." .
echo "fetched $UPSTREAM at $SHA"
echo "record that SHA with any results you produce; upstream has no licence file,"
echo "so do not commit this tree back into a public repository."
