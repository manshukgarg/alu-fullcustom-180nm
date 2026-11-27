#!/bin/bash
# Build the project report: Word file and PDF, with the page numbers of the contents and lists
# filled in from a first PDF.   Needs node with docx, LibreOffice (soffice) and pdftotext.
#   bash docs/report/build.sh [path to soffice wrapper or soffice]
set -e
cd "$(dirname "$0")"
SOFFICE=${1:-soffice}
convert() {
  rm -f ALU_project_report.pdf
  $SOFFICE --headless --convert-to pdf ALU_project_report.docx > /dev/null 2>&1
  test -f ALU_project_report.pdf
}
rm -f pages.json
node build_report.js
convert
python3 find_pages.py ALU_project_report.pdf
node build_report.js
convert
python3 find_pages.py ALU_project_report.pdf > /dev/null   # check: page numbers unchanged
zip -d ALU_project_report.docx '*/' > /dev/null 2>&1 || true
echo "built ALU_project_report.docx and ALU_project_report.pdf"
