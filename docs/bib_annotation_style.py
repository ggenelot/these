"""Local bibliography style that displays Zotero annotations.

Zotero/Better BibTeX exports comments from the Extra field as BibTeX
``annotation`` fields.  The default pybtex styles ignore that field, so this
style appends it to the formatted bibliography entry.
"""

from pybtex.plugin import register_plugin
from pybtex.richtext import Tag, Text
from pybtex.style import FormattedEntry
from pybtex.style.formatting.alpha import Style as AlphaStyle


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


class AlphaWithAnnotationsStyle(AlphaStyle):
    """Alpha bibliography style with an added annotation suffix."""

    def format_entry(self, label, entry, bib_data=None):
        formatted_entry = super().format_entry(label, entry, bib_data=bib_data)
        annotation = clean_annotation(entry.fields.get("annotation", ""))
        if not annotation:
            return formatted_entry

        try:
            annotation_text = Text.from_latex(annotation)
        except Exception:
            annotation_text = Text(annotation)

        text = Text(
            formatted_entry.text,
            " ",
            Tag("em", Text("Commentaire : ", annotation_text)),
        )
        return FormattedEntry(formatted_entry.key, text, formatted_entry.label)


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
