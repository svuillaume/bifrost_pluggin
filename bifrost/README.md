# Bifrost Chat — Chrome Extension

A secure AI chat side panel for your [Bifrost AI Gateway](https://github.com/svuillaume/bifrost_pluggin).

---

## What is this?

A Chrome browser extension that opens as a side panel and lets you chat with Claude AI models through a **Bifrost AI Gateway** — a private API proxy that manages model access and virtual keys for your organisation.

**Key capabilities:**
- 💬 Chat with Claude (haiku / sonnet / opus) via your private gateway
- 📄 **Read Web Page** — load any open tab into AI context and ask questions about it
- 📋 **TL;DR** — one-click bullet-point summary of the current page
- 🔍 **Web search** — live results via local SearXNG container (optional)
- 🔗 Clickable links in AI responses open in a new tab

---

## Who is this for?

Anyone with access to a Bifrost AI Gateway virtual key who wants a fast, private AI assistant embedded directly in Chrome — without sending data to third-party browser AI tools.

---

## Why is it secure?

| Concern | How it's handled |
|---------|-----------------|
| API key on disk | Never written to disk — stored in `chrome.storage.session` (RAM only, cleared on Chrome close) |
| API key in source | Loaded at runtime from `config.json` (gitignored) — never hardcoded |
| XSS from AI output | Markdown rendered via inert `<template>` element — injected scripts never execute |
| Outbound connections | CSP restricts to `https:` and `localhost:8080` only |
| Page content privacy | Page text stays local — sent only to your own Bifrost gateway |
| Secrets in git | `.env`, `config.json`, `searxng/` all gitignored |

---

## Requirements

- Google Chrome (or Chromium)
- Access to a Bifrost AI Gateway — URL + virtual key (`sk-bf-…`)
- (Optional) Docker Desktop for web search

---

## Step-by-step setup

### Step 1 — Clone the repo

```bash
git clone https://github.com/svuillaume/bifrost_pluggin.git
cd bifrost_pluggin/bifrost
```

### Step 2 — Create your credentials file

Copy the template and fill in your values:

```bash
cp extension/config.json.tpl extension/config.json
```

Edit `extension/config.json`:

```json
{
  "bifrost_url": "https://your-bifrost-endpoint/anthropic",
  "api_key":     "sk-bf-your-virtual-key-here",
  "searxng_url": "http://localhost:8080"
}
```

> `config.json` is **gitignored** — it will never be committed. Do not commit it manually.

The same values map to `.env` variables (used by `serve.py` if you run the local proxy):

```
ANTHROPIC_BASE_URL=https://your-bifrost-endpoint/anthropic
BIFROST_VIRTUAL_KEY=sk-bf-your-virtual-key-here
ANTHROPIC_DEFAULT_MODEL=claude-haiku-4-5-20251001
SEARXNG_URL=http://localhost:8080
```

> Copy `.env.tpl` → `.env` and fill in your values. `.env` is also gitignored.

`serve.py` reads `ANTHROPIC_BASE_URL` at startup to set its upstream proxy target — no hardcoded URLs anywhere in the codebase.

### Step 3 — Load the extension in Chrome

1. Open `chrome://extensions` in Chrome
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder inside this repo
5. The ⚡ **Bifrost Chat** icon appears in your toolbar

### Step 4 — Open the side panel

Click the ⚡ icon — the side panel opens on the right.

On first load the URL and API key are auto-filled from `config.json`. The status bar shows **config loaded**.

### Step 5 — Start chatting

- Type a message → press **Enter** (Shift+Enter for a newline)
- Choose model: **haiku-4-5 ⚡** (fast, default) · sonnet-4-6 · opus-4-8
- **clear** resets the conversation

---

## Web search setup (optional)

The easiest way to set up web search is with the included setup script.

### Using the setup script (recommended)

**Mac / Linux:**

```bash
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell — run as Administrator):**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

Both scripts walk you through the same steps:

1. Creates `.env` from template if missing and opens it for editing
2. Creates `extension/config.json` from template if missing
3. Asks: **Docker** or **Python venv**?

```
  How do you want to run web search?

  [1] Docker  — SearXNG container on localhost:8080
               Requires Docker Desktop. Fast, self-contained.

  [2] Python  — serve.py venv proxy on localhost:8765
               No Docker needed. Uses your Python venv.

  Enter 1 or 2:
```

- **Option 1 (Docker):** generates `searxng/settings.yml` with a random secret, starts the container, and waits for it to be ready.
- **Option 2 (Python):** creates a `.venv`, and starts `serve.py` which proxies search requests to SearXNG (or any `SEARXNG_URL` set in `.env`).

After either option, the extension automatically tries Docker at `localhost:8080` first, then falls back to the Python proxy at `localhost:8765` — no config change needed.

### Manual setup (Docker only)

If you prefer not to use the script:

```bash
# Generate config with a random secret key
mkdir -p searxng
sed "s/REPLACE_WITH_RANDOM_SECRET/$(openssl rand -hex 32)/" \
    searxng.settings.yml.tpl > searxng/settings.yml

# Start the container
docker compose up -d

# Test it
curl "http://localhost:8080/search?q=test&format=json" | python3 -m json.tool | head -20
```

Stop: `docker compose down`

> `searxng/settings.yml` is **gitignored** — the generated secret never leaves your machine.

---

## Toolbar buttons

| Button | What it does |
|--------|-------------|
| **📄 Read Web Page** | Extracts text from the current tab (up to 12,000 chars) and loads it as context. Button turns green when active. Ask follow-up questions about the page. |
| **TL;DR** | Reads the current page and immediately streams a 3-5 bullet summary |
| **clear** | Wipes conversation history and resets context |

---

## Security model (full detail)

| What | Where stored | Lifetime |
|------|-------------|----------|
| Bifrost URL | `chrome.storage.session` (RAM) | Cleared when Chrome closes |
| API key | `chrome.storage.session` (RAM) | Cleared when Chrome closes |
| SearXNG URL | `chrome.storage.session` (RAM) | Cleared when Chrome closes |
| Model choice | `chrome.storage.local` (disk) | Persists (not sensitive) |
| Conversation history | JS memory only | Cleared when panel closes |
| Page content | JS memory only | Never persisted |

**The API key is never written to disk after initial load.** `config.json` is read once on panel open; the value moves immediately to session RAM.

**Content Security Policy** blocks all inline scripts, all external scripts, and restricts network calls to `https:` + `localhost:8080`.

**Page reading** uses `chrome.scripting` to extract visible text — no form data, no cookies, no credentials. Chrome prompts for permission per site.

### `chrome.storage.session` vs `chrome.storage.local` — why it matters

Chrome extensions can store data in two places:

| | `chrome.storage.local` | `chrome.storage.session` |
|---|---|---|
| **Stored on** | Disk (persists on disk like a database) | RAM only |
| **Survives Chrome close** | Yes | No — wiped on close |
| **Risk if device stolen** | Key readable from disk | Nothing to read |
| **Used for** | Non-sensitive prefs (model choice) | API key, endpoint URL |

Many older or simpler extensions use `chrome.storage.local` for convenience — including the now-removed `popup.js` in this repo. This means the API key would be written to Chrome's profile directory on disk and readable by any process with access to that folder.

This extension deliberately uses `chrome.storage.session` for all sensitive values. **How it works:**

1. On panel open, `config.json` is fetched once via `chrome.runtime.getURL`
2. The key and URL are immediately written to `chrome.storage.session` (RAM)
3. `config.json` is only read — never written back, never cached by the browser
4. When Chrome closes, session storage is wiped automatically — nothing persists

**To verify this yourself:**

```
chrome://extensions → Bifrost Chat → Service Worker → inspect → Application → Storage
```

You will see `bf_key` and `bf_url` under Session Storage (not Local Storage).

---

## Code Security Scan

Scanned with **Lacework FortiCNAPP Code Security** (IaC + SCA/SAST).

| Severity | IaC | SCA | Total |
|----------|-----|-----|-------|
| Critical |  0  |  0  |   0   |
| High     |  0  |  0  |   0   |
| Medium   |  0  |  0  |   0   |
| Low      |  0  |  0  |   0   |

39 findings in `.venv/` (third-party packages) excluded via `.lacework/codesec.yaml`.

---

## File reference

```
extension/
  manifest.json           Permissions, CSP, extension metadata (v1.8)
  background.js           Service worker — opens side panel on icon click
  panel.html              Side panel UI + styles
  panel.js                All chat logic: storage, streaming, search, page reader
  config.json             Your credentials — gitignored, never committed
  config.json.tpl         Safe template — copy to config.json and fill in values
  icon16/48/128.png       Extension icons

setup.sh                  Mac/Linux setup script — interactive Docker or Python venv choice
setup.ps1                 Windows PowerShell setup script — same flow as setup.sh

docker-compose.yml        Starts local SearXNG search container
searxng.settings.yml.tpl  SearXNG config template — generated by setup script or manually
searxng/                  Generated at runtime, gitignored (contains secret key)

serve.py                  Python search proxy + CORS proxy for chatbox.html (configure via .env)
.env                      Server credentials — gitignored
.env.tpl                  Template: copy to .env and fill in values
.lacework/codesec.yaml    Code security scan config
```
