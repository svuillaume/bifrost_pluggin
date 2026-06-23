# Web AI Agent — Chrome Extension

> **License**: Apache 2.0 — see [LICENSE](LICENSE) | **Status**: BETA

A Chrome side panel that brings AI-powered cloud security to your browser. Ask questions about any webpage, scan code for vulnerabilities, run cloud security queries, and analyze threats — all without leaving your browser tab.

Works with **FortiCNAPP** (and any CNAPP platform built on Lacework).

---

## Features

| Feature | Description |
|---|---|
| 💬 **AI Chat** | General-purpose AI assistant with automatic web search for up-to-date information |
| 📖 **Read Page** | Loads the current webpage into context so you can ask questions about it |
| ⚡ **TL;DR** | Instant plain-English summary of any page |
| 🚨 **FortiGuard Alerts** | Live outbreak alert feed from FortiGuard Labs — button flashes red when active threats are detected in the last 5 days |
| 🛡 **Code Scanner** | Scans code on the current page or a GitHub repo for vulnerabilities, misconfigurations, and exposed secrets |
| 📋 **Compliance Reports** | Generates compliance PDF reports (CIS, NIST, PCI-DSS, SOC 2, HIPAA, and 50+ frameworks) from your FortiCNAPP environment |
| 📊 **Advanced Analytics (LQL)** | Run saved security queries against FortiCNAPP — or type what you want in plain English and the AI writes and executes the query automatically |
| 🔬 **Attack Surface Analyzer** | Search any CVE ID and instantly see which hosts and containers in your environment are exposed, enriched with FortiGuard outbreak intelligence and a direct FortiGuard search link |
| 🤖 **CISO-Level Reports** | Every AI response follows a consistent executive report template — findings, risk ratings, impacted resources table, MITRE ATT&CK mapping, and Quick Remediation CLI scripts |
| 📋 **Copy Button** | One-click copy on every AI response |

---

## What does it do?

Think of it as a security analyst sitting next to you while you browse. You open a side panel in Chrome, and from there you can:

**General AI assistant (works on any webpage)**

- **Chat** — ask the AI anything; it searches the web automatically when it needs fresh information
- **Read this page** — loads the page you're on so you can ask questions about it ("summarise this document", "what are the risks mentioned here?")
- **TL;DR** — get a plain-English summary of any page in seconds
- **FortiGuard** — opens the live FortiGuard threat intelligence feed; the button flashes red when there are active cybersecurity outbreak alerts

**Cloud security tools (requires FortiCNAPP)**

| Button | What it does |
|---|---|
| 🛡 **Scan Code** | Scans code on the current page or a GitHub repo for security vulnerabilities and exposed secrets |
| 📋 **Compliance** | Generates a compliance PDF report for frameworks like CIS, NIST, PCI-DSS, SOC 2, and HIPAA |
| 📊 **Advanced Analytics** | Run security queries against your cloud environment — use saved queries or describe what you want in plain English and the AI writes the query for you |
| 🔬 **Attack Surface** | Look up any CVE and instantly see which servers and containers in your environment are vulnerable — enriched with live FortiGuard outbreak intelligence |
| 💬 **Community** | Opens the FortiCNAPP community feed for blogs and updates |

> If a button is greyed out, hover over it — a tooltip explains exactly what's needed to enable it.

---

## How Attack Surface works

When you search for a CVE (a security vulnerability ID like `CVE-2024-21762`), the tool does two things **at the same time**:

1. **Checks your FortiCNAPP environment** — which of your servers and containers are running software affected by that CVE, how exposed they are to the internet, and whether a fix is available
2. **Checks FortiGuard Labs** — whether FortiGuard has published an active outbreak alert for that CVE, including attack techniques, severity, and remediation guidance

Both sources are combined and sent to the AI, which writes a full CISO-level security report with prioritised remediation steps and automation scripts.

---

## What you need before starting

