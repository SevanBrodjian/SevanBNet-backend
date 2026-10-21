import base64
import json
from datetime import UTC, date, datetime
from unittest import mock

from allauth.mfa.models import Authenticator
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, override_settings

from .auth import MFAAdapter
from .models import BlogPost, Media, Project, Publication, QRRedirect, SiteSettings


def panel_client(host="admin.sevanb.net"):
    return Client(HTTP_HOST=host)


def staff(client, **extra):
    user = User.objects.create_user("sevan", password="pw-for-tests", is_staff=True, **extra)
    client.force_login(user)
    return user


class ApiTests(TestCase):
    def setUp(self):
        Project.objects.all().delete()  # the rows the migration creates

    def test_projects_hide_invisible_and_flag_unlisted(self):
        Project.objects.create(title="Shown", slug="shown", summary="One line.")
        Project.objects.create(title="Hidden", slug="hidden", visible=False)
        Project.objects.create(title="Unlisted", slug="unlisted", listed=False)
        projects = {p["slug"]: p for p in self.client.get("/api/projects/").json()}
        self.assertEqual(set(projects), {"shown", "unlisted"})
        self.assertFalse(projects["unlisted"]["listed"])
        self.assertFalse(projects["unlisted"]["standalone"])
        self.assertEqual(self.client.get("/api/projects/hidden/").status_code, 404)
        self.assertEqual(self.client.get("/api/projects/unlisted/").status_code, 200)

    def test_project_shape(self):
        Project.objects.create(
            title="Maze",
            slug="maze",
            media_kind="youtube",
            media="https://www.youtube.com/watch?v=c6Bqb5Okdh8",
            description="Line one\n\n<script>x()</script>**bold**",
        )
        data = self.client.get("/api/projects/maze/").json()
        self.assertEqual(data["media"], {"kind": "youtube", "id": "c6Bqb5Okdh8"})
        self.assertIn("<p><strong>bold</strong></p>", data["description_html"])
        self.assertNotIn("script", data["description_html"])
        self.assertIsNone(data["thumbnail"])  # blank fields are null

    def test_papers_link_only_to_visible_projects(self):
        shown = Project.objects.create(title="Sonar", slug="sonar", source="https://github.com/s")
        hidden = Project.objects.create(title="Gone", slug="gone", visible=False)
        Publication.objects.create(title="A", status="Accepted", project=shown, rank=1)
        Publication.objects.create(title="B", status="Accepted", project=hidden, rank=2)
        Publication.objects.create(title="C", status="Under Review", visible=False)
        papers = self.client.get("/api/papers/").json()
        self.assertEqual([p["title"] for p in papers], ["A", "B"])
        self.assertEqual(
            papers[0]["project"],
            {"slug": "sonar", "title": "Sonar", "source": "https://github.com/s"},
        )
        self.assertIsNone(papers[1]["project"])
        self.assertEqual(
            set(papers[0]),
            {"id", "key", "title", "authors", "venue", "status", "date", "paper_url", "project"}
            | {"project_url", "bibtex", "description", "rank"},
        )

    def test_posts_and_site_settings(self):
        BlogPost.objects.create(title="Shown", slug="shown", date=date(2024, 5, 30))
        BlogPost.objects.create(title="Hidden", slug="hidden", visible=False)
        self.assertEqual(
            self.client.get("/api/posts/").json(),
            [{"slug": "shown", "title": "Shown", "description": None, "date": "2024-05-30"}],
        )
        site = self.client.get("/api/site/").json()
        self.assertEqual(site["role"], "PhD Student, Computation and Neural Systems, Caltech")
        self.assertEqual(len(site["about"]), 3)
        self.assertTrue(site["writing_note"].startswith("Warning: the following are my"))
        self.assertTrue(site["writing_note_html"].startswith("<p>Warning: the following"))
        self.assertEqual(site["about_html"].count("<p>"), 3)

    def test_site_text_markdown(self):
        settings = SiteSettings.load()
        settings.writing_note = (
            "First line\nsecond *line*\n\n[Link](https://example.com) <script>x</script>"
        )
        settings.save()
        html = self.client.get("/api/site/").json()["writing_note_html"]
        self.assertIn("First line<br>\nsecond <em>line</em>", html)
        self.assertIn('<a href="https://example.com"', html)
        self.assertNotIn("<script>", html)


