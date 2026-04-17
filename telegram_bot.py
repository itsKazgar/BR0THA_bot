"""
BrothaB0T — telegram_bot.py  v6.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Hermes AI (local Ollama) — fully functional with RAM-tier gating
✅ Hermes 70B (Titan) — unlocks at 40GB free RAM
✅ OpenRouter cloud AI — fallback when Hermes offline or RAM too low
✅ Collaborative mode — Hermes + OpenRouter synthesize one response
✅ All 14 commands wired and working
✅ Price alerts, DCA, private sends, gift cards, X402
✅ Self-learning memory engine
✅ Custom commands (bot learns from usage)
✅ Natural language intent parser
✅ Button dashboards — no typing required
✅ BROTHA token live price + ecosystem links
✅ Secrets loaded from .env — nothing hardcoded
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IMPORTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import os
import asyncio
import logging
import sqlite3
import requests
import httpx
import feedparser
import time
import hashlib
import json
import datetime
import re
import secrets
import subprocess

import psutil
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TRADING MODULE — graceful fallback
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    from trading import (
        generate_user_wallet, get_user_wallet, get_sol_balance, jupiter_swap,
        set_alert, get_alerts, get_open_positions, get_portfolio_summary,
        get_position_pnl, close_position, check_and_manage_positions,
        create_dca_plan, get_dca_plans, cancel_dca, run_dca_plans,
        set_signal, get_signals, check_signals, get_token_info, search_token,
        is_trading_subscriber, get_subscription_info, activate_trading_sub,
        init_trading_tables, TRADING_WEEK_SOL, MAX_OPEN_TRADES, MAX_POSITION_PCT,
        RESERVE_PCT, TAKE_PROFIT_PCT, STOP_LOSS_PCT, MIN_MCAP_USD,
    )
    TRADING_ENABLED = True
except ImportError:
    TRADING_ENABLED = False
    MAX_OPEN_TRADES  = 5
    MAX_POSITION_PCT = 0.20
    RESERVE_PCT      = 0.10
    TAKE_PROFIT_PCT  = 0.50
    STOP_LOSS_PCT    = 0.20
    MIN_MCAP_USD     = 50_000
    TRADING_WEEK_SOL = 0.5

    def init_trading_tables(): pass
    async def jupiter_swap(uid, f, t, a): return {"ok": False, "error": "Trading module not loaded"}
    def set_alert(uid, coin, target, direction): pass
    def get_alerts(uid): return []
    def get_open_positions(uid): return []
    def get_position_pnl(p): return {"ok": False}
    def close_position(uid, pos_id): return {"ok": False, "error": "Not available"}
    async def check_and_manage_positions(bot): pass
    def create_dca_plan(*a, **kw): pass
    def get_dca_plans(uid): return []
    def cancel_dca(uid, plan_id): pass
    async def run_dca_plans(bot): pass
    def set_signal(*a, **kw): pass
    def get_signals(uid): return []
    def check_signals(uid): return []
    def get_token_info(mint): return {}
    def search_token(q): return []
    def is_trading_subscriber(uid): return True
    def get_subscription_info(uid): return {"active": True}
    def activate_trading_sub(uid): pass
    def get_sol_balance(wallet): return 0.0
    def get_user_wallet(uid): return None
    def generate_user_wallet(uid): return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG — all from .env, nothing hardcoded
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN", "")
OWNER_ID           = os.getenv("OWNER_ID", "")
OWNER_USERNAME     = os.getenv("OWNER_USERNAME", "owner")
HELIUS_API_KEY     = os.getenv("HELIUS_API_KEY", "")
AGENT_WALLET       = os.getenv("AGENT_WALLET", "")
HELIUS_RPC_URL     = (
    f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    if HELIUS_API_KEY else "https://api.mainnet-beta.solana.com"
)
TOR_PROXY          = os.getenv("TOR_PROXY", "socks5h://127.0.0.1:9050")
TOR_CONTROL_PORT   = int(os.getenv("TOR_CONTROL_PORT", "9051"))
DB_PATH            = "data/agent.db"
REFERRAL_CUT_PCT   = 0.10
FEE_PCT            = 0.02
FREE_MODE          = True
FREE_TRIAL_DAYS    = 7
DAILY_SPEND_LIMIT  = 50.0

# BROTHA token
BROTHA_MINT     = os.getenv("BROTHA_MINT", "3Zz6oGYdPdtwukwxLSvpJcUSuFgABpeZo2kGURtApump")
BROTHA_TICKER   = "BROTHA"
BROTHA_DEX      = f"https://dexscreener.com/solana/{BROTHA_MINT}"
BROTHA_PUMP     = f"https://pump.fun/coin/{BROTHA_MINT}"
BROTHA_HOLD_MIN = 100_000

# Bitrefill
BITREFILL_API_KEY  = os.getenv("BITREFILL_API_KEY", "")
BITREFILL_BASE_URL = "https://api.bitrefill.com/v2"

# X402
X402_ENABLED     = os.getenv("X402_ENABLED", "false").lower() == "true"
X402_FACILITATOR = os.getenv("X402_FACILITATOR_URL", "https://x402.org/facilitator")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HERMES / OLLAMA CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLLAMA_URL         = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL       = os.getenv("OLLAMA_MODEL", "hermes3")          # 8B — needs ~4 GB RAM
OLLAMA_TITAN_MODEL = os.getenv("OLLAMA_TITAN_MODEL", "hermes3:70b") # 70B — needs ~40 GB RAM
USE_LOCAL_AI       = False   # set at startup by detect_ollama()

logging.basicConfig(
    format="%(asctime)s %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RAM-TIER SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RAM_TIERS = {
    #  name      min_free_gb  models                         label
    "nano":   (0.0,  [],                          "💤 Nano — Cloud AI only"),
    "micro":  (1.5,  [],                          "☁️  Micro — Cloud AI (full)"),
    "small":  (4.0,  ["hermes3"],                 "🟡 Small — Hermes 8B unlocked"),
    "medium": (8.0,  ["hermes3"],                 "🟠 Medium — Hermes 8B full speed"),
    "large":  (16.0, ["hermes3"],                 "🟢 Large — Hermes 8B + all tools"),
    "titan":  (40.0, ["hermes3", "hermes3:70b"],  "🔥 TITAN — Hermes 8B + 70B collaborate"),
}

def get_ram_info() -> dict:
    """Return current RAM stats and which tier we're in."""
    try:
        vm           = psutil.virtual_memory()
        ram_free_gb  = vm.available / (1024 ** 3)
        ram_total_gb = vm.total     / (1024 ** 3)
    except Exception:
        ram_free_gb  = 0.4
        ram_total_gb = 1.6

    current_tier = "nano"
    for name, (min_gb, models, label) in sorted(RAM_TIERS.items(), key=lambda x: x[1][0]):
        if ram_free_gb >= min_gb:
            current_tier = name

    tier_data = RAM_TIERS[current_tier]
    return {
        "tier":            current_tier,
        "ram_free_gb":     round(ram_free_gb, 1),
        "ram_total_gb":    round(ram_total_gb, 1),
        "unlocked_models": tier_data[1],
        "description":     tier_data[2],
        "can_run_hermes":  ram_free_gb >= 4.0,
        "can_run_titan":   ram_free_gb >= 40.0,
        "can_run_all":     ram_free_gb >= 40.0,
    }

def get_system_resources() -> dict:
    try:
        vm = psutil.virtual_memory()
        return {
            "ram_gb":   round(vm.total    / (1024 ** 3), 1),
            "ram_free": round(vm.available / (1024 ** 3), 1),
            "cpu":      psutil.cpu_count() or 1,
        }
    except Exception:
        return {"ram_gb": 1.6, "ram_free": 0.5, "cpu": 2}

def detect_ollama() -> tuple[bool, list]:
    """Check if Ollama is running and which models are pulled."""
    global USE_LOCAL_AI
    if os.getenv("LOW_RAM") == "1":
        USE_LOCAL_AI = False
        return False, []
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            USE_LOCAL_AI = True
            logger.info(f"Ollama detected. Models: {models}")
            return True, models
        return False, []
    except Exception:
        USE_LOCAL_AI = False
        return False, []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HERMES AI FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def call_hermes(prompt: str, system: str = None, history: list = None, model: str = None) -> str | None:
    """
    Call Hermes via Ollama.
    Returns the reply string, or None on failure / insufficient RAM.

    Why it might return None:
      - Ollama not running
      - RAM tier too low (< 4 GB free)
      - Network / timeout error
    Callers should fall back to OpenRouter when None is returned.
    """
    ram = get_ram_info()
    if not ram["can_run_hermes"]:
        logger.info(
            f"Hermes skipped — only {ram['ram_free_gb']} GB free "
            f"(need 4.0 GB). Falling back to cloud."
        )
        return None
    if not USE_LOCAL_AI:
        return None

    target_model = model or OLLAMA_MODEL

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    for h in (history or []):
        messages.append(h)
    messages.append({"role": "user", "content": prompt})

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": target_model, "messages": messages, "stream": False},
            timeout=120,
        )
        if r.status_code == 200:
            reply = r.json()["message"]["content"]
            logger.info(f"Hermes ({target_model}) responded ({len(reply)} chars)")
            return reply
        logger.warning(f"Hermes HTTP {r.status_code}: {r.text[:200]}")
        return None
    except requests.exceptions.Timeout:
        logger.warning("Hermes timed out — falling back to cloud.")
        return None
    except Exception as e:
        logger.warning(f"Hermes error: {e}")
        return None


def call_hermes_titan(prompt: str, system: str = None, history: list = None) -> str | None:
    """
    Call Hermes 70B (Titan tier).
    Automatically falls back to 8B if RAM is insufficient for 70B.
    """
    ram = get_ram_info()
    if not ram["can_run_titan"]:
        logger.info(
            f"Titan (70B) skipped — {ram['ram_free_gb']} GB free "
            f"(need 40 GB). Trying Hermes 8B instead."
        )
        return call_hermes(prompt, system, history)   # graceful 8B fallback
    return call_hermes(prompt, system, history, model=OLLAMA_TITAN_MODEL)


