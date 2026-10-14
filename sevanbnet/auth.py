import base64
import hashlib
import secrets

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core import context
from allauth.mfa.adapter import DefaultMFAAdapter
from allauth.mfa.webauthn.forms import AddWebAuthnForm
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # Accounts are made with `manage.py createsuperuser`, never from the web.
        return False


def _fernet():
    key = hashlib.sha256(b"mfa:" + settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class MFAAdapter(DefaultMFAAdapter):
    def get_public_key_credential_rp_entity(self):
        # One passkey for every *.sevanb.net host (admin. and dev-admin.). Elsewhere
        # (localhost) the passkey belongs to that host alone.
        host = context.request.get_host().partition(":")[0]
        rp_id = "sevanb.net" if host.endswith(".sevanb.net") else host
        return {"id": rp_id, "name": "sevanb.net"}

    # Backup codes are derived from a stored seed; keep it encrypted with a key from
    # DJANGO_SECRET_KEY, so a database copy alone can't reproduce the codes.
    def encrypt(self, text):
        return _fernet().encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text):
        try:
            return _fernet().decrypt(encrypted_text.encode()).decode()
        except InvalidToken:
            # Encrypted under another secret key (it was rotated): the old codes stop
            # working rather than breaking sign-in. Make new ones in the panel.
            return secrets.token_hex(40)


def get_webauthn_server():
    """allauth's passkey server, accepting only the origin of the page signing in.

    The RP ID is sevanb.net, and by default the browser-reported origin may then be any
    sevanb.net subdomain (www., dev., go.). A script on one of those sites could ask for
    Sevan's passkey on behalf of the admin, so only the admin host itself is accepted.
    """
    request = context.request
    rp = PublicKeyCredentialRpEntity(**MFAAdapter().get_public_key_credential_rp_entity())
    origin = f"{request.scheme}://{request.get_host()}"
    return Fido2Server(rp, verify_origin=lambda o: o == origin)


class AddPasskeyForm(AddWebAuthnForm):
    """New passkeys can also sign in on their own (Face ID / Touch ID), unless unticked."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "passwordless" in self.fields:
            field = self.fields["passwordless"]
            field.initial = True
            field.label = "Also sign in with this passkey alone"
            field.help_text = "No password needed; your device asks for Face ID or Touch ID."