class HostTests(TestCase):
    def test_panel_only_on_admin_hosts(self):
        for host in ["go.sevanb.net", "sevanbnet-backend-production.up.railway.app"]:
            client = panel_client(host)
            self.assertEqual(client.get("/admin/login/").status_code, 404, host)
            self.assertEqual(client.get("/accounts/login/").status_code, 404, host)
            self.assertEqual(client.get("/admin/qr/api/redirects/").status_code, 404, host)
            self.assertEqual(client.get("/api/projects/").status_code, 200, host)
        panel = panel_client()
        self.assertRedirects(panel.get("/"), "/admin/", fetch_redirect_response=False)
        response = panel.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("frame-ancestors 'self'", response["Content-Security-Policy"])

    def test_every_response_is_noindex(self):
        for url in ["/", "/healthz/", "/api/projects/", "/admin/login/"]:
            self.assertEqual(self.client.get(url)["X-Robots-Tag"], "noindex, nofollow", url)

    def test_passkey_relying_party_covers_both_admin_hosts(self):
        from allauth.core import context

        for host, rp_id in [("admin.sevanb.net", "sevanb.net"), ("localhost:8000", "localhost")]:
            with context.request_context(RequestFactory().get("/", HTTP_HOST=host)):
                self.assertEqual(MFAAdapter().get_public_key_credential_rp_entity()["id"], rp_id)


class SignInTests(TestCase):
    def test_lockout_after_five_failures_from_any_address(self):
        User.objects.create_user("sevan", password="right-password", is_staff=True)
        client = panel_client("localhost")
        for i in range(5):
            client.post(
                "/admin/login/",
                {"username": "sevan", "password": "wrong"},
                REMOTE_ADDR=f"10.0.0.{i}",
            )
        response = client.post("/admin/login/", {"username": "sevan", "password": "right-password"})
        self.assertEqual(response.status_code, 429)

    def test_passkeys_accept_only_the_admin_origin(self):
        from allauth.core import context
        from allauth.mfa.webauthn.internal import auth as webauthn

        request = RequestFactory().get("/", HTTP_HOST="admin.sevanb.net", secure=True)
        with context.request_context(request):
            server = webauthn.get_server()
        self.assertEqual(server.rp.id, "sevanb.net")
        self.assertTrue(server._verify("https://admin.sevanb.net"))
        for origin in ["https://www.sevanb.net", "https://dev.sevanb.net", "https://go.sevanb.net"]:
            self.assertFalse(server._verify(origin), origin)

    def test_backup_code_seed_is_encrypted(self):
        from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes

        user = User.objects.create_user("sevan")
        codes = RecoveryCodes.activate(user)
        self.assertNotRegex(codes.instance.data["seed"], r"^[0-9a-f]{80}$")
        self.assertTrue(codes.validate_code(codes.get_unused_codes()[0]))

    @override_settings(REQUIRE_PASSKEY=True)
    def test_staff_must_add_a_passkey_first(self):
        client = panel_client()
        user = staff(client)
        self.assertRedirects(
            client.get("/admin/"), "/accounts/2fa/webauthn/add/", fetch_redirect_response=False
        )
        Authenticator.objects.create(user=user, type=Authenticator.Type.WEBAUTHN, data={})
        self.assertEqual(client.get("/admin/").status_code, 200)


