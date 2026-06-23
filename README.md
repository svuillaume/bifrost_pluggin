# Web AI Agent — Chrome Extension

An AI-powered security assistant that lives in your Chrome browser. Ask questions, search the web, and run FortiCNAPP cloud security checks — all from a side panel without leaving the page you're on.

---

## What can it do?

**Chat & research (works on any webpage):**
- Ask the AI anything — it can also search the web automatically when needed
- **Read** — loads the page you're viewing so you can ask questions about it
- **TL;DR** — gives you a 3-bullet plain-English summary of any page

**FortiCNAPP security tools** (click the 🔰 FortiCNAPP button in the toolbar):

| Button | What it does |
|---|---|
| 🛡 Scan | Checks code on the page you're viewing for vulnerabilities and security issues |
| 📋 Compliance | Downloads a compliance PDF report (CIS, NIST, PCI-DSS, SOC 2, HIPAA, and 50+ more) |
| 🔍 LQL | Runs pre-built security queries against your FortiCNAPP account |
| ✨ LQL Generate | Describe what you want to find in plain English — it writes and runs the query for you |
| 🚨 CVE | Look up any CVE (e.g. Log4Shell) and see which of your servers and containers are exposed |

> If a button appears greyed out, hover over it — the tooltip will tell you exactly what's needed to enable it.

---

## What you need before you start

| What | Why you need it |
|---|---|
| **Google Chrome** | The extension runs inside Chrome |
| **Python 3** | Runs the small local server that powers the security tools |
| **AI Gateway URL + key** | Connects the chat to Claude (provided by your IT/Fortinet team) |
| **FortiCNAPP API key** | Lets the security tools connect to your FortiCNAPP account |

You don't need Docker. You don't need to be a developer.

---

## Setup — Step by step

### Step 1 — Download the extension

Clone or download this repository to a folder on your computer.  
If you received a `.zip` file, unzip it first.

### Step 2 — Run the setup script

Open a **Terminal** (macOS) or **PowerShell** (Windows) in the folder you just downloaded.

**On macOS or Linux — type this and press Enter:**
```
./setup.sh
```

**On Windows — type this and press Enter:**
```
.\setup.ps1
```

The script will walk you through everything interactively:

1. **Gateway URL** — paste the AI Gateway URL your IT team gave you
2. **Gateway key** — paste your API key (starts with `sk-bf-…`)
3. **FortiCNAPP credentials** — the script will ask if you want to set these up now
4. The server starts automatically in the background

If you see a ✔ at the end, you're ready.

### Step 3 — Load the Chrome extension

1. Open Chrome and go to: `chrome://extensions`
2. Turn on **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `extension` folder inside the folder you downloaded
5. The Web AI Agent icon will appear in your Chrome toolbar

### Step 4 — Open the side panel

Click the Web AI Agent icon in the Chrome toolbar.  
The side panel opens. Type a question to get started.

---

## FortiCNAPP credentials — two ways to set them up

### Option A — Using the setup script (easiest)

When you run `setup.sh` or `setup.ps1`, it will ask if you want to configure FortiCNAPP. Answer **y** and follow the prompts. You'll need:

- Your **FortiCNAPP account name** (e.g. `your-company`)
- Your **API Key** and **API Secret** — find these in FortiCNAPP under **Settings → API Keys**

### Option B — Paste credentials into the config file

Open the `.env` file in the folder (any text editor works) and fill in these three lines:

```
LW_ACCOUNT=your-account-name
LW_API_KEY=your-api-key-here
LW_API_SECRET=your-api-secret-here
```

Save the file and restart the server (re-run `setup.sh` or `setup.ps1`).

---

## Stopping and restarting the server

The server runs quietly in the background while you use Chrome.

**To stop it:**
- macOS/Linux: `kill $(cat .serve.pid)`
- Windows: `Stop-Process -Id (Get-Content .serve.pid)`

**To restart it:**  
Just run `./setup.sh` (or `.\setup.ps1`) again.

---

## Troubleshooting

**The side panel says "not connected" or buttons are greyed out**
- Make sure the server is running — open `http://localhost:8765` in Chrome; you should see a chat page
- If it's not running, open Terminal / PowerShell in the extension folder and run `./setup.sh` again

**"Cannot scan a browser page" when clicking Scan**
- Navigate to a real webpage first (not a Chrome settings page), then click Scan

**Scan runs but finds nothing**
- The page needs to have visible code on it (e.g. a GitHub repository page, a code documentation page)
- On a GitHub repo page, it automatically fetches the actual source files

**LQL / CVE / Compliance buttons are greyed out**
- Your FortiCNAPP credentials aren't set up yet — see the credentials section above

**🛡 Scan is greyed out but other buttons work**
- The lacework CLI isn't installed on your machine — run `./setup.sh` and answer **y** when asked to install it

---

## Privacy & security

Your API keys and credentials are never sent anywhere except the services they belong to:

| Data | Where it's stored | When it's cleared |
|---|---|---|
| Gateway URL + API key | Your browser's memory only | When you close Chrome |
| Chat history | Your browser's memory only | When you close the side panel |
| Page content you read | Your browser's memory only | Never saved to disk |
| FortiCNAPP credentials | Your machine only (`~/.lacework.toml` or `.env`) | You control this |

The small server (`serve.py`) only listens on your own computer (`localhost`) — nothing is accessible from outside your machine.

---

## For technical users

<details>
<summary>Manual start, configuration keys, API endpoints</summary>

### Manual start

```bash
cp .env.tpl .env        # fill in ANTHROPIC_BASE_URL and BIFROST_VIRTUAL_KEY
python3 serve.py        # starts on http://localhost:8765
```

### Configuration keys (`.env`)

| Key | Description |
|---|---|
| `ANTHROPIC_BASE_URL` | AI gateway endpoint |
| `BIFROST_VIRTUAL_KEY` | Gateway virtual key (`sk-bf-…`) |
| `ANTHROPIC_DEFAULT_MODEL` | Model for chat + LQL Generate (default: `claude-haiku-4-5`) |
| `LQL_QUERIES_DIR` | Path to `.yaml` LQL query files |
| `LW_ACCOUNT` | FortiCNAPP account name (alternative to `~/.lacework.toml`) |
| `LW_API_KEY` | FortiCNAPP API key |
| `LW_API_SECRET` | FortiCNAPP API secret |

### Backend endpoints

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

</details>
