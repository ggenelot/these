# Configuration file for the Sphinx documentation builder.

import os
import sys

project = "SIG et prospective"
copyright = "2025, Gabriel Genelot"
author = "Gabriel Genelot"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_nb",  # Active automatiquement .md + notebooks
    "sphinxcontrib.mermaid",
    "sphinx.ext.autosectionlabel", # Hover
    "sphinx_hoverxref", # Hover
]


# Configuration for hover
hoverxref_roles = ["ref", "numref"]
hoverxref_auto_ref = True
hoverxref_domains = ["std"]
hoverxref_mathjax = True
hoverxref_modal_hover_delay = 300
autosectionlabel_prefix_document = True



autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_mock_imports = [
    "py7zr",
    "rioxarray",
    "matplotlib",
    "osmnx",
    "terracatalogueclient",
]

# On autorise Sphinx à parcourir l'arborescence
include_patterns = [
    '**',                 # inclure tous les fichiers standards dans docs/
    '../notebooks/*.ipynb',   # ajouter explicitement l'accès aux notebooks externes
]



myst_enable_extensions = [
    "colon_fence",
    "linkify",
    "substitution",
]
# Allow ```mermaid fences in addition to ```{mermaid}
myst_fence_as_directive = ["mermaid"]

# Mermaid rendering
mermaid_version = "10.9.1"  # version bundled via sphinxcontrib-mermaid CDN
mermaid_init_js = """
mermaid.initialize({
  startOnLoad: true,
  securityLevel: "loose"
});
"""

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
#bibtex_default_style = 'unsrt'
bibtex_cite_style = "authoryear"

# -- Path to project code ----------------------------------------------------
sys.path.insert(0, os.path.abspath("../src"))
