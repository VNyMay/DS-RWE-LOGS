# Digital Society Casebook

A searchable repository of real-world technology cases, impacts, and ethical issues, built for IB Digital Society.

Visitors browse and search approved cases. Contributors submit new cases through a structured form with sources and their name. A moderator approves, rejects, edits, archives or deletes submissions. Every case is tagged **SL** (Standard Level) or **HL** (Higher Level).

Built with Python and Streamlit. Local data lives in SQLite; the data layer is ready for PostgreSQL/Supabase.

## Features

- **Home** with headline metrics, recently added cases, popular categories, SL and HL sections, and a "how it works" guide.
- **Browse** with keyword search across every descriptive field, independent filters (SL/HL, category, technology, country, year range, ethical issue), five sort orders including relevance, pagination, and a full detail page per case.
- **Submit** as a three-step guided form (the case, analysis, source and name) with the deeper analysis fields folded into an optional section, clear required-field marking, friendly validation, duplicate-title warnings, and a confirmation screen. Empty optional fields are stored as NULL. A required text field can be skipped by typing a single dash; the title is the only field that cannot be skipped, and a case without a source cannot be approved until a moderator adds one.
- **3Cs tagging**: every case can be tagged with the seven Digital Society concepts (Change, Expression, Identity, Power, Space, Systems, Values and ethics), the content strands (Data, Algorithms, Computers, Networks and the internet, Media, Artificial intelligence) and the contexts (Cultural, Economic, Environmental, Health, Human knowledge, Political, Social). All three are filters on Browse and charts on Analytics. HL cases can also record an HL extension challenge (global well-being, governance and human rights, sustainable development) and the intervention that addressed it.
- **Edit codes**: every submission gets a short code (for example `K7PQ-3XMZ`) shown on the confirmation screen. Entering it on the Submit page reopens the case for editing while it is still pending; once a moderator has reviewed it, changes go through the admin.
- **Admin / Review** protected by a password from secrets: pending queue with search, approve / reject / edit / archive / restore / delete (with confirmation), private reviewer notes, an all-records view, CSV export (public export never includes reviewer notes), and a demo-data cleaner.
- **Analytics** with charts by course level, year, category, ethical issue, technology and country, each with a table view, and an empty state when there is nothing to chart.
- Clean white interface with a deep-green accent, adapted from the Secure_Lan / EXVIN design language.

## Project structure

```
digital-society-casebook/
├── app.py                  # entry point: theme, database setup, navigation
├── config.py               # app name, categories, ethical issues, levels, limits, secrets helpers
├── database.py             # ALL SQL lives here (SQLite now, PostgreSQL-ready)
├── validation.py           # validation rules, placeholder cleaning, URL checks
├── ui.py                   # theme tokens, CSS, reusable visual blocks (badges, metrics, empty states)
├── seed_data.py            # add / remove demonstration records
├── components/
│   ├── cards.py            # example cards and grids
│   ├── detail.py           # the full detail view
│   ├── forms.py            # the shared submission / edit form
│   ├── messages.py         # success, warning, error and validation messages
│   └── navigation.py       # page switching, admin session, query-string helpers
├── screens/
│   ├── home.py
│   ├── browse.py
│   ├── submit.py
│   ├── analytics.py
│   └── admin.py
├── assets/                 # logo and icon (SVG)
├── data/                   # examples.db is created here (git-ignored)
├── tests/                  # pytest suite for the database and validation layers
├── .streamlit/
│   ├── config.toml         # theme and server settings
│   └── secrets.toml.example
├── requirements.txt
└── requirements-dev.txt
```

## Install

Python 3.10 or newer.

