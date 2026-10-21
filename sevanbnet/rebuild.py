"""The control panel's "Rebuild site" button.

The frontend prerenders its pages (for crawlers) from this API at build time, so content
edits reach those pages only after a new build. This redeploys the frontend service of
the same Railway environment from its latest commit.

Needs RAILWAY_DEPLOY_TOKEN (a Railway project token for this environment) and
FRONTEND_SERVICE_ID; Railway provides RAILWAY_ENVIRONMENT_ID itself.
"""

import json
import logging
import threading
import urllib.error
import urllib.request

from django.conf import settings

RAILWAY_API = "https://backboard.railway.com/graphql/v2"
DEPLOY = (
    "mutation($service: String!, $environment: String!) {"
    " serviceInstanceDeployV2(serviceId: $service, environmentId: $environment) }"
)


# Saving content in the control panel rebuilds the site by itself, so its prerendered pages
# (what crawlers and language models read) and the text built into the app never fall
# behind: SETTLE seconds after the last save, so a run of edits makes one build.
SETTLE = 45

log = logging.getLogger(__name__)
_timer = None
_lock = threading.Lock()


class RebuildError(Exception):
    pass


def configured():
    return bool(
        settings.RAILWAY_DEPLOY_TOKEN
        and settings.FRONTEND_SERVICE_ID
        and settings.RAILWAY_ENVIRONMENT_ID
    )


def rebuild():
    """Start a new frontend deploy. Returns Railway's deployment id."""
    body = {
        "query": DEPLOY,
        "variables": {
            "service": settings.FRONTEND_SERVICE_ID,
            "environment": settings.RAILWAY_ENVIRONMENT_ID,
        },
    }
    request = urllib.request.Request(
        RAILWAY_API,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Project-Access-Token": settings.RAILWAY_DEPLOY_TOKEN,
            "User-Agent": "sevanbnet-control-panel",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise RebuildError(f"Railway answered {error.code}.") from None
    except (urllib.error.URLError, TimeoutError):
        raise RebuildError("Couldn't reach Railway; try again.") from None
    # GraphQL reports failures in the body, even with HTTP 200.
    if data.get("errors"):
        raise RebuildError(f"Railway said: {data['errors'][0].get('message', 'unknown error')}")
    return (data.get("data") or {}).get("serviceInstanceDeployV2")


def soon():
    """Rebuild SETTLE seconds from now; each call starts the wait again. False if this
    server can't rebuild (not configured)."""
    global _timer
    if not configured():
        return False
    with _lock:
        if _timer:
            _timer.cancel()
        _timer = threading.Timer(SETTLE, _fire)
        _timer.daemon = True
        _timer.start()
    return True


def _fire():
    global _timer
    with _lock:
        _timer = None
    try:
        rebuild()
        log.info("Rebuild started after a content edit.")
    except RebuildError as error:
        log.warning("Automatic rebuild failed: %s (use Rebuild site in the panel)", error)
