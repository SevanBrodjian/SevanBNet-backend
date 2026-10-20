import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify

from .text import markdown_html

VISIBLE_HELP = "Off hides it everywhere on the site."


def link_or_path(value):
    """A full URL, or a path on the site (served from the frontend's public/ folder)."""
    if value and not re.match(r"^(https?://|/)", value):
        raise ValidationError("Use a full URL (https://...) or a site path starting with /.")


hex_colour = RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use a hex colour like #3f8fd2.")


def youtube_id(value):
    """The video id from a YouTube link (watch, youtu.be, embed or shorts) or a bare id."""
    match = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/)([\w-]{11})", value or "")
    if match:
        return match.group(1)
    return value if re.fullmatch(r"[\w-]{11}", value or "") else None


class Project(models.Model):
    IMAGE, VIDEO, YOUTUBE, CODE = "image", "video", "youtube", "code"
    MEDIA_KINDS = [
        (IMAGE, "Image"),
        (VIDEO, "Video"),
        (YOUTUBE, "YouTube"),
        (CODE, "Command (shown as terminal text)"),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="The page address: /projects/ followed by this. A project with a hand-built "
        "page in the site's code is matched by it, so don't change it casually.",
    )
    visible = models.BooleanField(
        "Visible",
        default=True,
        help_text="Off: the project's page is gone everywhere (404) and papers stop linking to it.",
    )
    listed = models.BooleanField(
        "Listed on Projects page",
        default=True,
        help_text="Off: the page still exists, and papers can link to it, "
        "but it isn't in the Projects list.",
    )
    rank = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Usually blank. Ranked projects come first, lowest number first; "
        "the rest follow, newest first.",
    )
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True, help_text="Blank while the project is ongoing.")
    summary = models.CharField(
        "One-line summary", max_length=300, blank=True, help_text="Shown in the Projects list."
    )
    thumbnail = models.CharField(
        max_length=500,
        blank=True,
        validators=[link_or_path],
        help_text="Image for the Projects list, 16:10 (560×350 is plenty). "
        "Paste a URL or pick an uploaded file.",
    )
    glow = models.CharField(
        "Glow colour",
        max_length=7,
        blank=True,
        validators=[hex_colour],
        help_text="Optional. The colour the thumbnail glows on hover, e.g. #3f8fd2.",
    )
    media_kind = models.CharField("Media type", max_length=10, choices=MEDIA_KINDS, blank=True)
    media = models.CharField(
        max_length=500,
        blank=True,
        help_text="Shown at the top of the default page: an image or video URL, "
        "a YouTube link, or the command text.",
    )
    media_poster = models.CharField(
        "Video poster",
        max_length=500,
        blank=True,
        validators=[link_or_path],
        help_text="Video only: the still shown before it plays.",
    )
    media_alt = models.CharField(
        "Image description", max_length=300, blank=True, help_text="Image only, for screen readers."
    )
    media_width = models.PositiveIntegerField(
        null=True, blank=True, help_text="Optional pixel size; keeps the page from jumping."
    )
    media_height = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(
        "Source",
        max_length=500,
        blank=True,
        validators=[link_or_path],
        help_text="Link to the code, e.g. the GitHub repository.",
    )
    description = models.TextField(
        blank=True,
        help_text="Markdown. The text of the default page. A project with a hand-built page "
        "doesn't show it, but search engines may.",
    )

    class Meta:
        ordering = [
            F("rank").asc(nulls_last=True),
            Coalesce("end", "start").desc(nulls_last=True),
            "title",
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{settings.SITE_URL}/projects/{self.slug}"

    def clean(self):
        if self.media_kind and not self.media:
            raise ValidationError({"media": "Add the media, or clear the media type."})
        if self.media and not self.media_kind:
            raise ValidationError({"media_kind": "Choose what kind of media this is."})
        if self.media_kind == self.YOUTUBE and not youtube_id(self.media):
            raise ValidationError({"media": "That doesn't look like a YouTube link."})
        if self.media_kind in (self.IMAGE, self.VIDEO):
            try:
                link_or_path(self.media)
            except ValidationError as error:
                raise ValidationError({"media": error.messages}) from None

    @property
    def description_html(self):
        return markdown_html(self.description)


class Publication(models.Model):
    """A paper. Papers have no page of their own; they can point at a project page."""

    title = models.CharField(max_length=200)
    key = models.SlugField(  # noqa: DJ001 (optional and unique, so blank must be NULL)
        "Widget key",
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Short stable name the site's code uses for this paper's interactive figure "
        "(e.g. kuramoto). Leave blank if it has none.",
    )
    visible = models.BooleanField("Visible", default=True, help_text=VISIBLE_HELP)
    authors = models.CharField(
        max_length=400,
        blank=True,
        help_text="As they should read, e.g. Jane Doe, Sevan Brodjian, John Roe. "
        "Your name is highlighted automatically.",
    )
    venue = models.CharField(
        max_length=200, blank=True, help_text="e.g. NeurIPS 2025. Blank for preprints."
    )
    status = models.CharField(max_length=1000, help_text="e.g. Accepted (Poster), Under Review.")
    date = models.DateField(
        null=True, blank=True, help_text="Publication date, or the submission date until then."
    )
    paper_url = models.URLField("Paper link", max_length=500, blank=True, help_text="PDF or arXiv.")
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="papers",
        help_text="A project page on this site. The paper's Project button appears only "
        "while that project is visible.",
    )
    project_url = models.URLField(
        "External project page",
        max_length=500,
        blank=True,
        help_text="Only for a project page hosted somewhere else.",
    )
    bibtex = models.TextField("BibTeX", blank=True)
    doi = models.CharField("DOI", max_length=200, blank=True, help_text="Kept for reference.")
    rank = models.IntegerField(
        null=True, blank=True, help_text="Ranked papers come first, lowest number first."
    )
    description = models.TextField(blank=True, help_text="A short summary for the Papers page.")

    class Meta:
        ordering = [F("rank").asc(nulls_last=True), F("date").desc(nulls_last=True), "title"]
        verbose_name = "paper"

    def __str__(self):
        return self.title

    def clean(self):
        if self.project_id and self.project_url:
            raise ValidationError(
                "Choose either a project on this site or an external project page, not both."
            )


