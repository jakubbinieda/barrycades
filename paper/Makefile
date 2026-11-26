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

.PHONY: print
print: ${DEFAULT}
	gucio_print --duplex --stapler ${DEFAULT}

.PHONY: check
check:
	aspell --lang=en_US.UTF-8 --check ${NAME}.tex

.PHONY: publish
publish: ${DEFAULT}
	if [ "${HOST}" == staff ]; then rsync -a $? /home/gutowski/public_html/content; else rsync -a $? staff:public_html/content; fi

.PHONY: ci
ci: show
	latexmk ${LATEXMKOPTS} ${LATEXMKCIOPTS} ${NAME}
