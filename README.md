# 🤖 BR0THA_bot v6.0

**The Solana AI agent with a real personality.**  
Trade. Chat. Research. Shop. Automate. Create wallets. All from Telegram.

---

## 🧠 AI Architecture — The Brain

BR0THA_bot runs a **cascading AI system** that automatically picks the best model based on your available RAM:

```
┌─────────────────────────────────────────────────────────┐
│                   ONE BRAIN — AI Router                 │
├─────────────────────────────────────────────────────────┤
│  🔥 TITAN (40GB+)   Hermes 70B + Hermes 8B + OpenRouter │
│                     → all 3 models collaborate          │
│                                                         │
│  🟢 Large  (16GB+)  Hermes 8B — stable & fast           │
│  🟠 Medium  (8GB+)  Hermes 8B — recommended minimum    │
│  🟡 Small   (4GB+)  Hermes 8B — may be slow/unstable   │
│                                                         │
│  ☁️  Micro  (1.5GB)  OpenRouter cloud only              │
│  💤 Nano    (0GB)   OpenRouter cloud only               │
└─────────────────────────────────────────────────────────┘
```

> ⚠️ **Hermes needs ~4 GB of *free* RAM** — not total. If your system is already using most of its memory, BR0THA_bot will automatically fall back to OpenRouter cloud AI. The `Medium (8GB+)` tier is the practical sweet spot for reliable local inference.

**Hermes** runs 100% locally via [Ollama](https://ollama.com) — no data sent to the cloud.  
**OpenRouter** is the cloud fallback when Hermes isn't available or RAM is too low.

### Installing Hermes (local AI)

```bash
# Install Ollama
brew install ollama           # macOS
# or: curl -fsSL https://ollama.com/install.sh | sh  (Linux)

# Start Ollama
ollama serve

# Pull Hermes 8B (needs ~5 GB disk, ~4 GB *free* RAM to run)
ollama pull hermes3

# Pull Hermes 70B TITAN (needs ~40 GB disk + RAM — optional)
ollama pull hermes3:70b
```

Then start BR0THA_bot — it auto-detects Hermes and your available RAM at startup.

### RAM Tier Check

Send `/hermes` in Telegram to see real-time Hermes status, RAM usage, and run a live test.  
Send `/system` for the full AI status dashboard.

---

## ✅ Features

| Feature | Status |
|---|---|
| Hermes 8B local AI | ✅ (needs 4 GB *free* RAM) |
| Hermes 70B TITAN | ✅ (needs 40 GB *free* RAM) |
| OpenRouter cloud fallback | ✅ automatic |
| Collaborative AI (all models) | ✅ TITAN tier |
| **Solana wallet creation** | ✅ (requires trading module) |
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
| Web search | ✅ (DuckDuckGo) |
| Crypto news feed | ✅ |
| Fear & Greed index | ✅ |
| Market dominance | ✅ |

---

## 🔑 Wallet Creation

BR0THA_bot can generate a fresh Solana wallet for you on the spot — no browser or external tools needed.

> Requires `trading.py` to be present alongside the main bot file.

Just ask:
- `"create me a wallet"`
- `"make a new Solana wallet"`
- `"generate a wallet address"`

BR0THA_bot will generate a new keypair and display your **public address** and **private key** directly in Telegram. Once created, you can immediately use that address to receive SOL or tokens, set it as your agent wallet in `.env`, or start trading — all without leaving the chat.

> ⚠️ BR0THA_bot never stores your private key. You are fully responsible for backing it up securely offline.

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

> **Note:** Hermes 8B needs roughly 4 GB of *free* RAM to run. If your system has 8 GB total, Hermes works best when other apps aren't eating into available memory. See the WSL tips below if you're on Windows.

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
| `BITREFILL_API_KEY` | Optional | For live gift card orders |
| `X402_ENABLED` | Optional | Set `true` to enable micropayments |
| `LOW_RAM` | Optional | Set `1` to skip Hermes entirely and use cloud-only mode |

---

## 💬 Commands

| Command | Description |
|---|---|
| `/start` | Launch bot, show dashboard |
| `/hermes` | **Hermes AI status + live test** |
| `/system` | Full AI + system dashboard |
| `/status` | Your tier, balance, AI status |
| `/price <coin>` | Live price (sol, btc, eth, etc.) |
| `/market` | Full market dashboard |
| `/balance <wallet>` | Check any Solana wallet |
| `/giftcard <brand> <amount>` | Buy a gift card with crypto |
| `/brain` | Show what the bot has learned |
| `/commands` | List custom commands |
| `/teach "trigger" response` | Teach the bot a new command |
| `/health` | Owner: server health dashboard |

**Natural language** — just type what you want:
- `"create me a wallet"`
- `"buy 0.1 SOL of bonk"`
- `"alert me when SOL hits 200"`
- `"send 0.5 SOL privately"`
- `"buy me a $25 Netflix gift card"`
- `"what's trending on Solana"`

---

## 🤖 How Hermes Integration Works

```python
# 1. Bot starts → detects Ollama + checks free RAM
def detect_ollama() -> tuple[bool, list]:
    if os.getenv("LOW_RAM") == "1":
        return False, []   # skip Hermes entirely
    ...

# 2. Every message routes through the unified brain
def ask(prompt, tier, history, agent, collaborative):
    ram = get_ram_info()

    # TITAN MODE — all models collaborate
    if collaborative and ram["can_run_all"]:        # needs 40 GB free
        return ask_collaborative(...)

    # LOCAL — Hermes 8B (needs 4 GB free RAM)
    if ram["can_run_hermes"] and USE_LOCAL_AI:
        reply = call_hermes(prompt, ...)
        if reply:
            return reply   # fast, local, private

    # CLOUD FALLBACK — always available
    return call_openrouter(prompt, ...)

# 3. call_hermes() checks free RAM before every call
def call_hermes(prompt, system, history, model):
    ram = get_ram_info()
    if not ram["can_run_hermes"]:   # < 4 GB free
        return None                 # silently falls back to cloud
    ...
```

BR0THA_bot **never crashes** if Hermes is offline or RAM is too low — it silently falls back to OpenRouter.

---

## 🗂️ Project Structure

```
BR0THA_bot/
├── telegram_bot.py     # Main bot
├── trading.py          # Jupiter swap + wallet creation (optional)
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
memory=8GB      # give WSL 8 GB so Hermes 8B has room to breathe
processors=4
```

Then: `wsl --shutdown` and restart.

Or skip Hermes entirely and run cloud-only:
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

## 📄 License

MIT — use it, fork it, build on it.

---

*Built by [@itsKazgar](https://github.com/itsKazgar)*
