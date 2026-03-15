# =============================================================
# NutriTrack — Documentation Build System
# =============================================================
# Build both LaTeX outputs with: make docs
# Prerequisites: pdflatex, bibtex (TeX Live or MacTeX)
# =============================================================

TEX      = pdflatex
BIBTEX   = bibtex
TEXFLAGS = -interaction=nonstopmode -halt-on-error -file-line-error

RAPPORT  = rapport_final
SLIDES   = defense_slides

.PHONY: all docs rapport slides clean distclean help

# Default target
all: docs

# Build both documents
docs: rapport slides

# Build the thesis report
rapport: $(RAPPORT).pdf

$(RAPPORT).pdf: $(RAPPORT).tex
	$(TEX) $(TEXFLAGS) $(RAPPORT).tex
	$(TEX) $(TEXFLAGS) $(RAPPORT).tex
	$(TEX) $(TEXFLAGS) $(RAPPORT).tex
	@echo "==> $(RAPPORT).pdf built successfully."

# Build the defense slides
slides: $(SLIDES).pdf

$(SLIDES).pdf: $(SLIDES).tex
	$(TEX) $(TEXFLAGS) $(SLIDES).tex
	$(TEX) $(TEXFLAGS) $(SLIDES).tex
	@echo "==> $(SLIDES).pdf built successfully."

# Clean auxiliary files
clean:
	rm -f *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg \
	      *.nav *.snm *.vrb *.fls *.fdb_latexmk *.synctex.gz \
	      *.run.xml *.bcf

# Clean everything including PDFs
distclean: clean
	rm -f $(RAPPORT).pdf $(SLIDES).pdf

help:
	@echo "Available targets:"
	@echo "  make docs      - Build both rapport_final.pdf and defense_slides.pdf"
	@echo "  make rapport   - Build rapport_final.pdf only"
	@echo "  make slides    - Build defense_slides.pdf only"
	@echo "  make clean     - Remove auxiliary files"
	@echo "  make distclean - Remove auxiliary files and PDFs"
