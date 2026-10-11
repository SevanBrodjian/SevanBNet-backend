# The control panel

| | Address | Data |
| --- | --- | --- |
| Production | https://admin.sevanb.net | the real site |
| Development | https://dev-admin.sevanb.net | the sandbox (a copy of production, see [sandbox.md](sandbox.md)) |
| Local | http://localhost:8000/admin/ | `db.sqlite3`, or the sandbox |

The badge at the top right says which one you're in. The panel exists only at these addresses; go.sevanb.net and the `*.up.railway.app` addresses serve the API and QR links and nothing else.

## Signing in

On admin.sevanb.net and dev-admin.sevanb.net:

- **Password, then passkey.** Enter your username and password, then confirm with your passkey (Face ID or Touch ID).
- **Passkey alone.** "Sign in with a passkey" skips the password.
- **Trust this browser.** After the passkey step you can trust the browser for 30 days; it then asks only for your password. Trust ends early if your password or passkeys change. Only do this on your own devices.
- **Backup codes.** If you have no passkey at hand, the passkey step also takes one of your backup codes. Each works once.
- After 5 failed sign-ins from one network, sign-in is paused there for an hour. Sessions last 3 days ("Remember me"), or until the browser closes.

Locally the panel is password only.

### First sign-in: add your passkey

The first time you sign in on admin.sevanb.net, the panel sends you to "Add a passkey" before anything else.

1. Keep "Also sign in with this passkey alone" ticked and press **Add passkey**. Safari or Chrome asks to save it to iCloud Keychain; confirm with Face ID or Touch ID.
2. The next page shows your 10 **backup codes**, once. Download them or put them in your password manager, then tick "I've saved these codes".

The passkey belongs to sevanb.net, so the same one works on dev-admin.sevanb.net and syncs to your iPhone and Mac. To add another (say, a hardware key) or make new backup codes: the site menu at the top left, or your name at the bottom left, then **Passkeys and backup codes**.

## What Visible and Listed do

Every project, paper and post has **Visible**. Off means it's gone from the site everywhere, as if it never existed: no page (a 404), not in any list, not in the API. Hidden papers stay hidden; nothing else needs to change.

Projects also have **Listed on Projects page**:

| Visible | Listed | Result |
| --- | --- | --- |
| on | on | Has a page and is in the Projects list. |
| on | off | Has a page (papers can link to it) but isn't in the Projects list. |
| off | either | No page at all. Papers that link to it lose their Project button; the panel warns you and names them. |

## Site settings

The home page line, the role shown with your name, and the About text (paragraphs separated by a blank line).

## Projects

Each project gets one of two kinds of page:

- **Default page:** the media at the top, then the description. Fill in "Default page": the media type and media (an image or video URL, a YouTube link, or a terminal command), and the description in Markdown.
- **Hand-built page:** written in the frontend code, like Learning Taichi and the Sonar project. The project still needs its entry here, with the same slug as the code, for its title, dates, one-liner, thumbnail and visibility. Its "Default page" fields are ignored.

To add a project: **Projects → +**. Title (the slug fills in), dates (leave End blank while ongoing), the one-line summary, a 16:10 thumbnail, and optionally a glow colour and Source (the code link). **Rank** is usually blank; ranked projects come first, lowest number first, and the rest are newest first. Learning Taichi is 1 and the Sonar project 2, so they stay at the top as now.

A project's title and summary are its own, independent of any paper's title.

## Papers

Title, authors (as they should read; your name is highlighted automatically), venue (blank for preprints), status, date, the paper link (PDF or arXiv) and a short description. The site shows "Venue · Status", or just the status.

**Project:** pick the project from the dropdown if the paper has a project page on this site (the Sonar paper → the Sonar project). Use "External project page" only for a page hosted elsewhere; not both. Papers never get pages of their own.

**BibTeX** is what the BibTeX button shows. **Widget key** connects the paper to its interactive figure in the frontend code (`temporal`, `sonar`, `kuramoto`); leave it blank for papers without one. The DOI is kept for reference and not shown.

## Writing

Each post's title, slug, date, description and visibility live here. The text is the Markdown file `content/writing/<slug>.md` in the frontend repo, so a new post means adding that file and a row here with the same slug.

## Media

**Media → +** uploads one file (images, MP4/WebM video or PDF, up to 20 MB) to the media repo on GitHub. It's served from a permanent jsDelivr URL tied to that upload, so it never changes or goes stale. The list shows each file's URL to copy, and a project's thumbnail, media and poster fields suggest every uploaded file as you type. Those fields also take any other URL.

Long videos belong on YouTube (jsDelivr is for modest files). Removing a row here doesn't delete the file from the repo.

## Rebuild site

Edits show on the site straight away. The copies of each page that search engines read are made when the site is built, so after editing, press **Rebuild site** (on the overview page, or in the site menu at the top left). It redeploys the frontend of the same environment and takes a few minutes.

## QR codes

The QR manager, as before, now inside the panel: create, retarget, restyle, download, see scans. Short links stay on go.sevanb.net.

## Setup reference

Railway variables (names only):

| Service / environment | Variable | Value |
| --- | --- | --- |
| backend_django, both | `MEDIA_REPO` | `SevanBrodjian/SevanBNet-media` |
| backend_django, both | `GITHUB_MEDIA_TOKEN` | fine-grained GitHub token: only SevanBNet-media, Contents read/write |
| backend_django, both | `RAILWAY_DEPLOY_TOKEN` | Railway project token for that environment |
| backend_django, development | `FRONTEND_SERVICE_ID` | `${{frontend_dev.RAILWAY_SERVICE_ID}}` (or the ID pasted from the service's settings) |
| backend_django, production | `FRONTEND_SERVICE_ID` | `${{frontend_prod.RAILWAY_SERVICE_ID}}` (likewise) |
| backend_django, production | `SANDBOX_SOURCE_URL` | see [sandbox.md](sandbox.md); read only by `scripts/sandbox-refresh` |
| backend_django, both (later) | `DATABASE_URL` | `${{Postgres_db.DATABASE_PRIVATE_URL}}` (private network) |
| frontend_dev, frontend_prod | `NO_CACHE` | `1`, so a rebuild always re-renders the pages |

Without `MEDIA_REPO` and `GITHUB_MEDIA_TOKEN`, Media explains this and uploading is off. Without `RAILWAY_DEPLOY_TOKEN` and `FRONTEND_SERVICE_ID`, Rebuild site is off with a note. Neither token is ever shown or logged.

Custom domains: `admin.sevanb.net` on the production backend_django service, `dev-admin.sevanb.net` on the development one. Each needs the CNAME record Railway shows when you add the domain (and the TXT record if Railway asks for one), added in Squarespace DNS.