| Requirement | Notes |
|---|---|
| **Google Chrome** | Any recent version |
| **Python 3** | Already installed on most Macs. Windows users: download from [python.org](https://python.org) — tick "Add to PATH" during install |
| **AI Gateway URL + key** | Provided by your IT team or Fortinet contact. The key usually starts with `sk-bf-…` |
| **FortiCNAPP account** | Only needed for the security tools (Scan Code, Compliance, Analytics, Attack Surface) |
| **FortiCNAPP API key** | Found in FortiCNAPP under **Settings → API Keys** |

You do **not** need to be a developer. You do **not** need Docker.

---

## Setup — 4 steps

### Step 1 — Download

**Option A — Git (if you have it):**
```bash
git clone https://github.com/svuillaume/webaiagent.git
cd webaiagent
```

**Option B — ZIP download:**
1. Go to [github.com/svuillaume/webaiagent](https://github.com/svuillaume/webaiagent)
2. Click the green **Code** button → **Download ZIP**
3. Unzip the file, then open Terminal (Mac) or PowerShell (Windows) inside that folder

---

### Step 2 — Run the setup script

This script installs everything and asks you a few questions.

**Mac / Linux — open Terminal and run:**
```
./setup.sh
```

**Windows — open PowerShell and run:**
```
.\setup.ps1
```

The script will walk you through these questions:

| Question | What to enter |
|---|---|
| AI Gateway URL | The URL your IT team gave you (e.g. `https://bifrost.yourcompany.com/anthropic`) |
| Gateway API key | Your key — starts with `sk-bf-…` |
| FortiCNAPP credentials | Answer **y** — you'll need your FortiCNAPP account name, API Key ID, and API Secret |

When the script finishes and shows a green `[OK]`, the server is running and you're ready for Step 3.

---

### Step 3 — Load the extension into Chrome

1. Open Chrome and type **`chrome://extensions`** in the address bar
2. Turn on **Developer mode** — the toggle is in the top-right corner of the page
3. Click **Load unpacked**
4. Select the **`extension`** folder inside the project folder you downloaded
5. The Web AI Agent icon appears in your Chrome toolbar (top-right)
6. **Pin it** for easy access: click the puzzle piece 🧩 icon in the toolbar → click the pin next to Web AI Agent

---

### Step 4 — Open and use it

Click the Web AI Agent icon in the Chrome toolbar. The side panel opens on the right side of your browser.

- The **status dot** in the top-right of the panel should be **green** — this means the AI is connected and ready
- Type anything in the chat box to start
- Click the **🔰 FortiCNAPP** button to access security tools

> If the status dot is grey or red, the server isn't running — go back to Step 2 and run the setup script again.

---

## Stopping and restarting

The server runs quietly in the background after setup.

**To stop the server:**
- Mac/Linux: open Terminal in the project folder and run `kill $(cat .serve.pid)`
- Windows: open PowerShell in the project folder and run `Stop-Process -Id (Get-Content .serve.pid)`

**To start it again:** run `./setup.sh` or `.\setup.ps1` — it skips the configuration questions if your `.env` is already set up.

---

## Troubleshooting

**Status dot is grey — "not connected"**
→ The server isn't running. Open Terminal/PowerShell in the project folder and run `./setup.sh` (or `.\setup.ps1`) again.
→ You can verify the server is running by opening `http://localhost:45321` in Chrome — you should see a chat page.

**Security tool buttons are greyed out (Compliance, CVE, LQL)**
→ FortiCNAPP credentials aren't configured. Run the setup script and answer **y** when asked about FortiCNAPP credentials.

**Scan Code button is greyed out**
→ The lacework CLI isn't installed. Run the setup script and answer **y** when asked to install it.

**"Cannot scan this page" when clicking Scan Code**
→ Navigate to a GitHub repository page first, then click Scan Code. It works best on GitHub repo pages.

**Attack Surface shows no results for a CVE**
→ That CVE may not affect any hosts in your monitored environment, or the time window is too short. Try extending the time window (default is 7 days).

**FortiGuard button is flashing red**
→ FortiGuard Labs has published an active outbreak alert in the last 5 days. Click the button to read it — the flashing stops once you've seen it.

**Windows: script won't run — "execution policy" error**
→ Open PowerShell as Administrator and run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
Then re-run `.\setup.ps1`.

---

## Privacy and your data

Everything stays on your machine.

| Data | Where it's stored | Notes |
|---|---|---|
| Gateway URL + API key | Your machine only (`.env` file) | Never sent anywhere except your own AI gateway |
| Chat history | Browser memory only | Cleared when you close the side panel |
| Page content you read | Browser memory only | Never written to disk |
| FortiCNAPP credentials | Your machine only (`~/.lacework.toml`) | Standard lacework CLI credential file |
| FortiGuard threat data | Fetched live, never stored | RSS feed proxied through your local server |

The local server (`serve.py`) only listens on `localhost` — it is not reachable from the internet or from other devices on your network.

---

## Technical reference

<details>
<summary>For developers — manual config, API endpoints, architecture</summary>

### Manual start (without setup script)

```bash
cp .env.tpl .env        # copy the template
# edit .env with your ANTHROPIC_BASE_URL and BIFROST_VIRTUAL_KEY
python3 serve.py        # starts on http://localhost:45321
```

### Environment variables (`.env`)

| Variable | Description |
|---|---|
| `ANTHROPIC_BASE_URL` | AI gateway endpoint URL |
| `BIFROST_VIRTUAL_KEY` | Gateway virtual key (`sk-bf-…`) |
| `ANTHROPIC_DEFAULT_MODEL` | Model used for chat and LQL Generate (default: `claude-haiku-4-5`) |
| `LQL_QUERIES_DIR` | Path to folder containing `.yaml` LQL query files |

FortiCNAPP credentials come from `~/.lacework.toml` (created by `lacework configure`).

### Backend API endpoints (`localhost:45321`)

| Method | Path | Description |
|---|---|---|
| GET | `/config` | Gateway URL, key, and feature-availability flags |
| POST | `/proxy/v1/*` | Proxies streaming requests to the AI gateway |
| POST | `/codesec` | SCA + SAST scan via lacework CLI |
| POST | `/sbom` | CycloneDX SBOM via lacework CLI |
| POST | `/compliance` | Generate compliance PDF report |
| GET | `/compliance/list` | List available compliance frameworks |
| GET | `/lql/queries` | List saved `.yaml` LQL query files |
| POST | `/lql/run` | Execute an LQL query against FortiCNAPP |
| POST | `/lql/cve` | CVE attack surface: affected hosts and containers |
| POST | `/lql/generate` | Convert plain-English objective to LQL via Claude |
| GET | `/fortiguard/outbreaks` | FortiGuard outbreak RSS feed (cached 30 min) |
| GET | `/fortiguard/outbreak-by-cve?cveId=` | Outbreak alerts matching a specific CVE |

### How LQL Generator works — lightweight RAG

The **✨ Generator** tab converts plain-English security objectives into validated LQL queries:

```
User types objective
  → cache lookup (normalized key)
    → HIT:  return cached queryId + queryText instantly
    → MISS: serve.py injects LQL reference into Claude's system prompt
              → Claude returns { queryId, queryText }
                → serve.py runs the query live: lacework query run
                  → if it fails: error sent back to Claude — fix and retry (up to 3x)
                    → validated query + pre-fetched rows returned to extension
                      → queryId + queryText stored in cache
```

**Why this works without a vector database**: Claude has no built-in knowledge of LQL. `serve.py` injects the entire LQL reference (~100 lines: datasource names, field syntax, valid operators, region filter rules, timestamp patterns) into every request. This is Retrieval-Augmented Generation (RAG) without the retrieval step — the knowledge base is small enough to inject in full every time.

| Approach | When to use |
|---|---|
| **Full injection (what we do)** | Knowledge base is small and always relevant |
| **Vector DB + RAG** | Knowledge base is large — retrieve only relevant chunks per query |
| **Fine-tuning** | Domain knowledge is stable, extremely high volume — bake into model weights |

### How Attack Surface + FortiGuard enrichment works

When a CVE is searched, two requests fire in parallel:
1. `/lql/cve` — queries FortiCNAPP for affected hosts and containers
2. `/fortiguard/outbreak-by-cve` — checks the FortiGuard RSS feed for matching outbreak alerts

Both datasets are combined into Claude's prompt. Claude produces a CISO-level report with host exposure, MITRE TTPs from FortiGuard, and remediation scripts.

The FortiGuard RSS feed is cached in memory for 30 minutes. CVE IDs are extracted from alert titles and descriptions via regex.

### Docker (for teams)

```bash
docker compose up -d          # first run
docker compose up --build -d  # after code changes
docker compose down
```

Requires `~/claude_cnapp/lql/lql_queries` for LQL files and `~/.lacework.toml` for credentials.

</details>
