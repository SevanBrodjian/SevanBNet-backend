from allauth.account.adapter import DefaultAccountAdapter
from allauth.core import context
from allauth.mfa.adapter import DefaultMFAAdapter
from allauth.mfa.webauthn.forms import AddWebAuthnForm


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # Accounts are made with `manage.py createsuperuser`, never from the web.
        return False


class MFAAdapter(DefaultMFAAdapter):
    def get_public_key_credential_rp_entity(self):
        # One passkey for every *.sevanb.net host (admin. and dev-admin.). Elsewhere
        # (localhost) the passkey belongs to that host alone.
        host = context.request.get_host().partition(":")[0]
        rp_id = "sevanb.net" if host.endswith(".sevanb.net") else host
        return {"id": rp_id, "name": "sevanb.net"}


class AddPasskeyForm(AddWebAuthnForm):
    """New passkeys can also sign in on their own (Face ID / Touch ID), unless unticked."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "passwordless" in self.fields:
            field = self.fields["passwordless"]
            field.initial = True
            field.label = "Also sign in with this passkey alone"
            field.help_text = "No password needed; your device asks for Face ID or Touch ID."
