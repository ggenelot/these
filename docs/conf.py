# Configuration file for the Sphinx documentation builder.

import os
import sys
import importlib
import warnings
import re
import logging

import yaml
import docutils.nodes
import pybtex.plugin
from sphinxcontrib.bibtex.domain import (
    BibtexDomain,
    SphinxReferenceInfo,
    format_references,
    parse_citation_targets,
)
from sphinx.writers.latex import CR, LaTeXTranslator

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
  securityLevel: "loose",
  theme: "base",
  themeVariables: {
    primaryColor: "#f6f3ee",
    primaryTextColor: "#222222",
    primaryBorderColor: "#555555",
    lineColor: "#666666",
    secondaryColor: "#e9ecef",
    tertiaryColor: "#ffffff",
    fontFamily: "Inter, Arial, sans-serif"
  },
  flowchart: {
    curve: "basis"
  },
  deterministicIds: true
});
"""

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "_build/**",
    "2_introduction/introduction.md",
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
    ("pdf_index", "bibliographie.tex", "Bibliographie", author, "manual"),
]
latex_docclass = {
    "manual": "tufte-book",
}
latex_elements = {
    "extraclassoptions": "nobib",
    "passoptionstopackages": r"\PassOptionsToPackage{nobottomtitles*}{titlesec}",
    "preamble": r"""
\newenvironment{chapterabstract}{
  \par\noindent
  \begin{minipage}{\linewidth}
  \small
  \textbf{Résumé. }\ignorespaces
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
    "bib_annotation_style",
    "sphinxcontrib.bibtex",
]

bibtex_bibfiles = ["references.bib"]
bibtex_reference_style = "author_year"
bibtex_default_style = "alpha_with_annotations"
bibtex_cite_style = "authoryear"

# -- Path to project code ----------------------------------------------------
sys.path.insert(0, os.path.abspath("../src"))


