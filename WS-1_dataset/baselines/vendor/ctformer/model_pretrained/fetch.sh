#!/usr/bin/env bash
# Fetch CTformer's pretrained weights from the authors' repository and verify
# them against the bytes this project used. See README.md for why they are
# fetched rather than mirrored.
set -euo pipefail
cd "$(dirname "$0")"
BASE=https://github.com/wdayang/CTformer/raw/main/model_pretrained
EXPECT_CKPT=1d9a459b0876582af60f612cdcc239afd856320fda7b69f516b9cea497b4bfb4
EXPECT_LOSS=67d7de15894da7a58cb1dff0a830ee9c3cbe43f290a4c432aeb978b92f59ff37

fetch_one() {  # name expected_sha
  local n=$1 want=$2
  if [ -f "$n" ]; then
    local have; have=$(sha256sum "$n" | cut -d' ' -f1)
    if [ "$have" = "$want" ]; then echo "  $n already present and verified"; return 0; fi
    echo "  $n present but hash differs; move it aside first" >&2; return 1
  fi
  echo "  fetching $n ..."
  curl -fsSL "$BASE/$n" -o "$n.part"
  local have; have=$(sha256sum "$n.part" | cut -d' ' -f1)
  if [ "$have" != "$want" ]; then
    rm -f "$n.part"
    echo "  FAILED: $n hash mismatch" >&2
    echo "    expected $want" >&2
    echo "    got      $have" >&2
    echo "  Upstream may have retrained. The v0.5 CTformer numbers are tied to the" >&2
    echo "  expected hash; report the difference rather than updating it." >&2
    return 1
  fi
  mv "$n.part" "$n"; echo "  $n verified"
}

fetch_one T2T_vit_530000iter.ckpt "$EXPECT_CKPT"
fetch_one loss_530000_iter.npy    "$EXPECT_LOSS"
echo "done."
