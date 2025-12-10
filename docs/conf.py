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
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for figure numbering --------------------------------------------

numfig = True
numfig_format = {
    "figure": "Figure %s",
    "table": "Table %s",
}


# -- Path to project code ----------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath("../../scripts"))
