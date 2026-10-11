"""Media uploads: each file is committed to the public media repo on GitHub and served
by jsDelivr from a URL pinned to that commit, so it never changes and is cached forever.

Needs MEDIA_REPO ("owner/name") and GITHUB_MEDIA_TOKEN (a fine-grained token for that one
repo with Contents read/write). The token is only ever sent to api.github.com.
"""

import base64
import json
import secrets
import urllib.error
import urllib.request
from pathlib import PurePosixPath
from urllib.parse import quote

from django.conf import settings
from django.utils.text import slugify

from .models import Media

# jsDelivr serves files from GitHub only up to 20 MB.
MAX_BYTES = 20 * 1024 * 1024
KINDS = {
    **dict.fromkeys([".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"], Media.IMAGE),
    **dict.fromkeys([".mp4", ".webm"], Media.VIDEO),
    ".pdf": Media.FILE,
}
GITHUB_API = "https://api.github.com"


class UploadError(Exception):
    pass


def configured():
    return bool(settings.MEDIA_REPO and settings.GITHUB_MEDIA_TOKEN)


def cdn_url(commit_sha, path):
    return f"https://cdn.jsdelivr.net/gh/{settings.MEDIA_REPO}@{commit_sha}/{quote(path)}"


def repo_path(filename, folder=""):
    """A tidy, unused path in the repo: <folder>/<name>.<ext>, e.g. projects/maze-thumb.webp."""
    name = PurePosixPath(filename)
    stem, ext = slugify(name.stem) or "file", name.suffix.lower()
    folder = "/".join(filter(None, (slugify(part) for part in folder.split("/")))) or "uploads"
    path = f"{folder}/{stem}{ext}"
    while Media.objects.filter(path=path).exists():
        path = f"{folder}/{stem}-{secrets.token_hex(3)}{ext}"
    return path


def put_file(path, content):
    """Create the file in the repo; returns the GitHub API response."""
    body = {
        "message": f"Upload {path}",
        "content": base64.b64encode(content).decode(),
        "branch": settings.MEDIA_BRANCH,
    }
    request = urllib.request.Request(
        f"{GITHUB_API}/repos/{settings.MEDIA_REPO}/contents/{quote(path)}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={
            "Authorization": f"Bearer {settings.GITHUB_MEDIA_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "sevanbnet-control-panel",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        reasons = {
            401: "GitHub rejected the token (expired or revoked?).",
            403: "The token isn't allowed to write to the media repo.",
            404: "GitHub can't find the media repo (check MEDIA_REPO and the token's access).",
            409: "GitHub was busy with another commit; try again.",
            422: "A file with that name is already in the media repo; rename it and try again.",
        }
        raise UploadError(reasons.get(error.code, f"GitHub answered {error.code}.")) from None
    except (urllib.error.URLError, TimeoutError):
        raise UploadError("Couldn't reach GitHub; try again.") from None


def upload(file, folder=""):
    """Commit an uploaded file to the media repo and record it. Returns the Media row."""
    if not configured():
        raise UploadError("Uploads aren't set up on this server.")
    kind = KINDS.get(PurePosixPath(file.name).suffix.lower())
    if kind is None:
        allowed = ", ".join(sorted(KINDS))
        raise UploadError(f"That file type isn't supported. Use one of: {allowed}.")
    if file.size > MAX_BYTES:
        raise UploadError("Files over 20 MB can't be served; put long videos on YouTube.")
    content = file.read()
    path = repo_path(file.name, folder)
    result = put_file(path, content)
    return Media.objects.create(
        path=path, url=cdn_url(result["commit"]["sha"], path), kind=kind, size=len(content)
    )
