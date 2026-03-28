# NIIT StackRoute Design Automation — Complete Setup Guide

> Local LLM · No external API calls · Zero per-request cost
> Powered by Ollama + FastAPI + React

---

## What you need before starting

| Tool | Minimum Version | Why |
|---|---|---|
| Python | 3.11 | Backend runtime |
| Node.js | 18 | React frontend |
| Ollama | Latest | Local LLM inference |
| Docker + Docker Compose | Latest | Optional — for team deployment |
| Git | Any | Clone the repo |

---

## OPTION A — Run Locally on One Machine (Development / Single User)

This is the fastest way to get up and running. Everything runs on your laptop.

---

### Step 1 — Install Ollama

Ollama is the local LLM runtime. Download and install it from:

```
https://ollama.com/download
```

After installing, verify it works:

```bash
ollama --version
```

---

### Step 2 — Pull the two models Ollama needs

Open a terminal and run both commands. These only need to be downloaded once.

```bash
# Generation model — used to write the program design content
ollama pull qwen2.5:7b-instruct

# Embedding model — used to find similar past designs
ollama pull nomic-embed-text
```

> **How long does this take?**
> `qwen2.5:7b-instruct` is about 4.7 GB. On a standard broadband connection, expect 5–15 minutes.
> `nomic-embed-text` is about 274 MB and downloads in under a minute.

> **Hardware note:**
> The system works without a GPU (CPU inference via Ollama) but generation will be slower (~1–3 minutes per design).
> With an Apple Silicon Mac or NVIDIA GPU, generation takes 15–45 seconds.

After both are downloaded, start the Ollama server (it may already be running as a background service):

```bash
ollama serve
```

Leave this terminal open, or Ollama will run silently in the background on Mac/Windows.

---

### Step 3 — Clone / navigate to the repo

```bash
cd /path/to/NIITSyllabriq
```

---

### Step 4 — Create a Python virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Your terminal prompt should now show `(.venv)`.

---

### Step 5 — Install Python dependencies

```bash
pip install -e ".[dev]"
```

This installs FastAPI, SQLModel, Alembic, python-docx, pypdf, and all other backend dependencies.

---

### Step 6 — Create the environment config file

```bash
cp .env.example .env
```

Open `.env` in any text editor. For a local single-machine setup you only need to change these two things:

```env
# Leave the rest as-is for local development

# Optional: change to a strong random string for production
JWT_SECRET_KEY=change-me-in-production

# The reviewer email addresses must match actual user accounts
# (pre-seeded accounts use these exact emails — change only if you create new users)
PRIMARY_REVIEWERS=primary.reviewer@niit.com
FINAL_REVIEWERS=final.reviewer1@niit.com,final.reviewer2@niit.com
```

All other defaults work out of the box for local development:

```
DATABASE_URL=sqlite:///./niit_design_automation.db   ← SQLite, no Postgres needed
OLLAMA_BASE_URL=http://localhost:11434               ← where Ollama is listening
OLLAMA_GENERATION_MODEL=qwen2.5:7b-instruct
OLLAMA_EMBED_MODEL=nomic-embed-text
```

---

### Step 7 — Run the database migrations

This creates all the tables in the SQLite database:

```bash
alembic upgrade head
```

You should see output like:

```
Running upgrade  -> 20260327_0001_initial, initial schema
Running upgrade 20260327_0001_initial -> 20260327_0002_training_reporting, training and reporting
```

---

### Step 8 — Start the backend API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag restarts the server automatically when you edit code.

Verify it is running — open this URL in your browser:

```
http://localhost:8000/health
```

You should see something like:

```json
{
  "status": "ok",
  "environment": "development",
  "ollama_reachable": true
}
```

> If `ollama_reachable` is `false`, make sure you ran `ollama serve` in Step 2.

The interactive API documentation is also available at:

```
http://localhost:8000/docs
```

---

### Step 9 — Start the React frontend

Open a **second terminal** (keep the backend running in the first one):

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at:

```
http://localhost:5173
```

---

### Step 10 — Log in and verify everything works

Open `http://localhost:5173` in your browser.

Use any of these pre-seeded accounts:

| Email | Password | Role |
|---|---|---|
| admin@niit.com | Admin@123 | Full access — all tabs |
| designer@niit.com | Designer@123 | Upload requirements, generate designs |
| primary.reviewer@niit.com | Reviewer@123 | Review tab (primary) |
| final.reviewer1@niit.com | Reviewer@123 | Review tab (final) |
| final.reviewer2@niit.com | Reviewer@123 | Review tab (final) |

