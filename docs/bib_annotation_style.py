"""Local bibliography style that displays Zotero annotations.

Zotero/Better BibTeX exports comments from the Extra field as BibTeX
``annotation`` fields.  The default pybtex styles ignore that field, so this
style appends it to the formatted bibliography entry.
"""

from pybtex.plugin import register_plugin
from pybtex.richtext import BaseText, Tag, Text
from pybtex.style import FormattedEntry
from pybtex.style.formatting.alpha import Style as AlphaStyle
from pybtex.style.names.plain import NameStyle
from sphinxcontrib.bibtex.nodes import raw_latex


IGNORED_ANNOTATION_PREFIXES = (
    "ads bibcode:",
    "item id:",
    "last modified:",
    "mag id:",
    "oclc:",
    "openalex:",
    "page version id:",
    "tldr:",
)

COMMENT_PREFIXES = (
    "comment:",
    "commentaire:",
    "note:",
    "remark:",
)

NAME_STYLE = NameStyle()


class LatexOnly(BaseText):
    """Raw LaTeX fragment for PDF-only bibliography layout adjustments."""

    def __init__(self, latex):
        self.latex = latex

    def __str__(self):
        return ""

    def __eq__(self, other):
        return isinstance(other, LatexOnly) and self.latex == other.latex

    def __len__(self):
        return 1

    def __contains__(self, item):
        return False

    def __getitem__(self, key):
        return self

    def split(self, sep=None, keep_empty_parts=None):
        return [self]

    def startswith(self, prefix):
        return False

    def endswith(self, suffix):
        return False

    def isalpha(self):
        return False

    def lower(self):
        return self

    def upper(self):
        return self

    def render(self, backend):
        if getattr(backend, "name", None) == "docutils":
            return [raw_latex(self.latex, "")]
        return backend.format_str("")


def clean_annotation(annotation):
    """Return a displayable comment, or None for technical metadata."""
    annotation = annotation.strip()
    normalized = annotation.lower()
    if normalized.startswith(IGNORED_ANNOTATION_PREFIXES):
        return None

    for prefix in COMMENT_PREFIXES:
        if normalized.startswith(prefix):
            return annotation[len(prefix) :].strip()

    return annotation


def field_text(value, fallback=""):
    """Return a rich text field, preserving LaTeX markup when possible."""
    if not value:
        return Text(fallback)

    try:
        return Text.from_latex(value)
    except Exception:
        return Text(value)


def format_people(people):
    """Format one or two names, then abbreviate longer author lists."""
    if len(people) > 2:
        return Text(NAME_STYLE.format(people[0]).format(), " et al.")

    if len(people) == 2:
        return Text(
            NAME_STYLE.format(people[0]).format(),
            " et ",
            NAME_STYLE.format(people[1]).format(),
        )

    if len(people) == 1:
        return NAME_STYLE.format(people[0]).format()

    return None


def format_author(entry):
    """Return author/editor/institution text for compact bibliography entries."""
    for role in ("author", "editor"):
        people = entry.persons.get(role, [])
        formatted_people = format_people(people)
        if formatted_people is not None:
            return formatted_people

    for field in ("institution", "organization", "publisher"):
        value = entry.fields.get(field)
        if value:
            return field_text(value)

    return Text("Auteur inconnu")


class AlphaWithAnnotationsStyle(AlphaStyle):
    """Compact alpha bibliography style with an added annotation block."""

    def format_entry(self, label, entry, bib_data=None):
        text = Text(
            format_author(entry),
            " - ",
            field_text(entry.fields.get("year"), fallback="s. d."),
            " - ",
            field_text(entry.fields.get("title"), fallback="Sans titre"),
        )

        annotation = clean_annotation(entry.fields.get("annotation", ""))
        if not annotation:
            return FormattedEntry(entry.key, text, label)

        annotation_text = field_text(annotation)

        text = Text(
            text,
            LatexOnly(r"\par\hspace*{2em}"),
            Tag("em", Text("Commentaire : ", annotation_text)),
        )
        return FormattedEntry(entry.key, text, label)


def setup(app):
    register_plugin(
        "pybtex.style.formatting",
        "alpha_with_annotations",
        AlphaWithAnnotationsStyle,
    )
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
