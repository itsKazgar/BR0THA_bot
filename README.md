# 🤖 BrothaBot v6.0

**The Solana AI agent with a real personality.**  
Trade. Chat. Research. Shop. Automate. All from Telegram.

## 🧠 AI Architecture — The Brain

BrothaBot runs a **cascading AI system** that automatically picks the best model based on your available RAM:

┌─────────────────────────────────────────────────────────┐
│                   ONE BRAIN — AI Router                 │
├─────────────────────────────────────────────────────────┤
│  🔥 TITAN (40GB+)   Hermes 70B + Hermes 8B + OpenRouter │
│                     → all 3 models collaborate          │
│                                                         │
│  🟢 Large  (16GB+)  Hermes 8B (local) first             │
│  🟠 Medium  (8GB+)  Hermes 8B (full speed)              │
│  🟡 Small   (4GB+)  Hermes 8B unlocked  ← sweet spot   │
│                                                         │
│  ☁️  Micro  (1.5GB)  OpenRouter cloud only              │
│  💤 Nano    (0GB)   OpenRouter cloud only               │
└─────────────────────────────────────────────────────────┘
```

**Hermes** runs 100% locally via [Ollama](https://ollama.com) — no data sent to the cloud.  
**OpenRouter** is the cloud fallback when Hermes isn't available.

### Installing Hermes (local AI)

```bash
# Install Ollama
brew install ollama           # macOS
# or: curl -fsSL https://ollama.com/install.sh | sh  (Linux)

# Start Ollama
ollama serve

# Pull Hermes 8B (needs ~5 GB disk, ~4 GB RAM)
ollama pull hermes3