class PanelTests(TestCase):
    def test_hiding_a_linked_project_warns(self):
        client = panel_client()
        staff(client, is_superuser=True)
        project = Project.objects.create(title="Sonar", slug="sonar")
        Publication.objects.create(title="The sonar paper", status="Accepted", project=project)
        data = {
            "title": "Sonar",
            "slug": "sonar",
            "listed": "on",
            "media_kind": "",
            "description": "",
        }
        response = client.post(f"/admin/sevanbnet/project/{project.pk}/change/", data, follow=True)
        self.assertFalse(Project.objects.get(pk=project.pk).visible)
        self.assertContains(response, "no longer show a Site button: The sonar paper")

    def test_saving_content_rebuilds_the_site_soon(self):
        client = panel_client()
        staff(client, is_superuser=True)
        project = Project.objects.create(title="Sonar", slug="sonar")
        data = {"title": "Sonar 2", "slug": "sonar", "visible": "on", "listed": "on"}
        data |= {"media_kind": "", "description": ""}
        with mock.patch("sevanbnet.rebuild.soon", return_value=True) as soon:
            response = client.post(
                f"/admin/sevanbnet/project/{project.pk}/change/", data, follow=True
            )
        soon.assert_called_once()
        self.assertContains(response, "The site rebuilds itself")

    def test_rebuild_soon_waits_for_the_last_edit(self):
        from . import rebuild

        with (
            override_settings(
                RAILWAY_DEPLOY_TOKEN="t", FRONTEND_SERVICE_ID="s", RAILWAY_ENVIRONMENT_ID="e"
            ),
            mock.patch.object(rebuild, "SETTLE", 0.05),
            mock.patch.object(rebuild, "rebuild") as deploy,
        ):
            for _ in range(3):
                self.assertTrue(rebuild.soon())
            rebuild._timer.join()
        deploy.assert_called_once()
        self.assertFalse(rebuild.soon())  # not configured here

    def test_media_upload_commits_to_github(self):
        client = panel_client()
        staff(client, is_superuser=True)
        upload = SimpleUploadedFile("Maze Thumb.webp", b"webp-bytes")
        answer = mock.MagicMock()
        answer.__enter__.return_value.read.return_value = json.dumps({"commit": {"sha": "abc123"}})
        with (
            override_settings(MEDIA_REPO="sevan/media", GITHUB_MEDIA_TOKEN="secret-token"),
            mock.patch("sevanbnet.media.urllib.request.urlopen", return_value=answer) as urlopen,
        ):
            client.post("/admin/sevanbnet/media/add/", {"file": upload, "folder": "projects"})
        item = Media.objects.get()
        self.assertEqual(item.path, "projects/maze-thumb.webp")
        self.assertEqual(
            item.url, "https://cdn.jsdelivr.net/gh/sevan/media@abc123/projects/maze-thumb.webp"
        )
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.github.com/repos/sevan/media/contents/projects/maze-thumb.webp",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(base64.b64decode(json.loads(request.data)["content"]), b"webp-bytes")

    def test_media_upload_is_disabled_without_configuration(self):
        client = panel_client()
        staff(client, is_superuser=True)
        response = client.get("/admin/sevanbnet/media/add/")
        self.assertRedirects(response, "/admin/sevanbnet/media/", fetch_redirect_response=False)
        self.assertContains(client.get("/admin/sevanbnet/media/"), "Uploading isn't set up")


class QRTests(TestCase):
    @override_settings(ON_RAILWAY=True)
    def test_qr_redirect_logs_scan(self):
        qr = QRRedirect.objects.create(
            short_code="cv", label="CV", target_url="https://example.com"
        )
        response = self.client.get(
            "/r/cv/", HTTP_X_REAL_IP="1.2.3.4", HTTP_X_FORWARDED_FOR="6.6.6.6"
        )
        self.assertRedirects(response, "https://example.com", fetch_redirect_response=False)
        self.assertEqual(qr.scans.get().ip_address, "1.2.3.4")

    def test_qr_management_is_staff_only(self):
        qr = QRRedirect.objects.create(
            short_code="cv", label="CV", target_url="https://example.com"
        )
        client = panel_client()
        self.assertEqual(client.get("/admin/qr/api/redirects/").status_code, 403)
        self.assertEqual(client.get(f"/admin/qr/image/{qr.id}/").status_code, 302)
        staff(client, is_superuser=True)
        self.assertEqual(client.get("/admin/qr/").status_code, 200)
        self.assertEqual(client.get(f"/admin/qr/image/{qr.id}/").status_code, 200)


class LegacyTests(TestCase):
    def test_old_site_urls_redirect_permanently_to_the_real_site(self):
        Project.objects.create(title="LLM Grounding - MazeGPT", slug="llm-grounding-mazegpt")
        BlogPost.objects.create(title="How Reality Ends: An Exploration", slug="how-reality-ends")
        cases = {
            "/": "https://www.sevanb.net",
            "/home/": "https://www.sevanb.net/",
            "/research/": "https://www.sevanb.net/research",
            "/projects/LLM_Grounding_-_MazeGPT": "https://www.sevanb.net/projects/llm-grounding-mazegpt",
            "/projects/llm-grounding-mazegpt": "https://www.sevanb.net/projects/llm-grounding-mazegpt",
            "/projects/unknown": "https://www.sevanb.net/projects",
            "/blog/How-Reality-Ends0-An-Exploration": "https://www.sevanb.net/blog/how-reality-ends",
        }
        for url, target in cases.items():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 301, url)
            self.assertEqual(response["Location"], target, url)