_FRONT_MATTER_RE = re.compile(
    r"\A---\s*\r?\n(?P<yaml>.*?)(?:\r?\n)---\s*(?:\r?\n)?",
    re.DOTALL,
)
_FIRST_H1_RE = re.compile(r"^#\s+.+$", re.MULTILINE)
_PANDOC_CITATION_KEY_RE = (
    r"[A-Za-z0-9_][A-Za-z0-9_:-]*(?:\.[A-Za-z0-9_][A-Za-z0-9_:-]*)*"
)
_PANDOC_BRACKET_CITATION_RE = re.compile(
    rf"\[((?:@{_PANDOC_CITATION_KEY_RE}(?:[;,]\s*)?)+)\]"
)
_PANDOC_BARE_CITATION_RE = re.compile(rf"(?<![\w`])@({_PANDOC_CITATION_KEY_RE})")
_FENCED_CODE_RE = re.compile(r"(^```.*?^```)", re.MULTILINE | re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def _replace_outside_code(text, replace_func):
    parts = _FENCED_CODE_RE.split(text)
    for index, part in enumerate(parts):
        if index % 2:
            continue
        inline_parts = _INLINE_CODE_RE.split(part)
        inline_matches = _INLINE_CODE_RE.findall(part)
        rebuilt = []
        for inline_index, inline_part in enumerate(inline_parts):
            rebuilt.append(replace_func(inline_part))
            if inline_index < len(inline_matches):
                rebuilt.append(inline_matches[inline_index])
        parts[index] = "".join(rebuilt)
    return "".join(parts)


def _convert_pandoc_citations(app, docname, source):
    """Convert Pandoc-style Markdown citations to sphinxcontrib-bibtex roles."""
    src_path = app.env.doc2path(docname, base=None)
    if not src_path.endswith(".md"):
        return

    def convert(text):
        def replace_bracket(match):
            keys = re.findall(rf"@({_PANDOC_CITATION_KEY_RE})", match.group(1))
            return "{cite:p}`" + ",".join(keys) + "`"

        text = _PANDOC_BRACKET_CITATION_RE.sub(replace_bracket, text)
        return _PANDOC_BARE_CITATION_RE.sub(r"{cite:p}`\1`", text)

    source[0] = _replace_outside_code(source[0], convert)


def _resolve_xref_with_non_citation_lists(
    self, env, fromdocname, builder, typ, target, node, contnode
):
    """Resolve citation references against citation, bullet, or enumerated lists."""
    targets = parse_citation_targets(target)
    keys = {target2.key: target2 for target2 in targets}
    citations = {cit.key: cit for cit in self.citations if cit.key in keys}

    for key in keys:
        if key not in citations:
            logger = logging.getLogger(__name__)
            logger.warning('could not find bibtex key "%s"', key)

    plaintext = pybtex.plugin.find_plugin("pybtex.backends", "plaintext")()
    references = [
        (
            citation.entry,
            citation.formatted_entry,
            SphinxReferenceInfo(
                builder=builder,
                fromdocname=fromdocname,
                todocname=citation.bibliography_key.docname,
                citation_id=citation.citation_id,
                title=(
                    citation.tooltip_entry.text.render(plaintext).replace("\\url ", "")
                    if citation.tooltip_entry
                    else None
                ),
                pre_text=keys[citation.key].pre,
                post_text=keys[citation.key].post,
            ),
        )
        for citation in citations.values()
    ]
    formatted_references = format_references(self.reference_style, typ, references)
    result_node = docutils.nodes.inline(rawsource=target)
    result_node += formatted_references.render(self.backend)
    return result_node


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

    parts = metadata.get("parts") or {}
    chapter_title = (metadata.get("title") or "").strip()
    abstract = (parts.get("abstract") or "").strip()
    problematic = (parts.get("problematic") or "").strip()
    literature_note = (parts.get("literature_note") or "").strip()
    partial_conclusion = (parts.get("partial_conclusion") or "").strip()

    raw_keywords = parts.get("keywords")
    if raw_keywords is None:
        raw_keywords = metadata.get("keywords")
    if isinstance(raw_keywords, str):
        keywords = [raw_keywords]
    elif isinstance(raw_keywords, list):
        keywords = [str(k).strip() for k in raw_keywords if str(k).strip()]
    else:
        keywords = []

    raw_keypoints = parts.get("keypoints")
    if isinstance(raw_keypoints, str):
        keypoints = [raw_keypoints]
    elif isinstance(raw_keypoints, list):
        keypoints = [str(k).strip() for k in raw_keypoints if str(k).strip()]
    else:
        keypoints = []

    if not any(
        (
            abstract,
            problematic,
            literature_note,
            partial_conclusion,
            keywords,
            keypoints,
        )
    ):
        return

    keywords_md = (
        f"**Mots-clés :** {', '.join(keywords)}\n\n" if keywords else ""
    )
    metadata_gap_md = ""
    if keywords and keypoints:
        metadata_gap_md = (
            "```{raw} latex\n"
            "\\vspace{0.7em}\n"
            "```\n\n"
        )
    keypoints_md = ""
    if keypoints:
        keypoints_md = "**Points clés :**\n\n" + "\n".join(
            f"- {point}" for point in keypoints
        ) + "\n\n"

    abstract_md = f"*{abstract}*\n\n" if abstract else ""
    chapter_fields = [
        ("Problématique", problematic),
        ("Littérature mobilisée", literature_note),
        ("Apport du chapitre", partial_conclusion),
    ]
    chapter_fields_md = "".join(
        f"**{label} :** {value}\n\n"
        for label, value in chapter_fields
        if value
    )
    metadata_sep_md = ""
    if abstract and (chapter_fields_md or keywords or keypoints):
        metadata_sep_md = (
            "```{raw} latex\n"
            "\\vspace{0.6em}\n"
            "\\noindent\\rule{\\linewidth}{0.3pt}\n"
            "\\vspace{0.6em}\n"
            "```\n\n"
        )

    abstract_block = (
        "<!-- auto-abstract -->\n\n"
        "```{raw} latex\n"
        "\\begin{chapterabstract}\n"
        "```\n\n"
        + abstract_md
        + metadata_sep_md
        + chapter_fields_md
        + keywords_md
        + metadata_gap_md
        + keypoints_md
        + "```{raw} latex\n"
        + "\\end{chapterabstract}\n"
        + "\\clearpage\n"
        + "```\n\n"
    )
    prefix = text[: match.end()]
    if not prefix.endswith(("\n", "\r")):
        prefix += "\n"
    h1_match = _FIRST_H1_RE.search(body)
    if chapter_title:
        title_line = f"# {chapter_title}"
        if h1_match:
            body = title_line + body[h1_match.end() :]
            h1_match = _FIRST_H1_RE.search(body)
        else:
            body = title_line + "\n\n" + body.lstrip()
            h1_match = _FIRST_H1_RE.search(body)

    if h1_match:
        insert_at = h1_match.end()
        body = body[:insert_at] + "\n\n" + abstract_block + body[insert_at:].lstrip()
    else:
        body = abstract_block + body.lstrip()

    source[0] = prefix + body


def _flatten_bibtex_bullet_lists(app, doctree, docname):
    """Render BibTeX bullet bibliographies as plain entry paragraphs in LaTeX."""
    if app.builder.format != "latex":
        return

    for bullet_list in list(doctree.findall(docutils.nodes.bullet_list)):
        if not bullet_list.children:
            continue
        if not all(
            isinstance(item, docutils.nodes.list_item) and item.get("docname")
            for item in bullet_list.children
        ):
            continue

        flattened = []
        for item in bullet_list.children:
            children = list(item.children)
            if not children:
                continue

            first_child = children[0]
            for attr in ("ids", "names", "classes", "backrefs"):
                values = item.get(attr, [])
                if values:
                    first_child[attr].extend(values)
            first_child["docname"] = item.get("docname")
            flattened.extend(children)

        if flattened:
            bullet_list.replace_self(flattened)


def _restore_titled_tip_admonitions(app, doctree, docname):
    """Use the first paragraph as title for ``{tip} Custom title`` blocks."""
    if app.builder.format != "latex":
        return

    for admonition in doctree.findall(docutils.nodes.tip):
        if not admonition.children:
            continue
        first_paragraph = admonition.children[0]
        if not isinstance(first_paragraph, docutils.nodes.paragraph):
            continue
        if len(first_paragraph.children) != 1:
            continue

        custom_title = first_paragraph.astext().strip()
        if custom_title:
            admonition["custom_title"] = custom_title
            first_paragraph.parent.remove(first_paragraph)


_ORIGINAL_LATEX_VISIT_TIP = LaTeXTranslator.visit_tip


def _visit_tip_with_custom_title(self, node):
    custom_title = node.get("custom_title")
    if not custom_title:
        return _ORIGINAL_LATEX_VISIT_TIP(self, node)

    self.body.append(
        CR
        + r"\begin{sphinxadmonition}{tip}{%s:}" % self.encode(custom_title)
        + CR
    )
    self.no_latex_floats += 1
    if self.table:
        self.table.has_problematic = True


def setup(app):
    BibtexDomain.resolve_xref = _resolve_xref_with_non_citation_lists
    LaTeXTranslator.visit_tip = _visit_tip_with_custom_title
    app.connect("source-read", _convert_pandoc_citations)
    app.connect("source-read", _inject_chapter_abstract)
    app.connect("doctree-resolved", _restore_titled_tip_admonitions)
    app.connect("doctree-resolved", _flatten_bibtex_bullet_lists)