```powershell
cd digital-society-casebook
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS / Linux use `source .venv/bin/activate`.

## Configure the admin password

Copy the example secrets file and set a password:

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Then edit `.streamlit/secrets.toml`:

```toml
ADMIN_PASSWORD = "a-long-random-password"
```

`secrets.toml` is git-ignored and must never be committed. An `ADMIN_PASSWORD` environment variable works too (secrets take priority). Without a password the Admin page shows setup instructions and stays locked.

## Run

```powershell
streamlit run app.py
```

Open http://localhost:8501. The database is created automatically on first run.

Optional demonstration data (eight well-known, real cases with Wikipedia overview pages as starting sources, all labelled "Demo record"):

```powershell
python seed_data.py            # add demo records
python seed_data.py --remove   # remove them again (also possible from Admin > Export)
python seed_data.py --reset    # delete the local database entirely, then add demo records
```

## How the database works

- Local development uses SQLite at `data/examples.db`. The file is git-ignored.
- One table, `examples`, holds every case with its status (`pending`, `approved`, `rejected`, `archived`), timestamps in ISO format, private `reviewer_notes`, and an `is_demo` flag.
- Every SQL statement is in `database.py` and uses parameterised queries. Pages call functions such as `create_example`, `find_examples`, `approve_example`, `export_examples`; they never write SQL.
- `initialize_database()` creates the table and applies small migrations (for example adding the `level` column to an older database), so it is safe to run on every start.
- Optional text is stored as `NULL`; values like `-`, `N/A` or `none` are cleaned before saving.

### Reset the local database

Stop the app, delete `data/examples.db`, start the app again (or run `python seed_data.py --reset`).

## Add categories or ethical issues

Edit the lists in `config.py` (`CATEGORIES`, `ETHICAL_ISSUES`, `CONCEPTS`, `CONTENT_STRANDS`, `CONTEXTS`). Existing records keep their values; the form, filters and analytics pick up the new entries automatically.

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

The suite covers validation rules, placeholder cleaning, the pending/approved visibility rule, search and combined filters, the status workflow, editing, deletion, exports and demo-data removal.

## Run with Docker

The image is built from the `Dockerfile` in the project root and has been tested locally.

```powershell
docker build -t digital-society-casebook .
docker run -d --name casebook -p 8501:8501 -e ADMIN_PASSWORD=change-me -v casebook-data:/app/data digital-society-casebook
```

Open http://localhost:8501. `ADMIN_PASSWORD` is passed as an environment variable because `secrets.toml` is never copied into the image. The named volume keeps `data/examples.db` across restarts; add `-e DATABASE_URL=...` instead to use Supabase/PostgreSQL. Any host that runs containers (Fly.io, Railway, Render, a school server) can run this image.

## Deploy for free

**Recommended: Streamlit Community Cloud + Supabase.**

1. Push this folder to a GitHub repository (see below).
2. Go to https://share.streamlit.io, sign in with GitHub, choose the repository, branch and `app.py`.
3. Under **Advanced settings > Secrets** paste:
   ```toml
   ADMIN_PASSWORD = "a-long-random-password"
   DATABASE_URL = "postgresql://..."   # from Supabase, see below
   ```
4. Deploy. The app gets a public `*.streamlit.app` URL.

Important: the Community Cloud file system is temporary. A SQLite file there is wiped whenever the app restarts or redeploys, so for a real deployment use Supabase's free PostgreSQL database for storage.

Alternatives: Hugging Face Spaces (Streamlit template, free, same temporary-storage caveat) or Render's free web service (sleeps when idle).

## Migrate to Supabase / PostgreSQL

The data layer already understands PostgreSQL. To switch:

1. Create a free project at https://supabase.com. In **Project Settings > Database**, copy the connection string (use the *session pooler* URI, which looks like `postgresql://postgres.xxxx:PASSWORD@aws-0-region.pooler.supabase.com:5432/postgres`).
2. Add `psycopg[binary]>=3.2` to `requirements.txt` (the line is already there, commented out).
3. Set `DATABASE_URL` in `.streamlit/secrets.toml` locally or in the Community Cloud secrets.
4. Start the app. `initialize_database()` creates the table in PostgreSQL on first run.
5. To move existing records, export a full CSV from **Admin > Export** with the SQLite database, then insert the rows into PostgreSQL (for example with the Supabase table editor's CSV import, matching the column names).

`database.py` handles the two backends in one place: `?` placeholders are translated to `%s`, `AUTOINCREMENT` becomes `SERIAL`, and inserts use `RETURNING id`. The PostgreSQL path has been written to the shared SQL dialect but has not yet been exercised against a live Supabase project; test it once with the demo data before relying on it.

## Publish to GitHub

```powershell
git init
git add .
git commit -m "Digital Society Casebook"
git branch -M main
git remote add origin https://github.com/<your-username>/digital-society-casebook.git
git push -u origin main
```

The `.gitignore` keeps `secrets.toml`, `.env`, the database file and virtual environments out of the repository.

## Security notes

- No password, key or connection string is in the source. Everything comes from Streamlit secrets or environment variables.
- All SQL is parameterised. User text is HTML-escaped before it is rendered.
- Visitors can only read approved records; pending, rejected and archived records and reviewer notes are never exposed, including in public exports.
- Deleting a record asks for confirmation; deleting demo records requires a checkbox first.
- Source URLs are validated for format only. Check them yourself before citing.
- Signing in as admin keeps you signed in across a page refresh by putting a token in the URL (`?session=...`). It is not the password itself, but anyone who gets that exact link can act as admin until you sign out or change the password. Do not share a URL that contains `?session=`.

## Not yet implemented

- Accounts for contributors (submissions are identified by a typed name and an edit code, not a login).
- Normalised tables for tags, sources and review history (the schema is one table by design; the columns are ready to be split later).
- Testing of the PostgreSQL path against a live Supabase project.
- Image or document attachments for cases.