class ContentMigrationTests(TransactionTestCase):
    """0032 keeps every value and maps the old fields onto the new ones."""

    serialized_rollback = True
    before = [("sevanbnet", "0031_blogpost_is_published_project_is_published_and_more")]
    after = [("sevanbnet", "0032_content_model")]

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.migrate(target)
        return executor.loader.project_state(target).apps

    def test_migration_maps_old_data(self):
        old = self.migrate(self.before)
        try:
            self.make_old_rows(old)
            new = self.migrate(self.after)
            self.check_new_rows(new)
            # And back again, without errors.
            self.migrate(self.before)
        finally:
            self.migrate(self.after)

    def make_old_rows(self, apps):
        Project = apps.get_model("sevanbnet", "Project")
        Publication = apps.get_model("sevanbnet", "Publication")
        BlogPost = apps.get_model("sevanbnet", "BlogPost")
        Project.objects.create(
            title="Maze",
            slug="llm-grounding-mazegpt",
            independent=True,
            is_published=False,
            link="https://github.com/SevanBrodjian/MazeGPT",
            img="https://www.youtube.com/embed/c6Bqb5Okdh8?mute=1&hd=1",
        )
        Project.objects.create(title="Old Thing", independent=True, img="/x/old.png")
        paper = {"description": "d", "first_author": False}
        Publication.objects.create(
            title="Single View Seafloor Recovery from Imaging Sonar",
            is_published=True,
            journal_name="CVPR PBVS Workshop",
            status="Accepted",
            citation="@inproceedings{x,\r\n  title={Sonar}\r\n}\r\n",
            url="https://arxiv.org/abs/2605.24195",
            site_path="/papers/sonar-rendering",
            project_url="https://go.sevanb.net/r/sonar-rendering",
            publication_date=datetime(2026, 5, 22, 5, tzinfo=UTC),
            submission_date=datetime(2026, 3, 8, 6, tzinfo=UTC),
            **paper,
        )
        Publication.objects.create(
            title="LITT: Hidden",
            is_published=False,
            status="Under Review",
            doi="10.1000/litt",
            project_url="https://example.org/litt",
            submission_date=datetime(2026, 5, 2, 5, tzinfo=UTC),
            **paper,
        )
        Publication.objects.create(
            title="Training-Free Temporal Abstraction for General Video Understanding",
            status="Under Review",
            project_url="https://www.sevanb.net/projects/llm-grounding-mazegpt",
            **paper,
        )
        BlogPost.objects.create(title="Post", description="d", content="text", slug="post")

    def check_new_rows(self, apps):
        Project = apps.get_model("sevanbnet", "Project")
        Publication = apps.get_model("sevanbnet", "Publication")
        SiteSettings = apps.get_model("sevanbnet", "SiteSettings")

        maze = Project.objects.get(slug="llm-grounding-mazegpt")
        self.assertFalse(maze.visible)
        self.assertEqual(maze.source, "https://github.com/SevanBrodjian/MazeGPT")
        self.assertEqual(maze.media, "https://www.youtube.com/watch?v=c6Bqb5Okdh8")
        self.assertEqual(maze.thumbnail, "/media/projects/maze-thumb.webp")
        self.assertTrue(maze.summary.startswith("GPT-3 and GPT-4"))
        old = Project.objects.get(title="Old Thing")
        self.assertEqual(
            (old.slug, old.thumbnail, old.media_kind), ("old-thing", "/x/old.png", "image")
        )

        sonar_project = Project.objects.get(slug="sonar-inverse-rendering")
        self.assertEqual(
            (sonar_project.rank, sonar_project.visible, sonar_project.listed), (2, True, True)
        )
        self.assertTrue(Project.objects.filter(slug="learning-taichi", rank=1).exists())

        sonar = Publication.objects.get(key="sonar")
        self.assertEqual(sonar.project_id, sonar_project.id)
        self.assertEqual((sonar.project_url, sonar.venue), ("", "CVPR PBVS Workshop"))
        self.assertEqual(sonar.date, date(2026, 5, 22))
        self.assertEqual(sonar.paper_url, "https://arxiv.org/abs/2605.24195")
        self.assertEqual(sonar.bibtex, "@inproceedings{x,\n  title={Sonar}\n}")

        litt = Publication.objects.get(title="LITT: Hidden")
        self.assertFalse(litt.visible)
        self.assertEqual(litt.date, date(2026, 5, 2))
        self.assertEqual(litt.paper_url, "https://doi.org/10.1000/litt")
        self.assertEqual((litt.project_id, litt.project_url), (None, "https://example.org/litt"))

        temporal = Publication.objects.get(key="temporal")
        self.assertEqual(temporal.project_id, maze.id)
        self.assertIn("eprint={2608.27929}", temporal.bibtex)

        self.assertIn("Generative models", SiteSettings.objects.get().home_line)
