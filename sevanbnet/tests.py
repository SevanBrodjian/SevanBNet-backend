from django.contrib.auth.models import User
from django.test import TestCase

from .models import Project, QRRedirect


class SiteTests(TestCase):
    def test_api_lists_only_published_projects(self):
        Project.objects.create(title="Shown", independent=True)
        Project.objects.create(title="Hidden", independent=True, is_published=False)
        titles = [p["title"] for p in self.client.get("/api/projects/").json()]
        self.assertEqual(titles, ["Shown"])

    def test_every_response_is_noindex(self):
        for url in ["/", "/healthz/", "/api/projects/", "/admin/login/"]:
            self.assertEqual(self.client.get(url)["X-Robots-Tag"], "noindex, nofollow", url)

    def test_qr_redirect_logs_scan(self):
        qr = QRRedirect.objects.create(
            short_code="cv", label="CV", target_url="https://example.com"
        )
        response = self.client.get("/r/cv/", HTTP_X_FORWARDED_FOR="6.6.6.6, 1.2.3.4")
        self.assertRedirects(response, "https://example.com", fetch_redirect_response=False)
        self.assertEqual(qr.scans.get().ip_address, "1.2.3.4")

    def test_qr_management_is_staff_only(self):
        qr = QRRedirect.objects.create(
            short_code="cv", label="CV", target_url="https://example.com"
        )
        self.assertEqual(self.client.get("/api/qr/redirects/").status_code, 403)
        self.assertEqual(self.client.get(f"/api/qr/image/{qr.id}/").status_code, 302)
        User.objects.create_user("staff", password="x", is_staff=True)
        self.client.login(username="staff", password="x")
        self.assertEqual(self.client.get(f"/api/qr/image/{qr.id}/").status_code, 200)
