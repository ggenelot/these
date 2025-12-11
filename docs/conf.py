# Configuration file for the Sphinx documentation builder.

project = 'TC damage spatial analysis'
copyright = '2025, Gabriel Genelot'
author = 'Gabriel Genelot'

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_nb",   # Active automatiquement .md + notebooks
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"

# Optionnel : quelques réglages simples
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#3A7DCE",
        "color-brand-content": "#3A7DCE",
    },
    "dark_css_variables": {
        "color-brand-primary": "#6BA4F8",
        "color-brand-content": "#6BA4F8",
    },
}


html_static_path = ["_static"]

# -- Options for figure numbering --------------------------------------------

numfig = True
numfig_format = {
    "figure": "Figure %s",
    "table": "Table %s",
}

# -- Options for the bibliography --------------------------------------------

extensions += [
    "sphinxcontrib.bibtex",
]

bibtex_bibfiles = ["references.bib"]
bibtex_reference_style = "author_year"


# -- Path to project code ----------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath("../../scripts"))
