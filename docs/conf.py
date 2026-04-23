# Configuration file for the Sphinx documentation builder.

import os
import sys

project = "Prospective spatiale des impacts cycloniques"
copyright = "2025, Gabriel Genelot, https://doi.org/10.5281/zenodo.18298318"
author = "Gabriel Genelot"
language = "fr"

PYBTEX_STRICT = os.environ.get("PYBTEX_STRICT", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Parse bibliography leniently by default so malformed entries are skipped
# as warnings instead of aborting the whole Sphinx build.
try:
    from pybtex.errors import set_strict_mode

    set_strict_mode(PYBTEX_STRICT)
except Exception:
    pass

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_nb",  # Active automatiquement .md + notebooks
    "sphinxcontrib.mermaid",
]
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

nb_execution_mode = "off"

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


html_theme = "sphinx_book_theme"

myst_enable_extensions = [
    "colon_fence",
]

html_theme_options = {
    "repository_url": "https://github.com/ggenelot/these",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
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

# -- Options for LaTeX / PDF output -----------------------------------------
# RTD uses the LaTeX builder to generate PDF artifacts.
latex_engine = "xelatex"
latex_documents = [
    ("index", "these.tex", project, author, "manual"),
]
