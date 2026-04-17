# 🤖 BrothaBot v5.0

> A fully agentic Solana AI assistant for Telegram.  
> Trade. Chat. Research. Shop. Earn. All from one bot.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Solana](https://img.shields.io/badge/chain-Solana-9945FF)](https://solana.com)
[![PTB](https://img.shields.io/badge/telegram--bot-v20-blue)](https://python-telegram-bot.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## ✨ What is BrothaBot?

BrothaBot is an open-source, self-hosted Telegram bot that acts as your personal Solana AI agent. It combines a conversational AI brain with real on-chain functionality — so when you say "buy bonk," it actually opens the buy flow. When you say "send 0.1 SOL privately," it routes through Tor. When you say "get me a Netflix gift card," it places the order.

This is not a chatbot that tells you *how* to do things. It *does* them.

---

## 🚀 Key Features

### 💳 x402 Payment Protocol
BrothaBot supports the [x402 micropayment protocol](https://x402.org) — an emerging standard that enables bots and AI agents to autonomously pay for paywalled web resources using on-chain transactions.

- Paste any x402-compatible URL and say "pay" or "unlock"
- Bot detects the `402 Payment Required` response header
- Shows you the cost and token required (USDC by default)
- One-tap approve → sign → confirm tx hash
- Fully logged per-user in the local database

This positions BrothaBot as a first-class participant in the emerging **agentic economy** where AI agents transact on behalf of users.

---

### ◎ Solana Wallet Creation (Auto)
Every new user gets a Solana wallet created automatically on `/start` via the [Helius](https://helius.dev) RPC.

- **No seed phrase confusion** — wallet is managed server-side for the bot context
- View SOL balance and SPL token holdings inline
- NFT portfolio via Helius API (`/nft`)
- Users can also paste any external wallet address to check balances

> ⚠️ For production, consider encrypting private keys at rest or integrating a non-custodial flow.

---

### 🔐 Token Gating & Subscription Tiers

BrothaBot has a multi-tier access system with token-gated perks for `$BROTHA` holders:

| Tier           | AI Model                      | Daily Limit | How to Unlock             |
|----------------|-------------------------------|-------------|---------------------------|
| `free`         | Mistral 7B (free tier)        | 50 msgs     | Default                   |
| `trial`        | Mistral 7B (free tier)        | 10 msgs     | New users                 |
| `brotha_holder`| LLaMA 3 8B                   | 250 msgs    | Hold `$BROTHA` token      |
| `pro`          | LLaMA 3 8B                   | 500 msgs    | Paid subscription         |
| `power`        | LLaMA 3 70B                  | 2,000 msgs  | Power subscription        |
| `god`          | Claude 3.5 Sonnet             | Unlimited   | God tier subscription     |
| `gifted`       | LLaMA 3 70B                  | Unlimited   | Owner-granted access      |
| `owner`        | Claude 3.5 Sonnet             | Unlimited   | Bot owner only            |

All tiers are stored in SQLite and can be updated by the owner via:
```
/airdrop @username <points>
```

---

### 🪙 $BROTHA Token Ecosystem

`$BROTHA` is the native points/reward token of the BrothaBot ecosystem.

**How to earn points:**
- `+1 pt` per chat message
- `+10 pts` per DEX swap
- `+15 pts` per trade
- `+50 pts` per referral
- `+2 pts` per DAO vote

**Ecosystem features:**
- `/brotha` — Live price, market cap, volume, buy/sell pressure
- `/leaderboard` — Top earners ranked globally
- `/earn` — Your points, rank, and recent activity
- `/dao` — Vote on proposals, submit new ones
- `/airdrop` — Owner can airdrop points to any user

Token is tracked via [DexScreener](https://dexscreener.com) and links to pump.fun on launch.

---

### 🤖 AI Brain — Hybrid Local + Cloud

BrothaBot automatically detects your server's RAM and routes AI calls accordingly:

| RAM Free | Tier     | AI Used                        |
|----------|----------|--------------------------------|
| <1.5 GB  | `nano`   | OpenRouter (cloud only)        |
| 1.5 GB+  | `micro`  | OpenRouter (full speed)        |
| 4 GB+    | `small`  | Hermes 8B (local) + cloud      |
| 8 GB+    | `medium` | Hermes 8B full speed           |
| 16 GB+   | `large`  | Hermes + all tools             |
| 40 GB+   | `titan`  | All models collaborate         |

**Supported providers:**
- [OpenRouter](https://openrouter.ai) — cloud AI (required)
- [Ollama](https://ollama.com) — local AI via Hermes3 / Hermes3:70B (optional)

**Agent routing:** Messages are automatically classified and routed to the best specialist agent — `trader`, `researcher`, `scheduler`, `ordering`, `privacy`, `creative`, `solana`, or `assistant`.

---

### 📈 Trading & DeFi

- **Jupiter swaps** — Swap any SPL token via the best DEX route
- **Price alerts** — Get pinged when any coin hits your target
- **DCA plans** — Dollar-cost average by time interval, price drop, price rise, or target
- **Portfolio** — View open positions, PnL, take profit / stop loss levels
- **Advanced DCA** — Smart triggers with conditional sell rules

---

### 🔒 Private Send (Multi-hop Tor Mixer)

Send SOL anonymously through a multi-hop routing system:

- 1, 3, or 5 hop options
- Each hop rotates a Tor circuit
- 2% platform fee
- Queued with time delays for unlinkability
- Full history dashboard

---

### 🎁 Gift Cards via Bitrefill

Purchase gift cards with crypto directly in Telegram:

- Netflix, Spotify, Amazon, Steam, Uber, Xbox, Apple, Google Play, Starbucks, DoorDash, Target, Walmart, PlayStation
- Works in demo mode without an API key (for showcase)
- Set `BITREFILL_API_KEY` for live ordering

---

### 🧠 Self-Learning Memory

- Stores the last 20 messages per user as conversational memory
- Extracts "learnings" from factual exchanges and injects them into future AI context
- Auto-registers frequent short questions as custom commands

---

### 🎯 Custom Commands

Teach the bot new shortcuts:
```
remember 'gm' means Good morning king
```
Or use the owner command:
```
/teach "alpha" Here's today's alpha...
```

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An [OpenRouter](https://openrouter.ai) API key (free tier available)
- A [Helius](https://helius.dev) API key (free tier available)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/brothabot.git
cd brothabot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
nano .env  # Fill in your keys
```

### 4. Run the bot
```bash
python telegram_bot.py
```

---

## ⚙️ Configuration Reference

| Variable            | Required | Description                                              |
|---------------------|----------|----------------------------------------------------------|
| `TELEGRAM_TOKEN`    | ✅       | Bot token from @BotFather                               |
| `OPENROUTER_API_KEY`| ✅       | Cloud AI provider key                                   |
| `HELIUS_API_KEY`    | ✅       | Solana RPC + NFT API                                    |
| `OWNER_ID`          | ✅       | Your Telegram user ID (find via @userinfobot)           |
| `BROTHA_MINT`       | —        | $BROTHA token mint address (set after launch)           |
| `BITREFILL_API_KEY` | —        | Gift card ordering (demo mode works without this)       |
| `X402_ENABLED`      | —        | Set to `1` to enable x402 payment protocol              |
| `X402_FACILITATOR`  | —        | x402 facilitator URL                                    |
| `OLLAMA_URL`        | —        | Local AI endpoint (default: `http://localhost:11434`)   |
| `LOW_RAM`           | —        | Set to `1` to force cloud-only mode on low-RAM servers  |
| `FREE_MODE`         | —        | Set to `1` to unlock all features for everyone (demo)   |
| `DB_PATH`           | —        | SQLite database path (default: `brothabot.db`)          |

---

## 📁 Project Structure

```
brothabot/
├── telegram_bot.py     # Main bot — all logic in one file
├── trading.py          # Optional: advanced trading module
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Keeps secrets out of git
└── README.md           # This file
```

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to the branch
5. Open a pull request

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits & Stack

| Tool | Purpose |
|------|---------|
| [python-telegram-bot v20](https://python-telegram-bot.org) | Telegram bot framework |
| [OpenRouter](https://openrouter.ai) | Multi-model cloud AI |
| [Ollama](https://ollama.com) | Local LLM inference |
| [Helius](https://helius.dev) | Solana RPC + NFT data |
| [Jupiter](https://jup.ag) | Solana DEX aggregator |
| [DexScreener](https://dexscreener.com) | Token price data |
| [CoinGecko](https://coingecko.com) | Market data |
| [Bitrefill](https://bitrefill.com) | Gift card ordering |
| [x402.org](https://x402.org) | Micropayment protocol |
| [Tor](https://torproject.org) | Privacy routing |

---

*Built for the Solana ecosystem. Not financial advice.*
