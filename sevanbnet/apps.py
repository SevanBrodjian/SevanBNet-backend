from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.signals import connection_created


def _require_sandbox_marker(sender, connection, **kwargs):
    """Locally, Postgres is only ever the sandbox. The sandbox has a sandbox.marker table
    (see docs/sandbox.md) and production doesn't, so a local command pointed at the wrong
    database stops here before it touches anything."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('sandbox.marker')")
        if cursor.fetchone()[0] is None:
            connection.close()
            raise ImproperlyConfigured(
                "This Postgres database has no sandbox.marker table, so it isn't the sandbox. "
                "Refusing to use it from a local checkout (see docs/sandbox.md)."
            )


class SevanBNetConfig(AppConfig):
    name = "sevanbnet"
    verbose_name = "Site"

    def ready(self):
        # Passkeys: accept only the admin host's own origin (see auth.get_webauthn_server).
        # allauth looks this factory up as a module global on every passkey request.
        from allauth.mfa.webauthn.internal import auth as webauthn

        from .auth import get_webauthn_server

        webauthn.get_server = get_webauthn_server

        if settings.USING_SANDBOX:
            connection_created.connect(_require_sandbox_marker, weak=False)