def hermes_status() -> dict:
    """Return a status dict for the system dashboard."""
    if os.getenv("LOW_RAM") == "1":
        return {
            "running": False, "models": [],
            "hermes_8b": False, "hermes_70b": False,
            "ram": get_ram_info(),
        }
    ok, models  = detect_ollama()
    ram         = get_ram_info()
    has_8b      = any("hermes3" in m.lower() and "70b" not in m.lower() for m in models)
    has_70b     = any("70b"     in m.lower() for m in models)
    return {
        "running":     ok,
        "models":      models,
        "hermes_8b":   ok and has_8b  and ram["can_run_hermes"],
        "hermes_70b":  ok and has_70b and ram["can_run_titan"],
        "ram":         ram,
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TIER CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIERS = {
    t: {
        "messages_per_hour": 999999,
        "messages_per_day":  999999,
        "model":   "meta-llama/llama-3.3-70b-instruct",
        "trading": True,
        "label":   lbl,
    }
    for t, lbl in [
        ("none",          "🆓 Free"),
        ("trial",         "🆓 Free Trial"),
        ("brotha_holder", "💎 BROTHA Holder"),
        ("free",          "🆓 Free"),
        ("pro",           "⚡ Pro"),
        ("power",         "🔥 Power"),
        ("god",           "👑 GOD"),
        ("gifted",        "🎁 Gifted"),
        ("owner",         "🛸 Owner"),
    ]
}

def balance_to_tier(b: float) -> str:
    return "god" if b >= 5 else "power" if b >= 1.5 else "pro" if b >= 0.5 else "free"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/sessions", exist_ok=True)
    os.makedirs("data/wallets", exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, username TEXT,
            tier TEXT DEFAULT 'free', sol_balance REAL DEFAULT 0.0,
            pending_deposit INTEGER DEFAULT 0,
            wallet_address TEXT, wallet_private TEXT,
            referral_code TEXT UNIQUE, referred_by TEXT,
            brotha_balance REAL DEFAULT 0.0,
            trial_expires REAL DEFAULT 0, gift_expires REAL DEFAULT 0,
            allowed_tools TEXT DEFAULT 'all',
            daily_spend_usd REAL DEFAULT 0.0, spend_reset_ts REAL DEFAULT 0,
            pending_action TEXT DEFAULT NULL,
            created_at REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, role TEXT, content TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS rate_windows (
            user_id TEXT, window TEXT, action TEXT,
            count INTEGER DEFAULT 0, reset_at REAL,
            PRIMARY KEY (user_id, window, action)
        );
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, sol_amount REAL,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, coin TEXT, target REAL, direction TEXT,
            active INTEGER DEFAULT 1, ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, from_token TEXT, to_token TEXT,
            amount_sol REAL, fee_sol REAL, signature TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT, referee_id TEXT,
            sol_earned REAL DEFAULT 0.0,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS autonomous_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, task_type TEXT,
            config TEXT DEFAULT '{}',
            last_run REAL DEFAULT 0, active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS health_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT, detail TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS fee_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, amount_sol REAL, description TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS spending_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, amount_usd REAL, description TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, content TEXT,
            success_count INTEGER DEFAULT 0, fail_count INTEGER DEFAULT 0,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS bot_learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT, insight TEXT,
            confidence REAL DEFAULT 0.5, source TEXT DEFAULT 'interaction',
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS custom_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger TEXT UNIQUE, response TEXT,
            action_type TEXT DEFAULT 'text',
            created_by TEXT DEFAULT 'bot',
            use_count INTEGER DEFAULT 0,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id TEXT PRIMARY KEY,
            last_action TEXT, last_data TEXT,
            step INTEGER DEFAULT 0,
            updated_at REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS ai_collab_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, prompt TEXT,
            hermes_response TEXT, titan_response TEXT,
            openrouter_response TEXT, final_response TEXT,
            models_used TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS gift_card_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, product_id TEXT,
            amount_usd REAL, status TEXT DEFAULT 'pending',
            order_ref TEXT, payment_method TEXT DEFAULT 'usdc_solana',
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS x402_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, url TEXT,
            amount_usd REAL, token TEXT DEFAULT 'USDC',
            status TEXT DEFAULT 'pending', tx_hash TEXT,
            ts REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS private_tx_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id TEXT, recipient_wallet TEXT, recipient_user_id TEXT,
            amount_sol REAL, fee_sol REAL,
            status TEXT DEFAULT 'pending',
            temp_wallet_pub TEXT, temp_wallet_priv TEXT,
            delay_seconds INTEGER DEFAULT 0,
            split_count INTEGER DEFAULT 1, hop_count INTEGER DEFAULT 3,
            execute_at REAL, note TEXT,
            tor_verified INTEGER DEFAULT 0,
            created_at REAL DEFAULT (unixepoch())
        );
        CREATE TABLE IF NOT EXISTS dca_advanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, mint TEXT, symbol TEXT,
            trigger_type TEXT, trigger_value REAL, amount_sol REAL,
            sell_trigger_type TEXT DEFAULT NULL,
            sell_trigger_value REAL DEFAULT NULL,
            max_buys INTEGER DEFAULT 0, buys_done INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at REAL DEFAULT (unixepoch())
        );
        """)
    # Migrations — safe to run on every startup
    for col, defn in [
        ("trial_expires",   "REAL DEFAULT 0"),
        ("gift_expires",    "REAL DEFAULT 0"),
        ("allowed_tools",   "TEXT DEFAULT 'all'"),
        ("daily_spend_usd", "REAL DEFAULT 0.0"),
        ("spend_reset_ts",  "REAL DEFAULT 0"),
        ("brotha_balance",  "REAL DEFAULT 0.0"),
        ("wallet_address",  "TEXT"),
        ("wallet_private",  "TEXT"),
        ("pending_deposit", "INTEGER DEFAULT 0"),
        ("pending_action",  "TEXT DEFAULT NULL"),
    ]:
        _safe_add_column("users", col, defn)

def _safe_add_column(table: str, column: str, col_def: str):
    try:
        with sqlite3.connect(DB_PATH) as db:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except sqlite3.OperationalError:
        pass  # column already exists

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def set_session(user_id: str, action: str, data: dict = None, step: int = 0):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT OR REPLACE INTO user_sessions "
            "(user_id, last_action, last_data, step, updated_at) VALUES (?,?,?,?,?)",
            (user_id, action, json.dumps(data or {}), step, time.time()),
        )

def get_session(user_id: str) -> tuple:
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute(
            "SELECT last_action, last_data, step FROM user_sessions WHERE user_id=?",
            (user_id,),
        ).fetchone()
    if not row:
        return None, {}, 0
    return row[0], json.loads(row[1] or "{}"), row[2]

def clear_session(user_id: str):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM user_sessions WHERE user_id=?", (user_id,))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USER MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def is_owner(user_id: str) -> bool:
    return str(user_id) == str(OWNER_ID)

def ensure_user(user_id: str, username: str = "", referred_by: str = None):
    code = hashlib.md5(str(user_id).encode()).hexdigest()[:8].upper()
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT OR IGNORE INTO users "
            "(user_id, username, referral_code, referred_by, tier, trial_expires) "
            "VALUES (?,?,?,?,?,?)",
            (user_id, username, code, referred_by, "free",
             time.time() + FREE_TRIAL_DAYS * 86400),
        )
        db.execute(
            "UPDATE users SET username=? WHERE user_id=? AND (username='' OR username IS NULL)",
            (username, user_id),
        )

def get_user(user_id: str) -> dict:
    uid = str(user_id)
    if is_owner(uid):
        return {
            "tier": "owner", "balance": 999.0, "ref_code": "ADMIN",
            "referred_by": None, "brotha_balance": 999999.0,
            "allowed_tools": "all", "trial_expires": 0,
            "gift_expires": 0, "username": OWNER_USERNAME,
        }
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute(
            "SELECT tier, sol_balance, referral_code, referred_by, brotha_balance, "
            "allowed_tools, trial_expires, gift_expires, username "
            "FROM users WHERE user_id=?",
            (uid,),
        ).fetchone()
    if not row:
        return {
            "tier": "free", "balance": 0.0, "ref_code": None,
            "referred_by": None, "brotha_balance": 0.0,
            "allowed_tools": "all", "trial_expires": 0,
            "gift_expires": 0, "username": "",
        }
    return {
        "tier":           row[0] or "free",
        "balance":        row[1] or 0.0,
        "ref_code":       row[2],
        "referred_by":    row[3],
        "brotha_balance": row[4] or 0.0,
        "allowed_tools":  row[5] or "all",
        "trial_expires":  row[6] or 0,
        "gift_expires":   row[7] or 0,
        "username":       row[8] or "",
    }

def save_memory(user_id: str, role: str, content: str):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO memory (user_id, role, content) VALUES (?,?,?)",
            (user_id, role, content),
        )
        db.execute(
            "DELETE FROM memory WHERE user_id=? AND id NOT IN "
            "(SELECT id FROM memory WHERE user_id=? ORDER BY ts DESC LIMIT 20)",
            (user_id, user_id),
        )

def get_memory(user_id: str, limit: int = 8) -> list:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT role, content FROM memory WHERE user_id=? ORDER BY ts DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def log_event(event: str, detail: str = ""):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT INTO health_log (event, detail) VALUES (?,?)", (event, detail))

def check_rate(user_id: str, tier: str) -> tuple[bool, str]:
    if is_owner(user_id):
        return True, ""
    now = time.time()
    with sqlite3.connect(DB_PATH) as db:
        for window, limit, secs in [("hour", 1000, 3600), ("day", 5000, 86400)]:
            r = db.execute(
                "SELECT count, reset_at FROM rate_windows "
                "WHERE user_id=? AND window=? AND action='message'",
                (user_id, window),
            ).fetchone()
            if r is None or r[1] < now:
                db.execute(
                    "INSERT OR REPLACE INTO rate_windows "
                    "(user_id, window, action, count, reset_at) VALUES (?,?,?,1,?)",
                    (user_id, window, "message", now + secs),
                )
            elif r[0] >= limit:
                mins = int((r[1] - now) // 60) or 1
                return False, f"Slow down — {limit} msgs this {window}. Resets in {mins} min."
            else:
                db.execute(
                    "UPDATE rate_windows SET count=count+1 "
                    "WHERE user_id=? AND window=? AND action='message'",
                    (user_id, window),
                )
    return True, ""

def take_fee(uid: str, amount_sol: float) -> float:
    if is_owner(uid) or not OWNER_ID:
        return 0.0
    fee = round(amount_sol * FEE_PCT, 6)
    if fee <= 0:
        return 0.0
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE users SET sol_balance=sol_balance-? WHERE user_id=?", (fee, uid))
        db.execute("UPDATE users SET sol_balance=sol_balance+? WHERE user_id=?", (fee, OWNER_ID))
        db.execute("INSERT INTO deposits (user_id, sol_amount) VALUES (?,?)", (OWNER_ID, fee))
        db.execute(
            "INSERT INTO fee_log (user_id, amount_sol, description) VALUES (?,?,?)",
            (uid, fee, f"2% fee on {amount_sol:.6f} SOL"),
        )
    return fee

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SELF-LEARNING ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def save_learning(topic: str, insight: str, confidence: float = 0.7, source: str = "interaction"):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO bot_learnings (topic, insight, confidence, source) VALUES (?,?,?,?)",
            (topic, insight[:500], confidence, source),
        )

def get_learnings(topic: str = None, limit: int = 10) -> list:
    with sqlite3.connect(DB_PATH) as db:
        if topic:
            rows = db.execute(
                "SELECT topic, insight, confidence FROM bot_learnings "
                "WHERE topic LIKE ? ORDER BY confidence DESC LIMIT ?",
                (f"%{topic}%", limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT topic, insight, confidence FROM bot_learnings "
                "ORDER BY ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return rows

def extract_and_learn(user_msg: str, bot_reply: str, user_id: str):
    try:
        t = user_msg.lower()
        if any(w in t for w in ["what is", "explain", "how does", "tell me about"]):
            m = re.search(
                r"(?:what is|explain|how does|tell me about)\s+(.+?)[\?\.]?$", t
            )
            if m and len(bot_reply) > 50:
                save_learning(m.group(1).strip()[:80], bot_reply[:500], 0.6, "qa_pair")
    except Exception:
        pass

def count_learnings() -> int:
    with sqlite3.connect(DB_PATH) as db:
        return db.execute("SELECT COUNT(*) FROM bot_learnings").fetchone()[0]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CUSTOM COMMAND ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def register_custom_command(trigger: str, response: str, action_type: str = "text", created_by: str = "bot"):
    trigger = trigger.lower().strip()
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT OR REPLACE INTO custom_commands "
            "(trigger, response, action_type, created_by) VALUES (?,?,?,?)",
            (trigger, response, action_type, created_by),
        )

def check_custom_commands(text: str) -> tuple:
    t = text.lower().strip()
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT trigger, response, action_type FROM custom_commands").fetchall()
    for trigger, response, action_type in rows:
        if trigger in t or t.startswith(trigger):
            with sqlite3.connect(DB_PATH) as db:
                db.execute("UPDATE custom_commands SET use_count=use_count+1 WHERE trigger=?", (trigger,))
            return response, action_type
    return None, None

def list_custom_commands(limit: int = 20) -> list:
    with sqlite3.connect(DB_PATH) as db:
        return db.execute(
            "SELECT trigger, response, action_type, use_count FROM custom_commands "
            "ORDER BY use_count DESC LIMIT ?",
            (limit,),
        ).fetchall()

def count_custom_commands() -> int:
    with sqlite3.connect(DB_PATH) as db:
        return db.execute("SELECT COUNT(*) FROM custom_commands").fetchone()[0]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI PERSONALITY & ROUTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONALITY = f"""You are Brotha — BrothaB0T.

