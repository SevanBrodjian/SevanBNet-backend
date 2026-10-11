import markdown
import nh3

# Inline HTML is allowed in the Markdown, then everything is sanitized: no scripts, styles
# or event handlers, and links only to http(s), mailto or paths on the site.
_cleaner = nh3.Cleaner(url_schemes={"http", "https", "mailto"})


def markdown_html(text):
    if not text:
        return ""
    html = markdown.markdown(text, extensions=["extra", "nl2br", "sane_lists"])
    return _cleaner.clean(html)