Log in as `admin@niit.com` first. You should see five tabs: Requirements, Designs, Training Library, Reviews, Reports.

---

## OPTION B — Team Deployment (Docker, shared office server)

Use this when you want one central server that the whole team accesses from their browsers.

---

### Step 1 — Install Ollama on the server (not in Docker)

Ollama must run directly on the host machine (not inside a container) so it can access the GPU if one is available.

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then pull the models:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

Start Ollama bound to all interfaces so Docker can reach it:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

To run it permanently as a service on Linux:

```bash
# Create a systemd service
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama LLM server
After=network.target

[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
ExecStart=/usr/local/bin/ollama serve
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ollama
```

---

### Step 2 — Configure the environment file

```bash
cp .env.example .env
```

Edit `.env` — for team Docker deployment change these:

```env
# Use Postgres instead of SQLite
DATABASE_URL=postgresql+psycopg://niit:niit@postgres:5432/niit_design_automation

# Ollama on the Docker host
OLLAMA_BASE_URL=http://host.docker.internal:11434

# MUST change this for production — use a long random string
JWT_SECRET_KEY=your-long-random-secret-here-at-least-32-chars

# Update with your real team reviewer emails
PRIMARY_REVIEWERS=firstname.lastname@yourcompany.com
FINAL_REVIEWERS=reviewer1@yourcompany.com,reviewer2@yourcompany.com

# Frontend URL (update with your server IP or domain)
ALLOWED_ORIGINS=http://YOUR_SERVER_IP:5173,http://localhost:5173
```

---

### Step 3 — Build and start with Docker Compose

```bash
docker compose up --build -d
```

This starts two containers:
- `postgres` — PostgreSQL database (data persists in a named volume)
- `design-automation` — FastAPI backend on port 8000

Check that both are running:

```bash
docker compose ps
docker compose logs design-automation
```

The migrations run automatically on startup. You should see `Running upgrade` lines in the logs.

---

### Step 4 — Start the frontend (on the same server or each team member's machine)

**Option 4A — Run on the server (team accesses via IP):**

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://YOUR_SERVER_IP:8000 npm run build
npx serve -s dist -l 5173
```

**Option 4B — Each team member runs on their own laptop:**

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://YOUR_SERVER_IP:8000 npm run dev
```

---

### Step 5 — Verify

From any team member's browser:

```
http://YOUR_SERVER_IP:5173
```

Log in as `admin@niit.com / Admin@123` and check that the health endpoint shows `ollama_reachable: true`:

```
http://YOUR_SERVER_IP:8000/health
```

---

## End-to-End Workflow — What the Team Does Every Day

Once running, here is the standard workflow step by step.

---

### Step 1 — (First time only) Upload prior design documents for training

Log in as admin or designer. Go to the **Training Library** tab.

Upload any existing program design documents — PDF, DOCX, TXT — that the team has already produced. The local LLM will read and index them. Future designs will reference similar past work automatically.

This is how the system "learns" from your history without any external API.

---

### Step 2 — Enter a new customer requirement

Requirements at NIIT StackRoute come in via email, Teams messages, or are captured during a call. There is no file to upload — you type or paste the requirement directly.

Go to the **Requirements** tab and fill in the form:

| Field | What to enter |
|---|---|
| Customer Name | e.g. `Accenture` |
| Program Title | e.g. `Cloud Native Development with AWS` |
| Duration (hours) | e.g. `40` — leave blank if not yet confirmed |
| Source | Choose: Email / Call Notes / Teams / WhatsApp / Direct / Other |
| Requirement text | Paste the email body, or type up what was discussed on the call |

Then click one of the two buttons:

- **Save Requirement** — saves it for review before generating
- **⚡ Save & Generate Design** — saves it and immediately kicks off design generation (recommended when the requirement is clear and complete)

---

### Step 3 — Generate the design

In the Requirements table, click **Generate Design** next to the requirement.

The system will:
1. Parse and normalize the requirement
2. Search training documents and past designs for similar work
3. Send the requirement to the local Ollama LLM with the full NIIT StackRoute system prompt
4. Render the output into the NIIT StackRoute template format (all 7 mandatory sections)
5. Score the design on 7 quality dimensions
6. Assign the design to the primary reviewer

