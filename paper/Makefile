NAME=main
DEFAULT=${NAME}.pdf
LATEXMKOPTS=-pdflatex -synctex=1 -emulate-aux-dir -aux-directory=${AUXDIR}
LATEXMKCIOPTS=-pvc -view=none -interaction=nonstopmode

AUXDIR=__aux__
HOST=$(shell uname -n |cut -d . -f 1)

.PHONY: default
default: ${DEFAULT}

.PHONY: clean
clean:
	rm -f ${AUX_DIR} ${DEFAULT} *.aux *.bbl *.blg *.bcf *.log *.out *.vtc

%.pdf: %.tex *.bib 
	latexmk ${LATEXMKOPTS} $*

.PHONY: show
show: ${DEFAULT}
	open -a Skim ${DEFAULT} >/dev/null 2>&1 || open ${DEFAULT} >/dev/null 2>&1 || evince ${DEFAULT} >/dev/null 2>&1 &

.PHONY: ci
ci: show
	latexmk ${LATEXMKOPTS} ${LATEXMKCIOPTS} ${NAME}
