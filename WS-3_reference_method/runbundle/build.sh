#!/usr/bin/env bash
# Build the WS-3 reference-reconstruction RunBundle image.
# Run from the REPO ROOT (the bundle installs three in-repo packages):
#   bash WS-3_reference_method/runbundle/build.sh [tag]
set -euo pipefail

TAG="${1:-pwm-ldct-recon:0.1.0}"
ROOT="$(git rev-parse --show-toplevel)"

cd "$ROOT"
docker build -f WS-3_reference_method/runbundle/Dockerfile -t "$TAG" .

echo
echo "Built $TAG. Self-test (no GPU/data):"
echo "  docker run --rm $TAG"
echo "Real reproduction (GPU + authorised WS-1 data):"
echo "  docker run --rm -v /path/to/weights:/weights -v /path/to/ws1:/data $TAG \\"
echo "    --emit --weights /weights/ensemble.pt --data-root /data --results /tmp/results.json"