Generation time: 15–45 seconds with GPU; 1–3 minutes without.

---

### Step 4 — Primary review

Log in as `primary.reviewer@niit.com`. Go to the **Reviews** tab.

You will see the pending review task. Click **Approve** or **Reject**.

If approved, the design moves automatically to final review. If rejected, the workflow stops and the designer is notified.

---

### Step 5 — Final review (two approvers required)

Log in as `final.reviewer1@niit.com` and then `final.reviewer2@niit.com` (or have each reviewer log in on their own machine).

Both must **Approve** for the design to reach **FINAL_APPROVED** status.

---

### Step 6 — Export the final design

Log in as any user. Go to the **Designs** tab.

Find the approved design. Use the export buttons:
- **MD** — Markdown text (for editing in any editor)
- **DOCX** — Word document with NIIT StackRoute branding (orange title, navy headings, Candara font, IP footer)
- **PDF** — Basic PDF (for a fully branded PDF, open the DOCX in Word and export to PDF)

---

## Choosing a Different Ollama Model

The default model is `qwen2.5:7b-instruct`. If your server hardware is different, here are alternatives:

| Model | RAM needed | Quality | Speed |
|---|---|---|---|
| `qwen2.5:7b-instruct` ← default | 8 GB | Good | Fast |
| `qwen2.5:14b-instruct` | 16 GB | Better | Medium |
| `llama3.2:3b` | 4 GB | Basic | Very fast |
| `mistral:7b-instruct` | 8 GB | Good | Fast |
| `phi4:14b` | 16 GB | Excellent | Medium |

To switch models, update `.env`:

```env
OLLAMA_GENERATION_MODEL=mistral:7b-instruct
```

And pull the new model first:

```bash
ollama pull mistral:7b-instruct
```

The embedding model (`nomic-embed-text`) should not be changed — it is the best available for this task.

---

## Adding or Changing Reviewer Accounts

By default the system seeds 5 accounts. To add your real team members:

**Via the API** (while logged in as admin):

```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@yourcompany.com",
    "full_name": "John Doe",
    "role": "primary_reviewer",
    "password": "SecurePassword@123"
  }'
```

Valid roles: `admin`, `designer`, `primary_reviewer`, `final_reviewer`

Then update `.env` to include their email in the reviewer lists:

```env
PRIMARY_REVIEWERS=john.doe@yourcompany.com
FINAL_REVIEWERS=jane.smith@yourcompany.com,bob.jones@yourcompany.com
```

Restart the server after changing `.env`.

---

## Troubleshooting

**"ollama_reachable: false" at `/health`**
- Make sure `ollama serve` is running
- For Docker: check that `OLLAMA_BASE_URL=http://host.docker.internal:11434` is set (macOS/Windows Docker Desktop)
- For Linux Docker: use the host's actual IP instead of `host.docker.internal`
  ```bash
  ip route show | grep docker  # find the docker bridge IP, usually 172.17.0.1
  OLLAMA_BASE_URL=http://172.17.0.1:11434
  ```

**Design generation is very slow**
- Ollama is running on CPU. Install the CUDA or Metal drivers for your hardware and reinstall Ollama.
- Or switch to a smaller model like `llama3.2:3b`

**"alembic upgrade head" fails**
- Make sure you activated the virtual environment first: `source .venv/bin/activate`
- Delete `niit_design_automation.db` if it exists and corrupted, then re-run

**Frontend shows "Failed to fetch" or CORS error**
- Make sure `ALLOWED_ORIGINS` in `.env` includes the frontend URL
- Make sure the backend is running (`http://localhost:8000/health` responds)

**Models not found in Ollama**
```bash
ollama list       # see what's downloaded
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

---

## File locations after setup

```
NIITSyllabriq/
├── .env                          ← your config (never commit this)
├── niit_design_automation.db     ← SQLite database (local dev only)
├── app/storage/
│   ├── requirements/             ← uploaded requirement files
│   └── designs/                  ← generated .md, .docx, .pdf exports
├── app/templates/designs/
│   └── niit_template.md          ← the Jinja2 template with all 7 StackRoute sections
└── app/services/
    ├── design_service.py         ← LLM system prompt lives here
    ├── export_service.py         ← DOCX branding (colors, fonts, boilerplate)
    └── scoring_service.py        ← quality scoring logic
```
