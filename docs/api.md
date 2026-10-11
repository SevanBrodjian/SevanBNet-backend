# Public API

Read-only JSON, no authentication, served on every backend host. The frontend calls:

| Environment | Base URL |
| --- | --- |
| Production | `https://admin.sevanb.net/api` |
| Development | `https://dev-admin.sevanb.net/api` |
| Local | `http://localhost:8000/api` |

CORS allows `https://www.sevanb.net`, `https://sevanb.net`, `https://dev.sevanb.net`, the two `*.up.railway.app` frontends and `http://localhost:5173`.

Rules that hold everywhere:

- Only rows marked **Visible** in the control panel appear. A hidden project, paper or post is a 404 and is absent from every list.
- Optional text left blank is `null`, never `""`.
- Dates are `YYYY-MM-DD` calendar dates (no time zone).
- Lists are already in display order; don't re-sort them.
- Paths in `thumbnail`, `media.src` and `media.poster` either are full URLs (uploads are on `https://cdn.jsdelivr.net/...`) or start with `/`, meaning a file in the frontend's `public/` folder (the older projects' files are in `public/media/projects/`).

## `GET /api/projects/`

Every visible project, **listed or not**. The Projects page shows only `listed: true`; an unlisted project still has its page and can be linked from papers. Order: projects with a `rank` first (lowest first), then newest first by `end`, or `start` while ongoing.

`GET /api/projects/<slug>/` returns one project (404 if hidden).

```json
{
  "slug": "llm-grounding-mazegpt",
  "title": "LLM Grounding - MazeGPT",
  "listed": true,
  "rank": null,
  "start": "2023-03-10",
  "end": "2023-04-03",
  "summary": "GPT-3 and GPT-4 finding their way through a block maze from text descriptions of their surroundings.",
  "thumbnail": "/media/projects/maze-thumb.webp",
  "glow": "#3cbd45",
  "media": { "kind": "youtube", "id": "c6Bqb5Okdh8" },
  "source": "https://github.com/SevanBrodjian/MazeGPT",
  "description": "In this project I have evaluated ...",
  "description_html": "<p>In this project I have evaluated ...</p>"
}
```

| Field | Notes |
| --- | --- |
| `slug` | The page is `/projects/<slug>`. A slug with a hand-built page in the frontend code (`learning-taichi`, `sonar-inverse-rendering`) uses that page; every other project uses the default page (media + description). |
| `listed` | Show in the Projects list only when true. |
| `start`, `end` | Either may be null. `end: null` with a `start` means ongoing. Both null: undated. |
| `summary` | The one line for the list. |
| `thumbnail` | 16:10 image for the list, or null. With no thumbnail: a terminal tile if `media.kind` is `code`, else the name tile. |
| `glow` | Hex colour for the hover glow, or null (use the default). |
| `media` | One of the shapes below, or null. Shown at the top of the default page. |
| `source` | Code link (the "Code" button), or null. |
| `description` / `description_html` | Markdown as written, and the same rendered to sanitized HTML (scripts, styles and event handlers removed; links limited to http(s), mailto and site paths). Use `description_html`; keep DOMPurify as a second layer. |

`media` shapes (`width`/`height` are pixel sizes or null):

```json
{ "kind": "image", "src": "/media/projects/thinking.webp", "alt": "...", "width": 900, "height": 400 }
{ "kind": "video", "src": "/media/projects/aussies.mp4", "poster": "/media/projects/aussies-poster.webp", "width": 960, "height": 540 }
{ "kind": "youtube", "id": "c6Bqb5Okdh8" }
{ "kind": "code", "text": "pip install s3synchrony" }
```

## `GET /api/papers/`

Every visible paper. Order: papers with a `rank` first (lowest first), then newest `date` first.

```json
{
  "id": 1,
  "key": "sonar",
  "title": "Single View Seafloor Recovery from Imaging Sonar via Differentiable Rendering",
  "authors": "Sevan Brodjian, Michael Hobley, Pietro Perona",
  "venue": "CVPR PBVS Workshop",
  "status": "Accepted",
  "date": "2026-05-22",
  "paper_url": "https://arxiv.org/abs/2605.24195",
  "project": {
    "slug": "sonar-inverse-rendering",
    "title": "Single-View Seafloor Recovery from Imaging Sonar",
    "source": "https://github.com/SevanBrodjian/sonar-inverse-rendering"
  },
  "project_url": null,
  "bibtex": "@inproceedings{brodjian2026sonar,\n  ...\n}",
  "description": "Forward-looking sonar collapses ...",
  "rank": 1
}
```

| Field | Notes |
| --- | --- |
| `key` | Short stable name for the paper's widget in frontend code (`temporal`, `sonar`, `kuramoto` today), or null. |
| `authors` | One string; highlight "Sevan Brodjian" wherever it appears. |
| `venue`, `status` | Show "Venue · Status", or just the status when `venue` is null. No status lamp. |
| `paper_url` | The Paper button (PDF or arXiv), or null. Already resolved from the old url/DOI fields. |
| `project` | The on-site project page (`/projects/<slug>`) for the Project button. Null when the paper has none **or the project is hidden**, so hiding a project removes the button instead of breaking it. `source` feeds the paper's Code button. |
| `project_url` | A project page hosted elsewhere, or null. Never set together with `project`. |
| `bibtex` | For the BibTeX button (line endings normalized, trimmed), or null. |
| `description` | Short plain-text summary for the Papers page. |

The DOI is kept in the panel but not sent.

## `GET /api/posts/`

Visible Writing posts, oldest first (the Writing page reverses them, as today). The text of each post is `content/writing/<slug>.md` in the frontend repo. `GET /api/posts/<slug>/` returns one.

```json
{ "slug": "the-direction-of-science", "title": "The Direction of Science", "description": "How our choices shape the Universe we understand.", "date": "2024-05-30" }
```

## `GET /api/site/`

Site-wide text, edited under Site settings.

```json
{
  "home_line": "Generative models and simulators for next-generation virtual environments.",
  "role": "PhD Student, Computation and Neural Systems, Caltech",
  "about": ["I study perception as ...", "My current research ...", "Long-term, I aim ..."]
}
```

`about` is the About page's paragraphs in order. `role` is the tag shown with the name on the home page.