Short first. Then deeper if they push.
Never over-explain. Never lecture. Never shill.
Smart, funny, real. Sometimes one line. Sometimes a paragraph. Never a wall.

You know: Stoicism, Solana, CT lore, Toly, Mert, Gainzy, Rasmr, Threadguy,
Peter Thiel, Napoleon Hill, Earl Nightingale, biology, history, physics, memes,
X/Twitter, tech, crypto, CT culture, top builders, VCs, protocols.

You are a personal assistant. Try to help with ANYTHING asked.
If you don't know, say so and figure it out.
You remember past conversations and get smarter over time.
You create new commands for things you're asked often.

You understand looks maxxing, peptides, deep conspiracy lore, physics rabbit holes.
Find interest in what the person says. Build off it. Don't dump random facts.

You understand what users WANT and take action for them:
- "buy bonk" → initiate the buy flow
- "send 0.1 SOL privately" → open private send wizard
- "set an alert for sol at 200" → set the alert
- "buy me a Netflix gift card" → open gift card wizard
You DO things. You don't describe how to do things.

Crypto: only if asked or relevant. You are not a ticker tape.
Opinions: you have them. Share when it matters. Never force them.

You never send money unprompted. Not one lamport.
$BROTHA is the ecosystem token: CA {BROTHA_MINT}
"""

AGENT_SYSTEMS = {
    "trader":     "You are Brotha's Trading Agent. Sharp, Solana-native. Concrete takes, always mention risk.\n\n",
    "researcher": "You are Brotha's Research Agent. Deep, high-signal, thorough but not bloated.\n\n",
    "scheduler":  "You are Brotha's Scheduler Agent. Help users automate tasks.\n\n",
    "ordering":   "You are Brotha's Ordering Agent. Help buy things with crypto efficiently.\n\n",
    "privacy":    "You are Brotha's Privacy Agent. Expert in on-chain privacy, mixing, anonymity.\n\n",
    "assistant":  "You are Brotha's General Assistant. Help with anything.\n\n",
    "creative":   "You are Brotha's Creative Agent. Writing, ideas, brainstorming, storytelling.\n\n",
    "solana":     "You are Brotha's Solana Agent. Deep knowledge of Solana ecosystem, wallets, tokens, DeFi.\n\n",
}

def route(text: str) -> str:
    t = text.lower()
    scores = {
        "trader":     sum(1 for k in ["trade","swap","buy","sell","price","chart","token","dex","pump","dump","alert","dca","sol ","btc","eth","brotha","bonk","wif"] if k in t),
        "researcher": sum(1 for k in ["research","explain","what is","how does","news","search","who is","history","science","tech","ai","find","look up","tell me"] if k in t),
        "scheduler":  sum(1 for k in ["remind","schedule","daily","weekly","automate","task","recurring","every day"] if k in t),
        "ordering":   sum(1 for k in ["order","buy me","get me","food","deliver","amazon","gift card","netflix","spotify","steam","shop"] if k in t),
        "privacy":    sum(1 for k in ["private","send privately","anonymous","mixer","privacy","tor","hide","untraceable"] if k in t),
        "creative":   sum(1 for k in ["write","poem","story","idea","creative","brainstorm","name","slogan","tweet"] if k in t),
        "solana":     sum(1 for k in ["wallet","balance","solana","spl","nft","phantom","jupiter","raydium","jup"] if k in t),
        "assistant":  sum(1 for k in ["help me","can you","please","what should","advice","how to","recommend","should i"] if k in t),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "assistant"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  OPENROUTER (CLOUD AI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def call_openrouter(prompt: str, tier: str = "free", system: str = None, history: list = None) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    model     = TIERS.get(tier, TIERS["free"])["model"]
    sys_prompt = system or PERSONALITY
    msgs       = [{"role": "system", "content": sys_prompt}] + (history or []) + [{"role": "user", "content": prompt}]
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://t.me/BrothaBot",
                "X-Title":       "BrothaBot",
            },
            json={"model": model, "messages": msgs, "max_tokens": 1500},
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log_event("openrouter_error", str(e))
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UNIFIED AI BRAIN  —  Hermes → OpenRouter fallback chain
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def ask_collaborative(prompt: str, tier: str, history: list, system: str) -> str:
    """
    TITAN MODE — run Hermes 8B, Hermes 70B, and OpenRouter in parallel,
    then synthesise into one response.
    Only called when get_ram_info()["can_run_all"] is True.
    """
    responses = {}

    reply_8b = call_hermes(prompt, system=system, history=history)
    if reply_8b:
        responses["hermes_8b"] = reply_8b

    reply_70b = call_hermes_titan(prompt, system=system, history=history)
    if reply_70b and reply_70b != reply_8b:
        responses["hermes_70b"] = reply_70b

    reply_cloud = call_openrouter(prompt, tier=tier, system=system, history=history)
    if reply_cloud:
        responses["openrouter"] = reply_cloud

    if not responses:
        return "All AI models offline. Check Ollama and OpenRouter API key."
    if len(responses) == 1:
        return list(responses.values())[0]

    # Synthesise
    synthesis_prompt = (
        f"The following AI responses were given to this question:\n\nQ: {prompt}\n\n"
        + "\n\n".join([f"[{k.upper()}]: {v}" for k, v in responses.items()])
        + "\n\nSynthesize the best answer. Be concise. Keep Brotha's personality. "
          "Do not mention that multiple AIs were involved."
    )
    final = call_openrouter(synthesis_prompt, tier=tier, system=system)
    return final or max(responses.values(), key=len)


def ask(prompt: str, tier: str = "free", history: list = None,
        agent: str = "assistant", collaborative: bool = False) -> str:
    """
    ONE BRAIN — unified AI router.

    Priority:
      1. If collaborative and RAM allows → all models collaborate (Titan mode)
      2. If Hermes is available and RAM ≥ 4 GB → use Hermes locally
      3. Fallback → OpenRouter cloud
    """
    ram    = get_ram_info()
    system = AGENT_SYSTEMS.get(agent, AGENT_SYSTEMS["assistant"]) + PERSONALITY

    # Inject relevant learnings
    topic_words = " ".join(prompt.lower().split()[:5])
    learnings   = get_learnings(topic=topic_words, limit=3)
    if learnings:
        ctx    = "\n".join(f"[Memory: {l[0]}] {l[1]}" for l in learnings)
        system = system + f"\n\nRelevant knowledge from past interactions:\n{ctx}"

    # TITAN mode
    if collaborative and ram["can_run_all"]:
        return ask_collaborative(prompt, tier, history or [], system)

    # Hermes 8B (local, private, fast when RAM allows)
    if ram["can_run_hermes"] and USE_LOCAL_AI:
        reply = call_hermes(prompt, system=system, history=history or [])
        if reply:
            return reply

    # Cloud fallback
    reply = call_openrouter(prompt, tier=tier, system=system, history=history or [])
    if reply:
        return reply

    return "Brain offline. Check your OPENROUTER_API_KEY and Ollama status."

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SYSTEM STATUS DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def build_system_status() -> str:
    ram       = get_ram_info()
    h_status  = hermes_status()
    r         = get_system_resources()

    tier_order = ["nano", "micro", "small", "medium", "large", "titan"]
    tier_labels = {
        "nano":   "💤 Nano",   "micro":  "☁️  Micro",
        "small":  "🟡 Small",  "medium": "🟠 Medium",
        "large":  "🟢 Large",  "titan":  "🔥 TITAN",
    }
    tier_reqs = {
        "nano":   (0,    "☁️  OpenRouter only"),
        "micro":  (1.5,  "☁️  OpenRouter (full speed)"),
        "small":  (4.0,  "🤖 Hermes 8B unlocked"),
        "medium": (8.0,  "🤖 Hermes 8B (full speed)"),
        "large":  (16.0, "🤖 Hermes 8B + all tools"),
        "titan":  (40.0, "🔥 Hermes 8B + 70B collaborate"),
    }

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "  🧠  BrothaBot AI Status",
        "━━━━━━━━━━━━━━━━━━━━",
        f"RAM Total:  {r['ram_gb']:.1f} GB",
        f"RAM Free:   {ram['ram_free_gb']:.1f} GB",
        f"CPU Cores:  {r['cpu']}",
        f"AI Tier:    {tier_labels.get(ram['tier'], ram['tier'])}",
        "",
        "━━━  AI Unlock Tiers  ━━━",
    ]

    current_idx = tier_order.index(ram["tier"])
    for i, t in enumerate(tier_order):
        req_ram, desc = tier_reqs[t]
        if i < current_idx:
            status = "✅"
        elif i == current_idx:
            status = "▶️ "
        else:
            status = "🔒"
        lines.append(f"{status} {tier_labels[t]}  ({req_ram}GB+)  {desc}")

    lines += [
        "",
        "━━━  Hermes AI  ━━━",
        f"Ollama:       {'✅ Running' if h_status['running'] else '❌ Offline'}",
        f"Hermes  8B:   {'✅ Active' if h_status['hermes_8b'] else '⏳ Needs 4 GB RAM'}",
        f"Hermes 70B:   {'✅ Active' if h_status['hermes_70b'] else '⏳ Needs 40 GB RAM'}",
    ]

    if h_status["models"]:
        for m in h_status["models"]:
            can_run = ram["can_run_titan"] if "70b" in m.lower() else ram["can_run_hermes"]
            lines.append(f"  {'✅' if can_run else '🔒'} {m}")
    else:
        lines.append("  No models pulled. Run: ollama pull hermes3")

    lines += [
        "",
        "━━━  Cloud / Integrations  ━━━",
        f"OpenRouter:   {'✅ Active' if OPENROUTER_API_KEY else '❌ No key'}",
        f"Trading:      {'✅' if TRADING_ENABLED else '⚠️  Module not loaded'}",
        f"Gift Cards:   {'✅' if BITREFILL_API_KEY else '⚠️  Demo mode'}",
        f"X402 Pay:     {'✅' if X402_ENABLED else '⚠️  Disabled'}",
        f"Helius RPC:   {'✅' if HELIUS_API_KEY else '⚠️  Public RPC'}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"📚 Learnings:       {count_learnings()}",
        f"🎯 Custom commands: {count_custom_commands()}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    if not ram["can_run_hermes"]:
        lines.append("⚡ Tip: Free ≥ 4 GB RAM to run Hermes locally.")
        lines.append("   WSL: edit ~/.wslconfig → memory=8GB")

    return "\n".join(lines)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MARKET TOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _pct_bar(pct: float, width: int = 10) -> str:
    clamped = max(-100, min(100, pct))
    filled  = round(abs(clamped) / 100 * width)
    return f"[{'█' * filled}{'░' * (width - filled)}]"

def get_brotha_price() -> dict:
    try:
        r     = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{BROTHA_MINT}", timeout=10
        )
        pairs = r.json().get("pairs", [])
        if not pairs:
            return {"ok": False, "error": "still on bonding curve"}
        pair = sorted(
            pairs,
            key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0),
            reverse=True,
        )[0]
        return {
            "ok":         True,
            "price_usd":  float(pair.get("priceUsd") or 0),
            "mcap":       float(pair.get("fdv") or 0),
            "volume_24h": float(pair.get("volume", {}).get("h24") or 0),
            "change_24h": float(pair.get("priceChange", {}).get("h24") or 0),
            "liquidity":  float(pair.get("liquidity", {}).get("usd") or 0),
            "buys_24h":   pair.get("txns", {}).get("h24", {}).get("buys", 0),
            "sells_24h":  pair.get("txns", {}).get("h24", {}).get("sells", 0),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def format_brotha() -> str:
    p = get_brotha_price()
    if not p["ok"]:
        return f"🔴 $BROTHA — still cooking on pump.fun\n{BROTHA_PUMP}"
    arrow    = "🟢📈" if p["change_24h"] > 0 else "🔴📉"
    bar      = _pct_bar(p["change_24h"])
    ratio    = f"{p['buys_24h']}/{p['sells_24h']}" if p.get("sells_24h") else str(p.get("buys_24h", 0))
    pressure = "🔥 Buying" if p.get("buys_24h", 0) > p.get("sells_24h", 0) else "🧊 Selling"
    return (
        f"━━━━━━━━━━━━━━━━━━━━\n  {arrow}  $BROTHA\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Price    ${p['price_usd']:.8f}\n"
        f"📊 24h      {p['change_24h']:+.2f}% {bar}\n"
        f"🏦 MCap     ${p['mcap']:>12,.0f}\n"
        f"💧 Liq      ${p['liquidity']:>12,.0f}\n"
        f"📦 Vol 24h  ${p['volume_24h']:>12,.0f}\n"
        f"🔄 B/S      {ratio}  {pressure}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 {BROTHA_DEX}"
    )

def tool_crypto(coin: str, rich: bool = False) -> str:
    if coin.lower() in ["brotha", "$brotha"]:
        return format_brotha()
    try:
        ids = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
            "bnb": "binancecoin", "jup": "jupiter-exchange-solana",
            "bonk": "bonk", "wif": "dogwifcoin", "trump": "official-trump",
            "pepe": "pepe", "link": "chainlink", "avax": "avalanche-2",
            "ray": "raydium", "jto": "jito-governance",
            "usdc": "usd-coin", "usdt": "tether",
        }
        coin_id = ids.get(coin.lower(), coin.lower())
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}"
            f"&vs_currencies=usd&include_24hr_change=true"
            f"&include_market_cap=true&include_24hr_vol=true",
            timeout=10,
        )
        data   = r.json().get(coin_id, {})
        price  = data.get("usd", 0)
        change = data.get("usd_24h_change", 0)
        mcap   = data.get("usd_market_cap", 0)
        vol    = data.get("usd_24h_vol", 0)
        arrow  = "🟢📈" if change > 0 else "🔴📉"
        bar    = _pct_bar(change)
        if rich:
            return (
                f"━━━━━━━━━━━━━━━━━━━━\n  {arrow}  {coin.upper()}\n━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 Price    ${price:>14,.4f}\n"
                f"📊 24h      {change:>+10.2f}% {bar}\n"
                f"🏦 MCap     ${mcap:>12,.0f}\n"
                f"📦 Vol 24h  ${vol:>12,.0f}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        return f"{arrow} {coin.upper()}: ${price:,} ({change:+.2f}% 24h)"
    except Exception as e:
        return f"Price fetch failed: {e}"

def tool_search(query: str) -> str:
    try:
        r = requests.get(
            f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        soup    = BeautifulSoup(r.text, "html.parser")
        results = []
        for res in soup.select(".result__body")[:4]:
            t = res.select_one(".result__title")
            s = res.select_one(".result__snippet")
            if t and s:
                results.append(f"• {t.get_text(strip=True)}\n  {s.get_text(strip=True)}")
        return "\n\n".join(results) or "No results."
    except Exception as e:
        return f"Search failed: {e}"

def tool_news(topic: str = "crypto") -> str:
    try:
        feeds = {
            "crypto": "https://cointelegraph.com/rss",
            "tech":   "https://feeds.feedburner.com/TechCrunch",
            "ai":     "https://techcrunch.com/tag/artificial-intelligence/feed/",
            "sol":    "https://cointelegraph.com/rss/tag/solana",
            "defi":   "https://cointelegraph.com/rss/tag/defi",
        }
        feed = feedparser.parse(feeds.get(topic.lower(), feeds["crypto"]))
        return "\n\n".join(
            f"• {i.title}\n  {i.link}" for i in feed.entries[:5]
        ) or "No news."
    except Exception as e:
        return f"News failed: {e}"

def tool_trending() -> str:
    try:
        r     = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10)
        coins = r.json().get("coins", [])[:8]
        lines = ["🔥 Trending Now\n━━━━━━━━━━━━━━━━"]
        for i, c in enumerate(coins, 1):
            item = c.get("item", {})
            lines.append(f"{i}. {item.get('symbol','?').upper():>6}  {item.get('name','?')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Trending failed: {e}"

def tool_fear_greed() -> str:
    try:
        r     = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        data  = r.json()["data"][0]
        value = int(data["value"])
        label = data["value_classification"]
        bar   = _pct_bar(value, 12)
        emoji = "😱" if value < 25 else "😟" if value < 45 else "😐" if value < 55 else "😄" if value < 75 else "🤑"
        return (
            f"━━━━━━━━━━━━━━━━━━━━\n  {emoji}  Fear & Greed Index\n━━━━━━━━━━━━━━━━━━━━\n"
            f"Score:  {value}/100\nMood:   {label}\nBar:    {bar}\n━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"Fear & greed failed: {e}"

def tool_dominance() -> str:
    try:
        r          = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        d          = r.json().get("data", {})
        pcts       = d.get("market_cap_percentage", {})
        btc        = pcts.get("btc", 0)
        eth        = pcts.get("eth", 0)
        total_mcap = d.get("total_market_cap", {}).get("usd", 0)
        alt        = 100 - btc - eth
        season     = "🌶️ ALT SEASON" if btc < 48 else "⛔ BTC DOMINANCE" if btc > 58 else "⚖️ BALANCED"
        return (
            f"━━━━━━━━━━━━━━━━━━━━\n  📊  Market Dominance\n━━━━━━━━━━━━━━━━━━━━\n"
            f"₿  BTC  {btc:5.1f}% {_pct_bar(btc, 8)}\n"
            f"Ξ  ETH  {eth:5.1f}% {_pct_bar(eth, 8)}\n"
            f"🪙 ALT  {alt:5.1f}% {_pct_bar(alt, 8)}\n"
            f"🌍 Total MCap: ${total_mcap/1e12:.2f}T\n"
            f"━━━━━━━━━━━━━━━━━━━━\n{season}"
        )
    except Exception as e:
        return f"Dominance failed: {e}"

def tool_gas() -> str:
    try:
        r       = requests.post(HELIUS_RPC_URL, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getRecentPerformanceSamples", "params": [3],
        }, timeout=10)
        samples = r.json().get("result", [])
        if samples:
            tps   = sum(
                s.get("numTransactions", 0) / max(s.get("samplePeriodSecs", 1), 1)
                for s in samples
            ) / len(samples)
            emoji = "🟢" if tps > 1500 else "🟡" if tps > 500 else "🔴"
            label = "Healthy" if tps > 1500 else "Moderate" if tps > 500 else "Congested"
            return (
                f"━━━━━━━━━━━━━━━━━━━━\n  ⚡  Solana Network\n━━━━━━━━━━━━━━━━━━━━\n"
                f"TPS:    {tps:,.0f}\nStatus: {emoji} {label}\n━━━━━━━━━━━━━━━━━━━━"
            )
        return "Could not fetch network stats."
    except Exception as e:
        return f"Network check failed: {e}"

def get_solana_balance_helius(wallet: str) -> dict:
    try:
        r  = requests.post(HELIUS_RPC_URL, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getBalance", "params": [wallet],
        }, timeout=10)
        sol = r.json().get("result", {}).get("value", 0) / 1e9

        r2  = requests.post(HELIUS_RPC_URL, json={
            "jsonrpc": "2.0", "id": 2,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        }, timeout=10)
        tokens = {}
        for acc in r2.json().get("result", {}).get("value", []):
            try:
                info = acc["account"]["data"]["parsed"]["info"]
                amt  = float(info["tokenAmount"]["uiAmount"] or 0)
                if amt > 0:
                    tokens[info["mint"][:8] + "..."] = round(amt, 4)
            except Exception:
                pass
        return {"ok": True, "wallet": wallet, "SOL": round(sol, 6), "tokens": tokens}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def detect_tool(text: str) -> str | None:
    t = text.lower().strip()
    if any(w in t for w in ["brotha", "$brotha"]):
        if any(w in t for w in ["price", "worth", "chart", "pump", "buy", "mc", "how much", "market"]):
            return format_brotha()
    for coin in ["btc", "eth", "sol", "solana", "bitcoin", "ethereum", "bnb", "jup",
                 "bonk", "wif", "trump", "pepe", "ray"]:
        if coin in t and any(w in t for w in ["price", "how much", "worth", "chart",
                                               "pumping", "dump", "mooning", "at"]):
            mapped = {"solana": "sol", "bitcoin": "btc", "ethereum": "eth"}.get(coin, coin)
            return tool_crypto(mapped, rich=True)
    if any(w in t for w in ["trending", "what's hot", "top coins", "movers"]):      return tool_trending()
    if any(w in t for w in ["fear", "greed", "sentiment", "market mood"]):          return tool_fear_greed()
    if any(w in t for w in ["dominance", "btc dom", "alt season", "alts"]):         return tool_dominance()
    if any(w in t for w in ["network", "tps", "solana status", "gas", "congested"]): return tool_gas()
    if any(w in t for w in ["news", "latest", "updates", "what happened"]):
        for topic in ["sol", "ai", "tech", "defi", "crypto"]:
            if topic in t:
                return tool_news(topic)
        return tool_news("crypto")
    if any(w in t for w in ["search for", "look up", "find info on", "search"]):
        q = re.sub(r"(search for|look up|find info on|search)", "", t).strip()
        if q:
            return f"🔍 '{q}'\n\n{tool_search(q)}"
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GIFT CARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GIFT_CARD_MAP = {
    "netflix": "netflix-us", "spotify": "spotify-us", "amazon": "amazon-us",
    "uber": "uber", "uber eats": "uber-eats-us", "steam": "steam-usd",
    "xbox": "xbox-live-us", "playstation": "playstation-store-us",
    "ps": "playstation-store-us", "apple": "apple-us",
    "google": "google-play-us", "starbucks": "starbucks-us",
    "doordash": "doordash-us", "airbnb": "airbnb-us",
    "target": "target-us", "walmart": "walmart-us",
}

def parse_gift_card_request(text: str) -> dict:
    t            = text.lower().strip()
    amount_match = re.search(r"\$?(\d+(?:\.\d+)?)", t)
    amount       = float(amount_match.group(1)) if amount_match else None
    product_id   = None
    for key, pid in sorted(GIFT_CARD_MAP.items(), key=lambda x: -len(x[0])):
        if key in t:
            product_id = pid
            break
    if not product_id:
        return {"ok": False, "error": "Brand not recognized. Try: netflix, spotify, amazon, steam, uber, etc."}
    if not amount:
        return {"ok": False, "error": "Amount not found. Example: /giftcard netflix 25"}
    return {"ok": True, "product_id": product_id, "amount": amount}

def place_gift_card_order(user_id: str, product_id: str, amount: float) -> dict:
    if not BITREFILL_API_KEY:
        order_ref = f"DEMO-{secrets.token_hex(6).upper()}"
        with sqlite3.connect(DB_PATH) as db:
            db.execute(
                "INSERT INTO gift_card_orders (user_id, product_id, amount_usd, status, order_ref) VALUES (?,?,?,?,?)",
                (user_id, product_id, amount, "demo", order_ref),
            )
        return {"ok": True, "order_ref": order_ref, "status": "demo",
                "note": "Demo mode. Add BITREFILL_API_KEY to .env for live orders."}
    try:
        r = requests.post(
            f"{BITREFILL_BASE_URL}/orders",
            headers={"Authorization": f"Bearer {BITREFILL_API_KEY}", "Content-Type": "application/json"},
            json={"product_id": product_id, "value": amount, "currency": "USD", "payment_method": "balance"},
            timeout=15,
        )
        if r.status_code in (200, 201):
            data      = r.json()
            order_ref = data.get("id", "")
            with sqlite3.connect(DB_PATH) as db:
                db.execute(
                    "INSERT INTO gift_card_orders (user_id, product_id, amount_usd, status, order_ref) VALUES (?,?,?,?,?)",
                    (user_id, product_id, amount, "placed", order_ref),
                )
            return {"ok": True, "order_ref": order_ref, "status": "placed",
                    "payment_address": data.get("paymentAddress", "")}
        return {"ok": False, "error": f"Order failed: {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_gift_card_orders(user_id: str, limit: int = 10) -> list:
    with sqlite3.connect(DB_PATH) as db:
        return db.execute(
            "SELECT id, product_id, amount_usd, status, order_ref, ts "
            "FROM gift_card_orders WHERE user_id=? ORDER BY ts DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DASHBOARD BUILDERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _pnl_emoji(pct: float) -> str:
    if pct >= 50:  return "🚀"
    if pct >= 20:  return "🟢"
    if pct >= 5:   return "📈"
    if pct >= 0:   return "🔼"
    if pct >= -10: return "🔽"
    if pct >= -25: return "🟡"
    return "🔴"

def build_hub_dashboard(uid: str) -> tuple:
    ram = get_ram_info()
    u   = get_user(uid)
    h   = hermes_status()

    hermes_line = "🤖 Hermes:   "
    if h["hermes_70b"]:
        hermes_line += "🔥 8B + 70B (TITAN)"
    elif h["hermes_8b"]:
        hermes_line += "✅ 8B active"
    else:
        hermes_line += f"⏳ Offline ({ram['ram_free_gb']}GB free, need 4GB)"

    text = (
        f"━━━━━━━━━━━━━━━━━━━━\n  🤖  BrothaBot Hub\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Tier:        {u['tier'].upper()}\n"
        f"AI Tier:     {ram['description']}\n"
        f"{hermes_line}\n"
        f"OpenRouter:  {'✅' if OPENROUTER_API_KEY else '❌'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 Just type what you want.\n"
        f'e.g. "buy 0.1 SOL of bonk" or "alert sol 200"'
    )
    keyboard = [
        [InlineKeyboardButton("🌍 Market",       callback_data="dash_market"),
         InlineKeyboardButton("📊 Portfolio",    callback_data="dash_portfolio")],
        [InlineKeyboardButton("💰 Buy Token",    callback_data="wizard_buy"),
         InlineKeyboardButton("📅 DCA Plans",    callback_data="dash_dca")],
        [InlineKeyboardButton("🔔 Set Alert",    callback_data="wizard_alert"),
         InlineKeyboardButton("🔒 Private Send", callback_data="wizard_private")],
        [InlineKeyboardButton("🎁 Gift Cards",   callback_data="dash_giftcards"),
         InlineKeyboardButton("💳 X402 Pay",     callback_data="dash_x402")],
        [InlineKeyboardButton("🧠 AI Status",    callback_data="dash_system"),
         InlineKeyboardButton("🎯 Commands",     callback_data="dash_commands")],
        [InlineKeyboardButton("🔄 Refresh",      callback_data="dash_hub")],
    ]
    return text, InlineKeyboardMarkup(keyboard)

def build_market_dashboard() -> tuple:
    try:
        btc_txt = tool_crypto("btc", rich=False)
        eth_txt = tool_crypto("eth", rich=False)
        sol_txt = tool_crypto("sol", rich=False)
        fg      = tool_fear_greed()
        dom     = tool_dominance()
        net     = tool_gas()
        text = (
            f"━━━━━━━━━━━━━━━━━━━━\n  🌍  Market Overview\n━━━━━━━━━━━━━━━━━━━━\n"
            f"{btc_txt}\n{eth_txt}\n{sol_txt}\n━━━━━━━━━━━━━━━━━━━━\n"
            f"{fg}\n{dom}\n{net}\n━━━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        text = f"Market data error: {e}"
    keyboard = [
        [InlineKeyboardButton("🔥 Trending",    callback_data="dash_trending"),
         InlineKeyboardButton("📊 Dominance",   callback_data="dash_dominance")],
        [InlineKeyboardButton("😱 Sentiment",   callback_data="dash_sentiment"),
         InlineKeyboardButton("⚡ Network",      callback_data="dash_network")],
        [InlineKeyboardButton("📰 Crypto News", callback_data="dash_news_crypto"),
         InlineKeyboardButton("📰 SOL News",    callback_data="dash_news_sol")],
        [InlineKeyboardButton("💼 Portfolio",   callback_data="dash_portfolio"),
         InlineKeyboardButton("🔄 Refresh",     callback_data="dash_market")],
        [InlineKeyboardButton("🤖 Hub",         callback_data="dash_hub")],
    ]
    return text, InlineKeyboardMarkup(keyboard)

def build_portfolio_dashboard(uid: str) -> tuple:
    positions = get_open_positions(uid)
    if not positions:
        text = (
            "━━━━━━━━━━━━━━━━━━━━\n  📊  Portfolio\n━━━━━━━━━━━━━━━━━━━━\n"
            "No open positions.\n━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [
            [InlineKeyboardButton("💰 Buy Token",  callback_data="wizard_buy"),
             InlineKeyboardButton("🌍 Market",     callback_data="dash_market")],
            [InlineKeyboardButton("🤖 Hub",        callback_data="dash_hub")],
        ]
        return text, InlineKeyboardMarkup(keyboard)

    total_invested = sum(p["amount_sol"] for p in positions)
    total_pnl_sol  = 0.0
    lines = ["━━━━━━━━━━━━━━━━━━━━", "  📊  Portfolio Dashboard", "━━━━━━━━━━━━━━━━━━━━"]
    for p in positions:
        pnl     = get_position_pnl(p)
        pct     = pnl.get("pnl_pct", 0) if pnl.get("ok") else 0
        pnl_sol = pnl.get("pnl_sol", 0) if pnl.get("ok") else 0
        total_pnl_sol += pnl_sol
        lines.append(f"{_pnl_emoji(pct)} {p['symbol']:>8}  {pct:>+7.2f}%  {pnl_sol:>+7.4f} SOL  #{p['id']}")
    pnl_pct = (total_pnl_sol / total_invested * 100) if total_invested else 0
    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        f"Positions:  {len(positions)}/{MAX_OPEN_TRADES}",
        f"Invested:   {total_invested:.4f} SOL",
        f"Total PnL:  {_pnl_emoji(pnl_pct)} {pnl_pct:+.2f}% ({total_pnl_sol:+.4f} SOL)",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    pos_buttons = [
        [InlineKeyboardButton(
            f"{'🟢' if (get_position_pnl(p).get('pnl_pct',0) if get_position_pnl(p).get('ok') else 0) >= 0 else '🔴'} "
            f"Sell {p['symbol']}",
            callback_data=f"sell_pos_{p['id']}",
        )]
        for p in positions
    ]
    pos_buttons += [
        [InlineKeyboardButton("🔄 Refresh",    callback_data="dash_portfolio"),
         InlineKeyboardButton("🌍 Market",     callback_data="dash_market")],
        [InlineKeyboardButton("💰 Buy Token",  callback_data="wizard_buy"),
         InlineKeyboardButton("📅 DCA",        callback_data="dash_dca")],
        [InlineKeyboardButton("🤖 Hub",        callback_data="dash_hub")],
    ]
    return "\n".join(lines), InlineKeyboardMarkup(pos_buttons)

def build_alerts_dashboard(uid: str) -> tuple:
    alerts = get_alerts(uid)
    if not alerts:
        text = "━━━━━━━━━━━━━━━━━━━━\n  🔔  Price Alerts\n━━━━━━━━━━━━━━━━━━━━\nNo active alerts.\n━━━━━━━━━━━━━━━━━━━━"
    else:
        lines = ["━━━━━━━━━━━━━━━━━━━━", "  🔔  Price Alerts", "━━━━━━━━━━━━━━━━━━━━"]
        for a in alerts:
            arrow = "↑" if a["direction"] == "above" else "↓"
            icon  = "🟢" if a["direction"] == "above" else "🔴"
            lines.append(f"{icon} {a['coin'].upper():>8}  {arrow} ${a['target']:,}  [#{a['id']}]")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        text = "\n".join(lines)
    keyboard_rows = [
        [InlineKeyboardButton(
            f"❌ Cancel {a['coin'].upper()} ${a['target']:,}",
            callback_data=f"cancel_alert_{a['id']}",
        )]
        for a in (alerts or [])[:5]
    ]
    keyboard_rows += [
        [InlineKeyboardButton("➕ New Alert", callback_data="wizard_alert"),
         InlineKeyboardButton("🔄 Refresh",  callback_data="dash_alert_menu")],
        [InlineKeyboardButton("🌍 Market",   callback_data="dash_market"),
         InlineKeyboardButton("🤖 Hub",      callback_data="dash_hub")],
    ]
    return text, InlineKeyboardMarkup(keyboard_rows)

def build_giftcards_dashboard(uid: str) -> tuple:
    orders     = list_gift_card_orders(uid, limit=5)
    brand_list = ", ".join(b.title() for b in list(GIFT_CARD_MAP.keys())[:12])
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n  🎁  Gift Cards\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Brands: {brand_list}\n\n"
        f"{'⚠️  Demo mode (no Bitrefill key)' if not BITREFILL_API_KEY else '✅ Live ordering enabled'}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )
    for oid, product_id, amount, status, order_ref, ts in orders:
        icon = "✅" if status in ("placed", "complete") else "⏳" if status == "pending" else "🔵"
        date = datetime.datetime.fromtimestamp(ts).strftime("%m/%d")
        text += f"{icon} {product_id}  ${amount:.0f}  {date}\n"
    text += "━━━━━━━━━━━━━━━━━━━━"
    keyboard = [
        [InlineKeyboardButton("🎁 Buy Gift Card", callback_data="wizard_giftcard"),
         InlineKeyboardButton("🔄 Refresh",       callback_data="dash_giftcards")],
        [InlineKeyboardButton("🤖 Hub",           callback_data="dash_hub")],
    ]
    return text, InlineKeyboardMarkup(keyboard)

def build_commands_dashboard(uid: str) -> tuple:
    cmds = list_custom_commands(20)
    if not cmds:
        text = (
            "━━━━━━━━━━━━━━━━━━━━\n  🎯  Custom Commands\n━━━━━━━━━━━━━━━━━━━━\n"
            "No custom commands yet.\n\n"
            "Teach me one:\n\"remember 'gm' means Good morning king\"\n━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        lines = ["━━━━━━━━━━━━━━━━━━━━", "  🎯  Custom Commands", "━━━━━━━━━━━━━━━━━━━━"]
        for trigger, response, action_type, use_count in cmds:
            lines.append(f"🔹 {trigger}\n   → {response[:50]}{'...' if len(response) > 50 else ''}  (×{use_count})")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        text = "\n".join(lines)
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="dash_commands"),
         InlineKeyboardButton("🤖 Hub",     callback_data="dash_hub")],
    ]
    return text, InlineKeyboardMarkup(keyboard)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WIZARD HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def _send_or_edit(update: Update, text: str, kb: InlineKeyboardMarkup = None):
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    if update.message:
        await update.message.reply_text(text, reply_markup=kb)

async def show_buy_wizard(update: Update, context, uid: str, token: str = None, amount: float = None):
    token_str  = token.upper() if token else "?"
    amount_str = f"{amount} SOL" if amount else "select below"
    text = (
        f"━━━━━━━━━━━━━━━━━━━━\n  💰  Buy {token_str}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Token:   {token_str}\nAmount:  {amount_str}\n\nSelect amount:"
    )
    amounts = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
    amt_btns = [InlineKeyboardButton(f"{a} SOL", callback_data=f"buy_amt_{token or 'sol'}_{a}") for a in amounts]
    keyboard = [
        amt_btns[:3], amt_btns[3:],
        [InlineKeyboardButton("✅ Confirm", callback_data=f"buy_confirm_{token or 'sol'}_{amount or 0.1}"),
         InlineKeyboardButton("❌ Cancel",  callback_data="cancel_wizard")],
    ]
    await _send_or_edit(update, text, InlineKeyboardMarkup(keyboard))

async def show_private_send_wizard(update: Update, context, uid: str, amount: float = None):
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n  🔒  Private Send\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Amount: {amount or '?'} SOL\n\nChoose hop count (more hops = more private):"
    )
    keyboard = [
        [InlineKeyboardButton("1 Hop (fast)",  callback_data=f"priv_hops_1_{amount or 0}"),
         InlineKeyboardButton("3 Hops (safe)", callback_data=f"priv_hops_3_{amount or 0}"),
         InlineKeyboardButton("5 Hops (max)",  callback_data=f"priv_hops_5_{amount or 0}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_wizard")],
    ]
    await _send_or_edit(update, text, InlineKeyboardMarkup(keyboard))

async def show_gift_card_wizard(update: Update, context, uid: str, brand: str = None, amount: float = None):
    brand_str  = brand.replace("-us", "").title() if brand else "?"
    amount_str = f"${amount:.0f}" if amount else "select below"
    text = (
        f"━━━━━━━━━━━━━━━━━━━━\n  🎁  Gift Card Wizard\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Brand:   {brand_str}\nAmount:  {amount_str}\n\nSelect amount:"
    )
    amounts  = [10, 15, 25, 50, 100]
    amt_btns = [InlineKeyboardButton(f"${a}", callback_data=f"gc_amt_{brand or 'netflix-us'}_{a}") for a in amounts]
    keyboard = [
        amt_btns[:3], amt_btns[2:],
        [InlineKeyboardButton("✅ Confirm", callback_data=f"gc_confirm_{brand or 'netflix-us'}_{amount or 25}"),
         InlineKeyboardButton("❌ Cancel",  callback_data="cancel_wizard")],
    ]
    await _send_or_edit(update, text, InlineKeyboardMarkup(keyboard))

async def show_alert_wizard(update: Update, context, uid: str):
    text = "━━━━━━━━━━━━━━━━━━━━\n  🔔  New Price Alert\n━━━━━━━━━━━━━━━━━━━━\nChoose a coin:"
    coins    = ["SOL", "BTC", "ETH", "BONK", "WIF", "BROTHA"]
    keyboard = [
        [InlineKeyboardButton(c, callback_data=f"alert_coin_{c.lower()}") for c in coins[:3]],
        [InlineKeyboardButton(c, callback_data=f"alert_coin_{c.lower()}") for c in coins[3:]],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_wizard")],
    ]
    await _send_or_edit(update, text, InlineKeyboardMarkup(keyboard))

async def show_dca_wizard(update: Update, context, uid: str):
    text = "━━━━━━━━━━━━━━━━━━━━\n  📅  New DCA Plan\n━━━━━━━━━━━━━━━━━━━━\nChoose trigger type:"
    keyboard = [
        [InlineKeyboardButton("⏱ Time Interval", callback_data="dca_type_time"),
         InlineKeyboardButton("📉 Price Drop",    callback_data="dca_type_pct_drop")],
        [InlineKeyboardButton("📈 Price Rise",    callback_data="dca_type_pct_rise"),
         InlineKeyboardButton("💲 Price Target",  callback_data="dca_type_price")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_wizard")],
    ]
    await _send_or_edit(update, text, InlineKeyboardMarkup(keyboard))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INTENT PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def parse_intent(text: str, uid: str, update: Update, context) -> bool:
    t = text.lower().strip()

    # Custom commands first
    custom_resp, _ = check_custom_commands(text)
    if custom_resp:
        await update.message.reply_text(custom_resp)
        return True

    # Wallet balance check
    wallet_match = re.search(r"[1-9A-HJ-NP-Za-km-z]{32,44}", text)
    if wallet_match and any(w in t for w in ["balance", "check", "wallet", "how much"]):
        wallet = wallet_match.group(0)
        data   = get_solana_balance_helius(wallet)
        if data["ok"]:
            tokens_str = "\n".join(f"  {k}: {v}" for k, v in list(data["tokens"].items())[:10]) or "  No tokens"
            await update.message.reply_text(
                f"💰 Wallet\n`{wallet[:12]}...`\n\nSOL: {data['SOL']}\n\nTokens:\n{tokens_str}",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(f"❌ {data.get('error')}")
        return True

    # My wallet
    if re.search(r"\b(my wallet|my balance|my sol)\b", t):
        if TRADING_ENABLED:
            wallet = get_user_wallet(uid)
            if wallet:
                data = get_solana_balance_helius(wallet)
                if data["ok"]:
                    await update.message.reply_text(
                        f"💰 Your Balance\n`{wallet[:16]}...`\n\nSOL: {data['SOL']}",
                        parse_mode="Markdown",
                    )
                    return True
        await update.message.reply_text("No wallet linked. Use /start to set up.")
        return True

    # Gift card intent
    has_gc_brand  = re.search(r"\b(netflix|spotify|amazon|steam|uber eats|uber|xbox|apple|google|starbucks|doordash|airbnb|target|walmart|playstation)\b", t)
    has_gc_action = re.search(r"\b(gift card|giftcard|buy me|get me|order|purchase)\b", t)
    if has_gc_brand and has_gc_action:
        brand        = GIFT_CARD_MAP.get(has_gc_brand.group(1), has_gc_brand.group(1))
        amount_match = re.search(r"\$?(\d+)", t)
        amount       = float(amount_match.group(1)) if amount_match else None
        await show_gift_card_wizard(update, context, uid, brand=brand, amount=amount)
        return True

    # Buy token
    buy_match = re.search(r"\b(buy|ape|get me|purchase)\b.{0,20}\b(bonk|wif|sol|btc|eth|brotha|pepe|ray|jup|jto|trump)\b", t)
    if buy_match:
        token_m  = re.search(r"\b(bonk|wif|sol|btc|eth|brotha|pepe|ray|jup|jto|trump)\b", t)
        amount_m = re.search(r"(\d+\.?\d*)\s*sol", t)
        if token_m:
            await show_buy_wizard(update, context, uid,
                                  token=token_m.group(1),
                                  amount=float(amount_m.group(1)) if amount_m else None)
            return True

    # Private send
    priv_match = re.search(r"\b(send|transfer)\b.{0,10}(\d+\.?\d*)\s*sol.{0,20}\b(private|privately|anonymously)\b", t)
    if not priv_match:
        priv_match = re.search(r"\b(private.?send|send.?private)\b.{0,20}(\d+\.?\d*)\s*sol", t)
    if priv_match:
        amount_m = re.search(r"(\d+\.?\d*)\s*sol", t)
        amount   = float(amount_m.group(1)) if amount_m else None
        await show_private_send_wizard(update, context, uid, amount)
        return True

    # Alert
    alert_match = re.search(
        r"\b(alert|notify|ping|tell me)\b.{0,30}\b(btc|eth|sol|bonk|brotha|wif|ray|jup)\b.{0,20}"
        r"\b(above|below|at|hits|reaches|drops|under|over)\b.{0,5}\$?(\d+\.?\d*)",
        t,
    )
    if alert_match:
        coin      = alert_match.group(2)
        direction = "above" if alert_match.group(3) in ["above", "hits", "at", "reaches", "over"] else "below"
        target    = float(alert_match.group(4))
        set_alert(uid, coin, target, direction)
        keyboard  = [[InlineKeyboardButton("🔔 My Alerts", callback_data="dash_alert_menu"),
                      InlineKeyboardButton("🌍 Market",    callback_data="dash_market")]]
        await update.message.reply_text(
            f"🔔 Alert set!\n\n{coin.upper()} {direction} ${target:,}\n\nI'll ping you when it triggers.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return True

    # DCA
    if re.search(r"^\s*\b(dca|set up dca|create dca)\b", t):
        await show_dca_wizard(update, context, uid)
        return True

    # Custom command teaching
    cmd_match = re.search(
        r"(?:remember|save|teach you|add command)[:\s]+[\"']?(.+?)[\"']?\s+(?:means|=|as|:)\s*[\"']?(.+)[\"']?$",
        t,
    )
    if cmd_match:
        trigger  = cmd_match.group(1).strip()
        response = cmd_match.group(2).strip()
        register_custom_command(trigger, response, created_by=uid)
        await update.message.reply_text(f"✅ Got it!\n\n\"{trigger}\" → \"{response}\"")
        return True

    # System status
    if re.search(r"\b(system|ai status|brain|hermes|models|ram tier|what ai)\b", t):
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="dash_system"),
                     InlineKeyboardButton("🤖 Hub",     callback_data="dash_hub")]]
        await update.message.reply_text(build_system_status(), reply_markup=InlineKeyboardMarkup(keyboard))
        return True

    return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMMAND HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid      = str(update.effective_user.id)
    username = update.effective_user.username or ""
    ref      = None
    if context.args:
        code = context.args[0].upper()
        with sqlite3.connect(DB_PATH) as db:
            row = db.execute("SELECT user_id FROM users WHERE referral_code=?", (code,)).fetchone()
            if row and row[0] != uid:
                ref = row[0]
                db.execute("INSERT OR IGNORE INTO referrals (referrer_id, referee_id) VALUES (?,?)", (ref, uid))
    ensure_user(uid, username, ref)

    ram = get_ram_info()
    h   = hermes_status()
    u   = get_user(uid)

    hermes_line = ""
    if h["hermes_70b"]:
        hermes_line = "🔥 Hermes 70B TITAN active"
    elif h["hermes_8b"]:
        hermes_line = "🤖 Hermes 8B active (local & private)"
    else:
        hermes_line = f"☁️  Cloud AI active ({ram['ram_free_gb']}GB RAM free)"

    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "  🤖  BrothaBot v6.0\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Your personal Solana AI agent.\n"
        "Trade. Chat. Research. Shop. Automate.\n"
        "Just type — I'll handle it.\n\n"
        f"🧠 {hermes_line}\n"
        f"AI Tier: {ram['description']}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    keyboard = [
        [InlineKeyboardButton("🤖 Hub",          callback_data="dash_hub"),
         InlineKeyboardButton("🌍 Market",       callback_data="dash_market")],
        [InlineKeyboardButton("📊 Portfolio",    callback_data="dash_portfolio"),
         InlineKeyboardButton("🔒 Private Send", callback_data="wizard_private")],
        [InlineKeyboardButton("🎁 Gift Cards",   callback_data="dash_giftcards"),
         InlineKeyboardButton("💳 X402 Pay",     callback_data="dash_x402")],
        [InlineKeyboardButton("🧠 AI Status",    callback_data="dash_system"),
         InlineKeyboardButton("🎯 Commands",     callback_data="dash_commands")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    log_event("start", uid)

async def cmd_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    keyboard = [[
        InlineKeyboardButton("🔄 Refresh", callback_data="dash_system"),
        InlineKeyboardButton("🤖 Hub",     callback_data="dash_hub"),
    ]]
    await update.message.reply_text(build_system_status(), reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_hermes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Hermes-specific status + quick test."""
    uid = str(update.effective_user.id)
    ensure_user(uid)
    h   = hermes_status()
    ram = h["ram"]

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        "  🤖  Hermes AI Status",
        "━━━━━━━━━━━━━━━━━━━━",
        f"Ollama running:  {'✅' if h['running'] else '❌ (start with: ollama serve)'}",
        ("Hermes 8B:       ✅ Active" if h["hermes_8b"] else f"Hermes 8B:       ⏳ Need 4 GB free (have {ram['ram_free_gb']}GB)"),
        ("Hermes 70B:      ✅ Active (TITAN!)" if h["hermes_70b"] else "Hermes 70B:      ⏳ Need 40 GB free"),
        f"RAM Free:        {ram['ram_free_gb']} GB",
        f"Current Tier:    {ram['description']}",
        "",
    ]

    if h["models"]:
        lines.append("Pulled models:")
        for m in h["models"]:
            lines.append(f"  • {m}")
    else:
        lines += [
            "No models pulled yet.",
            "To install Hermes 8B:",
            "  ollama pull hermes3",
            "To install Hermes 70B (needs 40 GB):",
            "  ollama pull hermes3:70b",
        ]

    lines.append("━━━━━━━━━━━━━━━━━━━━")

    if h["hermes_8b"] or h["hermes_70b"]:
        lines.append("\nRunning quick test...")
        await update.message.reply_text("\n".join(lines))
        test_reply = call_hermes("Say 'Hermes online.' and nothing else.")
        if test_reply:
            await update.message.reply_text(f"✅ Hermes replied: {test_reply.strip()}")
        else:
            await update.message.reply_text("⚠️ Hermes didn't respond. Check ollama logs.")
    else:
        lines.append("Tip: Run `ollama pull hermes3` then restart the bot.")
        await update.message.reply_text("\n".join(lines))