# Pull Hermes 70B TITAN (needs ~40 GB disk + RAM — optional)
ollama pull hermes3:70b
```

Then start BrothaBot — it auto-detects Hermes at startup.

### RAM Tier Check

Send `/hermes` in Telegram to see real-time Hermes status, RAM usage, and run a live test.  
Send `/system` for the full AI status dashboard.

---

## ✅ Features

| Feature | Status |
|---|---|
| Hermes 8B local AI | ✅ (needs 4 GB free RAM) |
| Hermes 70B TITAN | ✅ (needs 40 GB free RAM) |
| OpenRouter cloud fallback | ✅ |
| Collaborative AI (all models) | ✅ TITAN tier |
| Solana price alerts | ✅ |
| Jupiter swaps | ✅ (requires trading module) |
| DCA automation | ✅ |
| Private sends via Tor | ✅ |
| Gift cards (Bitrefill) | ✅ |
| X402 micropayments | ✅ |
| Self-learning memory | ✅ |
| Custom commands | ✅ |
| Natural language intent parser | ✅ |
| Button dashboards | ✅ |
| BROTHA token live price | ✅ |
| Web search | ✅ (DuckDuckGo) |
| Crypto news feed | ✅ |
| Fear & Greed index | ✅ |
| Market dominance | ✅ |

---

## 🚀 Quickstart

### 1. Clone + install

```bash
git clone https://github.com/itsKazgar/BR0THA_bot.git
cd BR0THA_bot
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
nano .env
```

Fill in at minimum:
```
TELEGRAM_TOKEN=your_bot_token_from_BotFather
OPENROUTER_API_KEY=sk-or-v1-...
OWNER_ID=your_telegram_user_id
```

### 3. (Optional) Install Hermes for local AI

```bash
ollama serve
ollama pull hermes3
```

### 4. Run

```bash
python3 telegram_bot.py
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `OPENROUTER_API_KEY` | ✅ | From [openrouter.ai](https://openrouter.ai) — cloud AI |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `HELIUS_API_KEY` | Recommended | Fast Solana RPC — [helius.dev](https://helius.dev) |
| `AGENT_WALLET` | For deposits | Solana wallet address to receive SOL |
| `OLLAMA_URL` | Optional | Default: `http://localhost:11434` |
| `OLLAMA_MODEL` | Optional | Default: `hermes3` |
| `OLLAMA_TITAN_MODEL` | Optional | Default: `hermes3:70b` |
| `BROTHA_MINT` | Optional | Token CA (defaults to BROTHA) |
| `BITREFILL_API_KEY` | Optional | For live gift card orders |
| `X402_ENABLED` | Optional | Set `true` to enable micropayments |
| `LOW_RAM` | Optional | Set `1` to force cloud-only mode |

---

## 💬 Commands

| Command | Description |
|---|---|
| `/start` | Launch bot, show dashboard |
| `/hermes` | **Hermes AI status + live test** |
| `/system` | Full AI + system dashboard |
| `/status` | Your tier, balance, AI status |
| `/price <coin>` | Live price (sol, btc, eth, brotha, etc.) |
| `/market` | Full market dashboard |
| `/balance <wallet>` | Check any Solana wallet |
| `/giftcard <brand> <amount>` | Buy a gift card with crypto |
| `/brain` | Show what the bot has learned |
| `/commands` | List custom commands |
| `/teach "trigger" response` | Teach the bot a new command |
| `/health` | Owner: server health dashboard |

**Natural language** — just type what you want:
- `"buy 0.1 SOL of bonk"`
- `"alert me when SOL hits 200"`
- `"send 0.5 SOL privately"`
- `"buy me a $25 Netflix gift card"`
- `"what's trending on Solana"`

---

## 🤖 How Hermes Integration Works

```python
# 1. Bot starts → detects Ollama + checks RAM
def detect_ollama() -> tuple[bool, list]:
    ...

# 2. Every message routes through the unified brain
def ask(prompt, tier, history, agent, collaborative):
    ram = get_ram_info()

    # TITAN MODE — all models collaborate
    if collaborative and ram["can_run_all"]:
        return ask_collaborative(...)   # Hermes 8B + 70B + OpenRouter

    # LOCAL — Hermes 8B runs on your machine
    if ram["can_run_hermes"] and USE_LOCAL_AI:
        reply = call_hermes(prompt, ...)
        if reply:
            return reply   # fast, local, private

    # CLOUD FALLBACK — OpenRouter
    return call_openrouter(prompt, ...)

# 3. call_hermes() has built-in RAM checks + graceful fallback
def call_hermes(prompt, system, history, model):
    ram = get_ram_info()
    if not ram["can_run_hermes"]:
        return None   # caller falls back to OpenRouter
    ...
```

The bot **never crashes** if Hermes is offline — it silently falls back to OpenRouter.

---

## 🗂️ Project Structure

```
BR0THA_bot/
├── telegram_bot.py     # Main bot (this file)
├── trading.py          # Jupiter swap + wallet management (optional)
├── requirements.txt    # Python dependencies
├── .env.example        # Config template
├── .gitignore
└── data/
    └── agent.db        # SQLite database (auto-created)
```

---

## 🔧 WSL / Low RAM Tips

If you're running on WSL with limited RAM:

```ini
# ~/.wslconfig
[wsl2]
memory=8GB      # give WSL 8 GB for Hermes 8B
processors=4
```

Then: `wsl --shutdown` and restart.

Or force cloud-only mode:
```
LOW_RAM=1
```

---

## 📦 Requirements

```
python-telegram-bot>=20.0
requests
httpx
feedparser
beautifulsoup4
psutil
python-dotenv
```

Optional (for local AI):
- [Ollama](https://ollama.com) — runs Hermes locally
- Model: `hermes3` (8B) or `hermes3:70b` (70B)

---

## 🪙 BROTHA Token

- **Contract:** `3Zz6oGYdPdtwukwxLSvpJcUSuFgABpeZo2kGURtApump`
- **Chart:** [dexscreener.com/solana/3Zz6...](https://dexscreener.com/solana/3Zz6oGYdPdtwukwxLSvpJcUSuFgABpeZo2kGURtApump)
- **Buy:** [pump.fun](https://pump.fun/coin/3Zz6oGYdPdtwukwxLSvpJcUSuFgABpeZo2kGURtApump)

---

## 📄 License

MIT — use it, fork it, build on it.

---

*Built by [@itsKazgar](https://github.com/itsKazgar)*
