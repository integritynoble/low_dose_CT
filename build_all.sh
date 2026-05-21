#!/usr/bin/env bash
# build_all.sh — compile all four WS paper drafts.
# Requires pdflatex + bibtex (any modern TeX distribution: TeX Live,
# MiKTeX, MacTeX). Tested on MiKTeX 25.12 / Windows + Git Bash.
#
# Usage:
#   ./build_all.sh         # build all four manuscripts
#   ./build_all.sh clean   # remove generated PDFs and build artifacts
#
# After a clean build, each WS-N_*/paper_draft/ contains manuscript.pdf
# alongside the .tex source.
set -euo pipefail

DRAFTS=(
    WS-1_dataset/paper_draft
    WS-2_framework/paper_draft
    WS-3_reference_method/paper_draft
    WS-4_leaderboard/paper_draft
)

case "${1:-build}" in
    clean)
        for d in "${DRAFTS[@]}"; do
            echo "Cleaning $d"
            ( cd "$d" && rm -f manuscript.pdf manuscript.aux manuscript.bbl \
                            manuscript.blg manuscript.log manuscript.out \
                            manuscript.toc manuscript.synctex.gz )
        done
        echo "Clean complete."
        ;;
    build|"")
        for d in "${DRAFTS[@]}"; do
            echo
            echo "=========================================================="
            echo "Building $d"
            echo "=========================================================="
            ( cd "$d" \
                && pdflatex -interaction=nonstopmode manuscript.tex > /dev/null \
                && bibtex   manuscript                              > /dev/null \
                && pdflatex -interaction=nonstopmode manuscript.tex > /dev/null \
                && pdflatex -interaction=nonstopmode manuscript.tex > /dev/null )
            pages=$(pdfinfo "$d/manuscript.pdf" 2>/dev/null | awk '/^Pages:/ {print $2}')
            size=$(  stat -c '%s' "$d/manuscript.pdf" 2>/dev/null \
                  || stat -f '%z' "$d/manuscript.pdf" )
            echo "  -> manuscript.pdf  ${pages} pages, ${size} bytes"
        done
        echo
        echo "All four manuscripts built successfully."
        ;;
    *)
        echo "usage: $0 [build|clean]" >&2
        exit 2
        ;;
esac