class BlogPost(models.Model):
    """A post's metadata. Its text is content/writing/<slug>.md in the frontend repo."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="The post's text is the frontend's content/writing/ file with this name "
        "(plus .md), and its page is /writing/ followed by this.",
    )
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.localdate)
    visible = models.BooleanField("Visible", default=True, help_text=VISIBLE_HELP)

    class Meta:
        ordering = ["date", "title"]
        verbose_name = "post"
        verbose_name_plural = "writing"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{settings.SITE_URL}/writing/{self.slug}"


WRITING_NOTE = (
    "Warning: the following are my unfiltered philosophical explorations. They reflect my "
    "thinking over time and not necessarily what I still believe. I do not edit old essays, "
    "even when they now seem immature to me."
)


class SiteSettings(models.Model):
    """Text on the site that isn't tied to a project, paper or post. There is one row."""

    home_line = models.CharField(
        "Home page line", max_length=300, help_text="The line the home page leads with."
    )
    role = models.CharField(max_length=200, help_text="Shown with your name on the home page.")
    about = models.TextField(
        "About",
        help_text="The About page, in Markdown: a blank line starts a paragraph, a single "
        "line break stays a line break, *italic*, **bold**, [a link](https://…).",
    )
    writing_note = models.TextField(
        "Writing page note",
        blank=True,
        default=WRITING_NOTE,
        db_default=WRITING_NOTE,
        help_text="Shown at the top of the Writing page, in Markdown like the About text. "
        "Leave it empty to show nothing.",
    )

    class Meta:
        verbose_name = verbose_name_plural = "site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    @property
    def about_paragraphs(self):
        return [p.strip() for p in re.split(r"\n\s*\n", self.about) if p.strip()]

    @property
    def about_html(self):
        return markdown_html(self.about)

    @property
    def writing_note_html(self):
        return markdown_html(self.writing_note)


class Media(models.Model):
    """A file uploaded through the control panel, committed to the media repo on GitHub."""

    IMAGE, VIDEO, FILE = "image", "video", "file"
    KINDS = [(IMAGE, "Image"), (VIDEO, "Video"), (FILE, "File")]

    path = models.CharField(max_length=300, unique=True, help_text="Path in the media repo.")
    url = models.URLField("URL", max_length=500)
    kind = models.CharField("Type", max_length=10, choices=KINDS)
    size = models.PositiveIntegerField(help_text="Bytes.")
    uploaded_at = models.DateTimeField("Uploaded", auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = verbose_name_plural = "media"

    def __str__(self):
        return self.path


# ── QR Code Manager ──────────────────────────────────────────────────────────

QR_STYLE_CHOICES = [
    ("square", "Square"),
    ("rounded", "Rounded"),
    ("circle", "Circle"),
    ("gapped", "Gapped"),
]


class QRRedirect(models.Model):
    short_code = models.SlugField(max_length=50, unique=True)
    label = models.CharField(max_length=200)
    target_url = models.URLField(max_length=2000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fg_color = models.CharField(max_length=7, default="#000000")
    bg_color = models.CharField(max_length=7, default="#ffffff")
    qr_style = models.CharField(max_length=10, choices=QR_STYLE_CHOICES, default="square")
    qr_radius = models.FloatField(default=0.5)
    bg_transparent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "QR code"

    def __str__(self):
        return f"{self.label} ({self.short_code})"


class Scan(models.Model):
    redirect = models.ForeignKey(QRRedirect, on_delete=models.CASCADE, related_name="scans")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Scan of {self.redirect.short_code} at {self.timestamp}"
