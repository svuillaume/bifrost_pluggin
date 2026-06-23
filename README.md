# Web AI Agent — Chrome Extension

A Chrome side-panel extension that brings AI chat and FortiCNAPP cloud security tools directly into your browser, backed by a zero-dependency Python server.

---

## Features

**Available on any page:**
- **AI chat** — streaming chat via any AI Gateway (Bifrost, Portkey, LiteLLM, Helicone)
- **Web search** — Anthropic's native `web_search_20260209` tool runs server-side automatically
- **Read / TL;DR** — load any open tab into context or get a 3-bullet summary

**FortiCNAPP security tools** (via the 🔰 FortiCNAPP dropdown):

| Button | Requires | What it does |
|---|---|---|
| 🛡 Scan | lacework CLI | SCA + SAST on code from any page or GitHub repo |
| 📋 Compliance | `~/.lacework.toml` | PDF reports for 54 frameworks (CIS, NIST, PCI-DSS, SOC 2…) |
| 🔍 LQL | `~/.lacework.toml` | Run saved LQL queries against your live tenant |
| ✨ LQL Generate | `~/.lacework.toml` | Plain-English → LQL, built and run instantly |
| 🚨 CVE | `~/.lacework.toml` | Attack surface lookup: hosts + containers ranked by internet exposure |

Buttons grey out automatically when their dependency is missing — the tooltip explains what's needed.

---

## Requirements

- Google Chrome
- Python 3.8+
- AI Gateway URL + key (Bifrost, Portkey, LiteLLM, or Helicone)
- `~/.lacework.toml` — for LQL, CVE, Compliance _(run `lacework configure`)_
- `lacework` CLI — for CodeSec/SBOM only _(setup.sh can install it)_

No Docker required.

---

## Quick start

**macOS / Linux:**
```bash
./setup.sh
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

Both scripts:
1. Create `.env` from template — prompt for gateway URL and key
2. Check for the lacework CLI; offer to install it if missing
3. Check for `~/.lacework.toml`; offer to run `lacework configure` if missing
4. Start `python3 serve.py` in the background on `localhost:8765`

---

## Manual start

`serve.py` runs **locally on the same machine as Chrome** — it listens on `localhost:8765` and the extension connects to it via `fetch`. Nothing is exposed outside the machine.

```bash
cp .env.tpl .env        # fill in ANTHROPIC_BASE_URL and BIFROST_VIRTUAL_KEY
python3 serve.py        # http://localhost:8765
```

---

## FortiCNAPP credentials

**Option 1 — `lacework configure` (interactive, writes `~/.lacework.toml`):**
```bash
curl -sL https://raw.githubusercontent.com/lacework/go-sdk/main/cli/install.sh | bash
lacework configure      # prompts for account, API key, API secret
```
`setup.sh` / `setup.ps1` offer to run both steps automatically.

**Option 2 — env vars (no toml, good for PoV/CI):**

Add to `.env` (copy from `.env.tpl`):
```
LW_ACCOUNT=your-account
LW_API_KEY=your-api-key
LW_API_SECRET=your-api-secret
```
Or export before running:
```bash
export LW_ACCOUNT=your-account LW_API_KEY=your-api-key LW_API_SECRET=your-api-secret
python3 serve.py
```
LQL, CVE, and Compliance work immediately — no CLI or toml file required.

> **CodeSec / SBOM** still require the `lacework` CLI binary for local SCA scanning.  
> **Windows:** `setup.ps1` downloads `lacework.exe` automatically.

---

## Load the Chrome extension

1. `chrome://extensions` → enable **Developer mode**
2. **Load unpacked** → select the `extension/` folder
3. Click the toolbar icon to open the side panel

The extension reads its config from `GET /config` on `localhost:8765` at startup.

---

## Configuration

Copy `.env.tpl` → `.env` and fill in:

| Key | Description |
|---|---|
| `ANTHROPIC_BASE_URL` | AI gateway endpoint (e.g. `https://your-gateway.example.com/anthropic`) |
| `BIFROST_VIRTUAL_KEY` | Gateway virtual key (`sk-bf-…`) |
| `ANTHROPIC_DEFAULT_MODEL` | Model for chat and LQL Generate (default: `claude-haiku-4-5`) |
| `LQL_QUERIES_DIR` | Path to `.yaml` LQL query files |

---

## Security model

| Data | Storage | Lifetime |
|---|---|---|
| Gateway URL + API key | `chrome.storage.session` (RAM) | Cleared on Chrome close |
| Model / gateway choice | `chrome.storage.local` | Persists across sessions |
| Chat history | JS memory | Cleared on panel close |
| Page content | JS memory | Never persisted |

---

## Backend endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/config` | Gateway URL, key, `lw_ready`, `lw_cli` flags |
| POST | `/proxy/v1/*` | Proxy to AI gateway (streaming) |
| POST | `/codesec` | SCA + SAST scan — requires lacework CLI |
| POST | `/sbom` | CycloneDX SBOM — requires lacework CLI |
| POST | `/compliance` | Generate compliance PDF |
| GET | `/compliance/list` | List available frameworks |
| GET | `/lql/queries` | List saved `.yaml` LQL query files |
| POST | `/lql/run` | Execute LQL query |
| POST | `/lql/cve` | CVE attack surface: hosts + containers |
| POST | `/lql/generate` | Plain-English → LQL via Claude |
