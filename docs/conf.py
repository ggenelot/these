# Configuration file for the Sphinx documentation builder.

import os
import sys
import importlib
import warnings

# Make BibTeX parsing non-fatal for malformed entries.
# This keeps the PDF build running while still surfacing warnings.
try:
    import pybtex.errors as pybtex_errors

    def _warn_only(exception):
        warnings.warn(str(exception), RuntimeWarning)

    # Disable strict mode when available.
    if hasattr(pybtex_errors, "set_strict_mode"):
        pybtex_errors.set_strict_mode(False)

    # Patch every known report_error binding used by pybtex internals.
    for module_name in (
        "pybtex.errors",
        "pybtex.database",
        "pybtex.database.input.bibtex",
    ):
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "report_error"):
                setattr(module, "report_error", _warn_only)
        except Exception:
            pass
except Exception:
    pass

project = "Prospective spatiale des impacts cycloniques"
copyright = "2025, Gabriel Genelot, https://doi.org/10.5281/zenodo.18298318"
author = "Gabriel Genelot"

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

# On autorise Sphinx à parcourir l'arborescence des sources docs
include_patterns = [
    "**",
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
exclude_patterns = [
    "_build",
    "_build/**",
    "**/.ipynb_checkpoints",
]

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

# -- Options for PDF output --------------------------------------------------

latex_engine = "xelatex"
latex_documents = [
    ("pdf_index", "bibliographie.tex", "Documentation complete", author, "manual"),
]
latex_docclass = {
    "manual": "tufte-book",
}
latex_additional_files = [
    "../templates/tufte/tufte-book.cls",
    "../templates/tufte/tufte-common.def",
    "../templates/tufte/tufte-handout.cls",
]

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
