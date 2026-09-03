@echo off
cd /d D:\ZHY\low_dose_CT-heyang\WS-1_dataset\paper_draft
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex > compile1.log 2>&1
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex > compile2.log 2>&1
echo DONE > compile_done.flag