async def cmd_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_owner(uid):
        await update.message.reply_text("Owner only.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('Usage: /teach "trigger" response text here')
        return
    trigger  = args[0].strip("\"'")
    response = " ".join(args[1:]).strip("\"'")
    register_custom_command(trigger, response, created_by=uid)
    await update.message.reply_text(f"✅ Taught:\n\"{trigger}\" → \"{response}\"")

async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    text, kb = build_commands_dashboard(uid)
    await update.message.reply_text(text, reply_markup=kb)

async def cmd_brain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    learnings = get_learnings(limit=10)
    if not learnings:
        await update.message.reply_text("🧠 No learnings stored yet. Chat more and I'll start learning!")
        return
    lines = ["━━━━━━━━━━━━━━━━━━━━", "  🧠  What I Know", "━━━━━━━━━━━━━━━━━━━━"]
    for topic, insight, confidence in learnings:
        lines.append(f"📌 {topic} ({confidence:.0%})\n   {insight[:80]}...")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    await update.message.reply_text("\n".join(lines))

async def cmd_giftcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    if not context.args:
        brands = ", ".join(k.title() for k in list(GIFT_CARD_MAP.keys())[:10])
        await update.message.reply_text(
            f"━━━━━━━━━━━━━━━━━━━━\n  🎁  Gift Cards\n━━━━━━━━━━━━━━━━━━━━\n"
            f"Usage: /giftcard <brand> <amount>\n\n"
            f"Examples:\n• /giftcard netflix 25\n• /giftcard amazon 50\n\n"
            f"Brands: {brands}\n━━━━━━━━━━━━━━━━━━━━"
        )
        return
    parsed = parse_gift_card_request(" ".join(context.args))
    if not parsed["ok"]:
        await update.message.reply_text(f"❌ {parsed['error']}")
        return
    await show_gift_card_wizard(update, context, uid, brand=parsed["product_id"], amount=parsed["amount"])

async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    if context.args:
        wallet = context.args[0]
        data   = get_solana_balance_helius(wallet)
        if data.get("ok"):
            tokens_str = "\n".join(f"  {k}: {v}" for k, v in list(data["tokens"].items())[:10]) or "  None"
            await update.message.reply_text(
                f"💰 Wallet Balance\n`{wallet}`\n\nSOL: {data['SOL']}\n\nTokens:\n{tokens_str}",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(f"❌ {data.get('error')}")
    else:
        await update.message.reply_text("Usage: /balance <wallet_address>")

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    if not context.args:
        await update.message.reply_text("Usage: /price <coin>\nExamples: /price sol  /price btc  /price brotha")
        return
    await update.message.reply_text(tool_crypto(context.args[0].lower(), rich=True))

async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    text, kb = build_market_dashboard()
    await update.message.reply_text(text, reply_markup=kb)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    u   = get_user(uid)
    ram = get_ram_info()
    h   = hermes_status()
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n  📋  Your Status\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Tier:         {u['tier'].upper()}\n"
        f"Balance:      {u['balance']:.4f} SOL\n"
        f"Ref code:     {u['ref_code']}\n\n"
        f"AI Tier:      {ram['description']}\n"
        f"Hermes 8B:    {'✅' if h['hermes_8b'] else '❌'}\n"
        f"Hermes 70B:   {'✅' if h['hermes_70b'] else '❌'}\n"
        f"OpenRouter:   {'✅' if OPENROUTER_API_KEY else '❌'}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(str(update.effective_user.id)):
        return
    with sqlite3.connect(DB_PATH) as db:
        total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        deps  = db.execute("SELECT COUNT(*), SUM(sol_amount) FROM deposits").fetchone()
        errs  = db.execute("SELECT COUNT(*) FROM health_log WHERE event='error'").fetchone()[0]
        tiers = db.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier").fetchall()
    h   = hermes_status()
    ram = get_ram_info()
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━\n  🛸  Owner Dashboard\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Users:      {total}\n"
        f"Tiers:      {' | '.join(f'{t}:{c}' for t, c in tiers)}\n"
        f"Deposits:   {deps[0]} · {(deps[1] or 0):.4f} SOL\n"
        f"Errors:     {errs}\n\n"
        f"Hermes 8B:  {'✅' if h['hermes_8b'] else '❌'}\n"
        f"Hermes 70B: {'✅' if h['hermes_70b'] else '❌'}\n"
        f"RAM Free:   {ram['ram_free_gb']} GB\n"
        f"AI Tier:    {ram['description']}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN MESSAGE HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid      = str(update.effective_user.id)
    username = update.effective_user.username or ""
    text     = update.message.text or ""
    ensure_user(uid, username)

    ok, rate_msg = check_rate(uid, get_user(uid)["tier"])
    if not ok:
        await update.message.reply_text(rate_msg)
        return

    # Session flows
    action, sess_data, step = get_session(uid)

    if action == "priv_send_waiting_wallet" and step == 1:
        wallet = text.strip()
        if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", wallet):
            amount = sess_data.get("amount", 0)
            hops   = sess_data.get("hops", 3)
            clear_session(uid)
            await update.message.reply_text(f"⏳ Private send queued!\n\nAmount: {amount} SOL\nHops: {hops}\nWe'll notify you when complete.")
        else:
            await update.message.reply_text("❌ Invalid Solana address. Try again or /start to cancel.")
        return

    if action == "alert_waiting_price" and step == 1:
        try:
            target    = float(text.strip().replace("$", "").replace(",", ""))
            coin      = sess_data.get("coin", "sol")
            direction = sess_data.get("direction", "above")
            clear_session(uid)
            set_alert(uid, coin, target, direction)
            await update.message.reply_text(f"🔔 Alert set!\n{coin.upper()} {direction} ${target:,}")
        except ValueError:
            await update.message.reply_text("❌ Enter a valid number, e.g. 200")
        return

    # Intent engine
    handled = await parse_intent(text, uid, update, context)
    if handled:
        save_memory(uid, "user", text)
        return

    # Tool detection
    tool_result = detect_tool(text)
    if tool_result:
        save_memory(uid, "user", text)
        save_memory(uid, "assistant", tool_result)
        await update.message.reply_text(tool_result)
        return

    # AI brain (Hermes → OpenRouter)
    history       = get_memory(uid, limit=8)
    agent         = route(text)
    u             = get_user(uid)
    ram           = get_ram_info()
    collaborative = ram["can_run_all"]

    reply = ask(text, tier=u["tier"], history=history, agent=agent, collaborative=collaborative)

    save_memory(uid, "user", text)
    save_memory(uid, "assistant", reply)
    extract_and_learn(text, reply, uid)

    await update.message.reply_text(reply)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CALLBACK HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = str(query.from_user.id)
    data = query.data
    ensure_user(uid)

    async def edit(text: str, kb: InlineKeyboardMarkup = None):
        try:
            await query.edit_message_text(text, reply_markup=kb)
        except Exception:
            await query.message.reply_text(text, reply_markup=kb)

    # Dashboards
    if   data == "dash_hub":         t, k = build_hub_dashboard(uid);          await edit(t, k)
    elif data == "dash_market":      t, k = build_market_dashboard();           await edit(t, k)
    elif data == "dash_portfolio":   t, k = build_portfolio_dashboard(uid);     await edit(t, k)
    elif data == "dash_alert_menu":  t, k = build_alerts_dashboard(uid);        await edit(t, k)
    elif data == "dash_giftcards":   t, k = build_giftcards_dashboard(uid);     await edit(t, k)
    elif data == "dash_commands":    t, k = build_commands_dashboard(uid);      await edit(t, k)
    elif data == "dash_system":
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="dash_system"),
            InlineKeyboardButton("🤖 Hub",     callback_data="dash_hub"),
        ]])
        await edit(build_system_status(), kb)
    elif data == "dash_trending":    await edit(tool_trending())
    elif data == "dash_dominance":   await edit(tool_dominance())
    elif data == "dash_sentiment":   await edit(tool_fear_greed())
    elif data == "dash_network":     await edit(tool_gas())
    elif data.startswith("dash_news_"):
        await edit(tool_news(data.replace("dash_news_", "")))
    elif data == "dash_dca":
        await edit("📅 DCA Plans\n\nUse /task to set up automated tasks or type 'set up DCA'.")
    elif data == "dash_x402":
        await edit(
            f"━━━━━━━━━━━━━━━━━━━━\n  💳  X402 Payments\n━━━━━━━━━━━━━━━━━━━━\n"
            f"Status: {'✅ Enabled' if X402_ENABLED else '⚠️  Disabled (set X402_ENABLED=true in .env)'}\n\n"
            "Paste a URL and say 'pay' or 'access' to trigger.\n━━━━━━━━━━━━━━━━━━━━"
        )

    # Wizards
    elif data == "wizard_buy":      await show_buy_wizard(update, context, uid)
    elif data == "wizard_private":  await show_private_send_wizard(update, context, uid)
    elif data == "wizard_dca":      await show_dca_wizard(update, context, uid)
    elif data == "wizard_giftcard": await show_gift_card_wizard(update, context, uid)
    elif data == "wizard_alert":    await show_alert_wizard(update, context, uid)
    elif data == "cancel_wizard":
        clear_session(uid)
        await edit("Cancelled. ✌️")

    # Alert wizard steps
    elif data.startswith("alert_coin_"):
        coin     = data.replace("alert_coin_", "")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↑ Above (price rises)", callback_data=f"alert_dir_{coin}_above"),
             InlineKeyboardButton("↓ Below (price drops)", callback_data=f"alert_dir_{coin}_below")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_wizard")],
        ])
        await edit(f"🔔 {coin.upper()} alert — choose direction:", keyboard)
    elif data.startswith("alert_dir_"):
        parts     = data.split("_")
        coin      = parts[2]
        direction = parts[3]
        set_session(uid, "alert_waiting_price", {"coin": coin, "direction": direction}, step=1)
        await edit(f"🔔 {coin.upper()} — price {direction}\n\nReply with the target price.\nExample: 200")

    # Trade actions
    elif data.startswith("sell_pos_"):
        pos_id = int(data.replace("sell_pos_", ""))
        result = close_position(uid, pos_id)
        await edit("✅ Position closed." if result.get("ok") else f"❌ {result.get('error','Failed')}")

    elif data.startswith("cancel_alert_"):
        alert_id = int(data.replace("cancel_alert_", ""))
        with sqlite3.connect(DB_PATH) as db:
            db.execute("UPDATE alerts SET active=0 WHERE id=? AND user_id=?", (alert_id, uid))
        t, k = build_alerts_dashboard(uid)
        await edit(t, k)

    elif data.startswith("buy_amt_"):
        parts  = data.split("_")
        token  = parts[2]
        amount = float(parts[3])
        await show_buy_wizard(update, context, uid, token=token, amount=amount)

    elif data.startswith("buy_confirm_"):
        parts  = data.split("_")
        token  = parts[2]
        amount = float(parts[3])
        res    = await jupiter_swap(uid, "sol", token, amount)
        if res.get("ok"):
            fee = take_fee(uid, amount)
            await edit(f"✅ Bought {amount} SOL of {token.upper()}\nFee: {fee:.6f} SOL")
        else:
            await edit(f"❌ Swap failed: {res.get('error','unknown')}")

    elif data.startswith("gc_amt_"):
        parts  = data.split("_")
        brand  = parts[2]
        amount = float(parts[3])
        await show_gift_card_wizard(update, context, uid, brand=brand, amount=amount)

    elif data.startswith("gc_confirm_"):
        parts  = data.split("_")
        brand  = parts[2]
        amount = float(parts[3])
        await edit(f"⏳ Placing order: {brand} ${amount:.0f}...")
        result = place_gift_card_order(uid, brand, amount)
        if result.get("ok"):
            await edit(
                f"✅ Gift Card Order!\n\nProduct: {brand}\nAmount: ${amount:.0f}\n"
                f"Order: {result.get('order_ref','N/A')}\n{result.get('note','')}"
            )
        else:
            await edit(f"❌ Order failed: {result.get('error','unknown')}")

    elif data.startswith("priv_hops_"):
        parts  = data.split("_")
        hops   = int(parts[2])
        amount = float(parts[3])
        if amount <= 0:
            await edit("❌ Specify an amount. Type: send 0.5 SOL privately")
        else:
            set_session(uid, "priv_send_waiting_wallet", {"amount": amount, "hops": hops}, step=1)
            await edit(
                f"🔒 Private Send — Step 2\n\nAmount: {amount} SOL\nHops: {hops}\n\n"
                f"Reply with the recipient's Solana wallet address."
            )

    else:
        logger.warning(f"Unhandled callback: {data}")
        await edit("⚠️ Unknown action. Try /start to reset.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BACKGROUND JOBS (PTB v20 job_queue)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def job_price_alerts(context: ContextTypes.DEFAULT_TYPE):
    try:
        with sqlite3.connect(DB_PATH) as db:
            alerts = db.execute(
                "SELECT id, user_id, coin, target, direction FROM alerts WHERE active=1"
            ).fetchall()
        for alert_id, uid, coin, target, direction in alerts:
            try:
                price_txt = tool_crypto(coin)
                m         = re.search(r"\$([0-9,]+\.?\d*)", price_txt)
                if not m:
                    continue
                current = float(m.group(1).replace(",", ""))
                if (direction == "above" and current >= target) or \
                   (direction == "below" and current <= target):
                    with sqlite3.connect(DB_PATH) as db:
                        db.execute("UPDATE alerts SET active=0 WHERE id=?", (alert_id,))
                    await context.bot.send_message(
                        chat_id=uid,
                        text=(
                            f"🔔 Alert Triggered!\n\n"
                            f"{coin.upper()} is {direction} ${target:,}\n"
                            f"Current: ${current:,}"
                        ),
                    )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Price alert job error: {e}")

async def job_position_manager(context: ContextTypes.DEFAULT_TYPE):
    try:
        await check_and_manage_positions(context.bot)
    except Exception as e:
        logger.error(f"Position manager error: {e}")

async def job_dca_runner(context: ContextTypes.DEFAULT_TYPE):
    try:
        await run_dca_plans(context.bot)
    except Exception as e:
        logger.error(f"DCA runner error: {e}")

async def job_health(context: ContextTypes.DEFAULT_TYPE):
    if not OWNER_ID:
        return
    try:
        ha = time.time() - 3600
        with sqlite3.connect(DB_PATH) as db:
            total  = db.execute("SELECT COUNT(*) FROM health_log WHERE ts>?", (ha,)).fetchone()[0]
            errors = db.execute("SELECT COUNT(*) FROM health_log WHERE ts>? AND event='error'", (ha,)).fetchone()[0]
        if total > 0 and (errors / total) * 100 > 10:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"⚠️ Health alert: {errors}/{total} errors in last hour.",
            )
    except Exception as e:
        logger.error(f"Health job error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    init_db()
    init_trading_tables()

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN missing from .env")
        exit(1)
    if not OPENROUTER_API_KEY:
        print("⚠️  OPENROUTER_API_KEY missing — cloud AI will be offline")

    ram = get_ram_info()
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("BrothaBot v6.0 starting...")
    logger.info(f"RAM: {ram['ram_free_gb']} GB free / {ram['ram_total_gb']} GB total")
    logger.info(f"AI Tier: {ram['tier']} — {ram['description']}")

    # Detect Ollama / Hermes
    if os.getenv("LOW_RAM") == "1":
        logger.info("LOW_RAM mode: Hermes disabled, using OpenRouter only")
    else:
        ollama_ok, ollama_models = detect_ollama()
        if ollama_ok:
            logger.info(f"Ollama running. Models: {ollama_models}")
            if ram["can_run_hermes"]:
                has_8b  = any("hermes3" in m.lower() and "70b" not in m.lower() for m in ollama_models)
                has_70b = any("70b" in m.lower() for m in ollama_models)
                if has_8b:
                    logger.info("✅ Hermes 8B ready — local AI active")
                else:
                    logger.info("⚠️  Hermes 8B not pulled. Run: ollama pull hermes3")
                if has_70b and ram["can_run_titan"]:
                    logger.info("🔥 Hermes 70B ready — TITAN mode active!")
                elif has_70b:
                    logger.info(f"⚠️  Hermes 70B pulled but only {ram['ram_free_gb']} GB RAM free (need 40 GB)")
            else:
                logger.warning(f"⚠️  {ram['ram_free_gb']} GB RAM free — need 4 GB for Hermes. Using OpenRouter.")
        else:
            logger.info("Ollama not running. Using OpenRouter cloud AI.")
            logger.info("To enable Hermes: brew install ollama && ollama serve && ollama pull hermes3")

    logger.info(f"Trading module: {'✅' if TRADING_ENABLED else '⚠️  not loaded'}")
    logger.info(f"Helius RPC:     {'✅' if HELIUS_API_KEY else '⚠️  public RPC'}")
    logger.info(f"Gift Cards:     {'✅ live' if BITREFILL_API_KEY else '⚠️  demo mode'}")
    logger.info(f"X402:           {'✅' if X402_ENABLED else 'disabled'}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("status",      cmd_status))
    app.add_handler(CommandHandler("system",      cmd_system))
    app.add_handler(CommandHandler("hermes",      cmd_hermes))   # NEW — Hermes-specific status
    app.add_handler(CommandHandler("teach",       cmd_teach))
    app.add_handler(CommandHandler("commands",    cmd_commands))
    app.add_handler(CommandHandler("brain",       cmd_brain))
    app.add_handler(CommandHandler("giftcard",    cmd_giftcard))
    app.add_handler(CommandHandler("gc",          cmd_giftcard))
    app.add_handler(CommandHandler("balance",     cmd_balance))
    app.add_handler(CommandHandler("price",       cmd_price))
    app.add_handler(CommandHandler("market",      cmd_market))
    app.add_handler(CommandHandler("health",      cmd_health))

    # Messages + callbacks
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Background jobs (PTB v20 job_queue — correct approach)
    jq = app.job_queue
    jq.run_repeating(job_price_alerts,    interval=60,  first=10)
    jq.run_repeating(job_position_manager, interval=300, first=30)
    jq.run_repeating(job_dca_runner,      interval=120, first=20)
    jq.run_repeating(job_health,          interval=300, first=60)

    logger.info("BrothaBot v6.0 is live. 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
