#!/usr/bin/env bash
# PREPARED, NOT APPLIED. Run this to stop mirroring CTformer's pretrained
# weights and fetch them from the authors' repository instead.
#
# Why you might: the weights are CTformer trained on the 2016 NIH-AAPM-Mayo
# challenge data, so they are derived from DUA-restricted data. CTformer's MIT
# licence permits redistribution, and the authors publish them openly, so the
# licence is not the question — the DUA is. Fetching removes the question at no
# cost to reproducibility, because the bytes come from the authors themselves
# and fetch.sh verifies them against the hashes this project used.
#
# Why you might not: if Mayo/AAPM confirm that derived weights may be
# redistributed, mirroring is simpler for anyone cloning the repository.
#
#   ./scripts/apply-ctformer-weight-fetch.sh            # show what would change
#   ./scripts/apply-ctformer-weight-fetch.sh --apply    # do it
set -euo pipefail
cd "$(dirname "$0")/.."
D=WS-1_dataset/baselines/vendor/ctformer/model_pretrained
W=WS-1_dataset/baselines/src/pwm_ldct_baselines/models/ctformer_wrapper.py
APPLY=${1:-}

[ -f "$D/fetch.sh" ] || { echo "error: $D/fetch.sh missing; nothing prepared"; exit 1; }

if [ "$APPLY" != "--apply" ]; then
  echo "would remove from git (keeping fetch.sh + README.md):"
  git ls-files "$D" | grep -vE 'fetch\.sh|README\.md' | sed 's/^/  /'
  echo "would patch $W so a requested-but-missing checkpoint raises instead of"
  echo "  silently training from scratch."
  echo
  echo "re-run with --apply to make the change."
  exit 0
fi

echo "== 1. remove the mirrored weights from git (files stay on disk) =="
git ls-files "$D" | grep -vE 'fetch\.sh|README\.md' | while read -r f; do
  git rm --cached -q "$f"; echo "  untracked: $f"
done

echo "== 2. ignore them so they are not re-added =="
grep -q 'model_pretrained/\*\.ckpt' .gitignore 2>/dev/null || cat >> .gitignore <<'IGN'

# CTformer pretrained weights are fetched from the authors' repository, not
# mirrored here: they are derived from DUA-restricted AAPM/Mayo data.
# See WS-1_dataset/baselines/vendor/ctformer/model_pretrained/README.md
WS-1_dataset/baselines/vendor/ctformer/model_pretrained/*.ckpt
WS-1_dataset/baselines/vendor/ctformer/model_pretrained/*.npy
IGN
git add .gitignore

echo "== 3. a missing checkpoint must fail loudly, not train from scratch =="
python3 - "$W" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text(encoding="utf-8")
old = '''            else:
                print(f"[ctformer] pretrained ckpt not found: {ckpt} (training from scratch)")'''
new = '''            else:
                # Falling back to random init here would hand back a model that
                # looks trained and is not, and the only signal was a print.
                # pretrained=True was asked for explicitly; if it cannot be
                # honoured, say so.
                raise FileNotFoundError(
                    "CTformer pretrained checkpoint not found: %s\\n"
                    "These weights are fetched, not mirrored, because they are derived "
                    "from DUA-restricted AAPM/Mayo data.\\n"
                    "    run: %s\\n"
                    "Pass pretrained=False to train from scratch deliberately."
                    % (ckpt, os.path.join(os.path.dirname(ckpt), "fetch.sh")))'''
if old not in t:
    print("  already patched (or the wrapper changed); leaving it alone"); sys.exit(0)
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("  patched: missing checkpoint now raises FileNotFoundError")
PY
git add "$W"

echo
echo "staged. review with 'git diff --cached --stat', then commit."
echo "anyone cloning afterwards runs: $D/fetch.sh"
