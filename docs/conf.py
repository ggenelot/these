# Configuration file for the Sphinx documentation builder.

import os
import sys
import importlib
import warnings
import re

import yaml

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
latex_elements = {
    "passoptionstopackages": r"\PassOptionsToPackage{nobottomtitles*}{titlesec}",
    "preamble": r"""
\newenvironment{chapterabstract}{
  \par\noindent
  \begin{minipage}{\linewidth}
  \small\itshape
  \textbf{Resume. }\ignorespaces
}{
  \par
  \end{minipage}
  \par
}
""",
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


_FRONT_MATTER_RE = re.compile(
    r"\A---\s*\r?\n(?P<yaml>.*?)(?:\r?\n)---\s*(?:\r?\n)?",
    re.DOTALL,
)
_FIRST_H1_RE = re.compile(r"^#\s+.+$", re.MULTILINE)


def _inject_chapter_abstract(app, docname, source):
    """Inject parts.abstract from Markdown frontmatter as a visible section."""
    if app.builder.format != "latex":
        return

    src_path = app.env.doc2path(docname, base=None)
    if not src_path.endswith(".md"):
        return

    text = source[0]
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return

    body = text[match.end() :]
    if "<!-- auto-abstract -->" in body:
        return

    try:
        metadata = yaml.safe_load(match.group("yaml")) or {}
    except Exception:
        return

    abstract = ((metadata.get("parts") or {}).get("abstract") or "").strip()
    if not abstract:
        return

    abstract_block = (
        "<!-- auto-abstract -->\n\n"
        "```{raw} latex\n"
        "\\begin{chapterabstract}\n"
        "```\n\n"
        f"{abstract}\n\n"
        "```{raw} latex\n"
        "\\end{chapterabstract}\n"
        "\\clearpage\n"
        "```\n\n"
    )
    prefix = text[: match.end()]
    if not prefix.endswith(("\n", "\r")):
        prefix += "\n"
    h1_match = _FIRST_H1_RE.search(body)
    if h1_match:
        insert_at = h1_match.end()
        body = body[:insert_at] + "\n\n" + abstract_block + body[insert_at:].lstrip()
    else:
        body = abstract_block + body.lstrip()

    source[0] = prefix + body


def setup(app):
    app.connect("source-read", _inject_chapter_abstract)
