# Data Access

How the `client` layer reads data from NU Moodle once `auth` has a valid session.
See [authentication.md](authentication.md) for how the session is obtained.

## Method: Cookie + `/lib/ajax/service.php`

We use the **session cookie** (the `MoodleSession` cookie held in Playwright
`storage_state`) together with Moodle's internal AJAX endpoint — the same one
the Moodle web UI calls. We do **not** use web-service tokens (`wstoken`):
NU logs in through Microsoft Entra ID, so `/login/token.php` cannot mint a token
(see authentication.md).

At the network level this is **one endpoint for almost every read**. Only the
method name changes:

```
POST /lib/ajax/service.php?info=<method>&sesskey=<sesskey>
Content-Type: application/json

[{"index":0,"methodname":"<method>","args":{ ... }}]
```

- `sesskey` is required on every call. There is no endpoint that returns it —
  read it from `M.cfg.sesskey` in the HTML of any logged-in page (e.g. `/my/`).
  Read `M.cfg.userId` at the same time; some methods need the user id.
- Error codes (all observed live on NU, 2026-09-30):
  - `servicerequireslogin` — no/expired session (checked before `sesskey`).
    Treat as session expired.
  - `invalidsesskey` — session alive but `sesskey` stale/wrong. Re-read it from
    `/my/` and retry once.
  - `missingparam` (sesskey) — `sesskey` omitted from the URL.
  - `servicenotavailable` — function not AJAX-enabled; use a page route.
- `service.php` only serves functions flagged `ajax => true` in Moodle. Reads
  mostly are; some reports/writes are not, and those go through a page route
  instead (see below).

The `client` layer therefore exposes two primitives:

1. `call(method, args)` → POST to `service.php` with `sesskey` (primary path).
2. `fetch_page(path)` → GET HTML, for the cases `service.php` won't serve.

Implemented in `moodle_mcp/client.py` as `MoodleClient` (`connect(context)` reads
`sesskey`/`userId` from `/my/`). `call()` retries once after re-reading `sesskey`
on `invalidsesskey`. `servicerequireslogin`, or a page redirect to `/login/`,
raises `SessionExpiredError`. Other errors raise `MoodleError(errorcode)`.

## Methods by domain

Each `tools/` domain maps to specific methods. All go through
`POST /lib/ajax/service.php?info=<method>` unless marked **(page)**.

### Bootstrap / identity
- (page) `GET /my/` — read `M.cfg.sesskey` and `M.cfg.userId` from the page.
  Required before any `call()`. Lives in `client` startup, not a tool.

### Courses
- `core_course_get_enrolled_courses_by_timeline_classification` — the user's
  courses (dashboard "Course overview" block). Args: `classification`
  (`inprogress` | `future` | `past` | `all` | `favourites` | `hidden`),
  `limit`, `offset`, `sort`.
- `core_course_get_recent_courses` — recently accessed courses (optional).

### Course content (`tools/courses.py`)
- `core_courseformat_get_state` — the course index the UI itself uses. Args:
  `courseid`. Returns a **JSON string** (decode it again) with `section[]`
  (`number`, `title`, `cmlist`) and `cm[]` (`id`, `module`, `name`, `url`,
  `uservisible`). Ids are strings. **`module` is the plugin key** (`resource`);
  `modname` is only the display label ("File"). Labels have no `url`. No course
  name in the payload, so use the courses method for that.
- `core_course_get_contents` is **not** served on NU (`servicenotavailable`), but
  get_state makes course-page scraping unnecessary.

### Course materials (`tools/materials.py`)
All verified live with the cookie context:
- **resource**: `/mod/resource/view.php?id=<cmid>&redirect=1` → `303` →
  `/pluginfile.php/<ctx>/mod_resource/content/<rev>/<file>`. The filename is the
  last URL segment, so it's known before downloading. `redirect=1` forces the
  redirect even when the display mode is "embed".
- **folder**: `/mod/folder/view.php?id=<cmid>` (HTML) links every file as
  `/pluginfile.php/<ctx>/mod_folder/content/<rev>/<subdirs...>/<file>`, sometimes
  twice (with `?forcedownload=1`). Folders **can have subdirectories**; keep them.
- **url**: `/mod/url/view.php?id=<cmid>&redirect=1` → `303`, `Location` = the
  external target. Don't follow it.
- `pluginfile.php` returns the bytes with `content-disposition: inline; filename=…`.
  A sample course took 32 files / 161 MB in ~60 s sequentially.

### Deadlines
- `core_calendar_get_action_events_by_timesort` — the deadlines feed
  ("Timeline" block). Args: `timesortfrom`, `timesortto`, `limitnum`.
  Assignment/quiz due dates surface here as action events (`modulename`,
  `instance`, `url`, `timesort`, `overdue`). Returns only *actionable* items
  (for example, assignments not yet submitted). Overdue ones stay listed, so query from
  a point in the past to include them. `name` arrives **HTML-entity-encoded**
  (`E&#38;M`), so unescape it.
- `core_calendar_get_action_events_by_course` — same, scoped to one course.

### Calendar (optional, fuller view)
- `core_calendar_get_calendar_upcoming_view` — upcoming events.
- `core_calendar_get_calendar_monthly_view` — month grid.

### Assignments
- (page) `GET /mod/assign/view.php?id=<cmid>` — `div.submissionstatustable
  table tr` holds `th`/`td` pairs (Submission status, Grading status, Last
  modified, …). The "Submission comments" row holds a JS template; skip it.
  The sampled page showed **no due dates**, so take them from the deadline events.
  `mod_assign_get_submission_status` is **not** served on NU.

### Grades
- (page) `GET /grade/report/user/index.php?id=<courseid>` — scrape (returns 200).
  No grade AJAX method is served on NU: `gradereport_user_get_grade_items`,
  `gradereport_user_get_grades_table` and `gradereport_overview_get_course_grades`
  all return `servicenotavailable`.
  Markup: `table.user-grade` rows. Category header rows have only a `th`. Item
  rows have `th.column-itemname` (the name is in `.rowtitle`, after a type label
  such as "External tool") and `td.column-grade` (value in the first inner
  `div`, followed by an "Actions" menu), plus `column-range`, `column-percentage`
  and `column-feedback`. The last row is "Course total".

### Messages / notifications (optional)
- `core_message_get_conversations` — inbox.
- `message_popup_get_popup_notifications` — notifications.

## Verified on NU (2026-09-30)

Probed live with a logged-in session:

| Method | Served via `service.php`? |
|--------|---------------------------|
| `core_course_get_enrolled_courses_by_timeline_classification` | yes |
| `core_course_get_recent_courses` | yes |
| `core_calendar_get_action_events_by_timesort` | yes |
| `core_calendar_get_action_events_by_course` | yes |
| `core_calendar_get_calendar_upcoming_view` | yes |
| `core_calendar_get_calendar_monthly_view` | yes |
| `core_message_get_conversations` | yes |
| `message_popup_get_popup_notifications` | yes |
| `core_courseformat_get_state` | yes (replaces course-page scraping) |
| `core_course_get_contents` | **no** (use get_state) |
| `mod_assign_get_submission_status` | **no** → assignment page |
| `gradereport_user_get_grade_items` / `_get_grades_table` | **no** → grade report page |
| `gradereport_overview_get_course_grades` | **no** → grade report page |

`M.cfg.sesskey` and `M.cfg.userId` are present in the `/my/` HTML as described.
`pluginfile.php` downloads work with the cookie context.

NU is on Moodle 5.1 (error links resolve to `docs.moodle.org/501/...`).
