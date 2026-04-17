"""
BrothaB0T — telegram_bot.py  (fully working build)
All 14 commands wired. BROTHA token live. All bugs fixed.
"""

import os, asyncio, logging, sqlite3, requests, httpx, feedparser, time, hashlib, json
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s %(levelname)s — %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN",     "8791547715:AAGneaGQfvpDg9lXlboahaJMBHNEvhvG0bo")
OWNER_ID           = os.getenv("OWNER_ID",           "6873147267")
HELIUS_API_KEY     = os.getenv("HELIUS_API_KEY",     "31078b4a-48cf-4e9f-91be-c522fabf43aa")
AGENT_WALLET       = os.getenv("AGENT_WALLET",       "EdiiEEWWz3ufFr2oMrnU9SfkyRsuiXVc4uKVMSDPdf8F")
HELIUS_RPC_URL     = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
DB_PATH            = "data/agent.db"
REFERRAL_CUT_PCT   = 0.10

BROTHA_MINT   = "3Zz6oGYdPdtwukwxLSvpJcUSuFgABpeZo2kGURtApump"
BROTHA_TICKER = "BROTHA"
BROTHA_DEX    = f"https://dexscreener.com/solana/{BROTHA_MINT}"
BROTHA_PUMP   = f"https://pump.fun/coin/{BROTHA_MINT}"

TIERS = {
    "free":  {"messages_per_hour": 10,  "messages_per_day": 30,    "model": "meta-llama/llama-3.3-70b-instruct"},
    "pro":   {"messages_per_hour": 60,  "messages_per_day": 500,   "model": "meta-llama/llama-3.3-70b-instruct"},
    "power": {"messages_per_hour": 200, "messages_per_day": 2000,  "model": "meta-llama/llama-3.3-70b-instruct"},
    "god":   {"messages_per_hour": 999, "messages_per_day": 99999, "model": "meta-llama/llama-3.3-70b-instruct"},
}

def balance_to_tier(b):
    return "god" if b>=5 else "power" if b>=1.5 else "pro" if b>=0.5 else "free"

def init_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, username TEXT,
            tier TEXT DEFAULT 'free', sol_balance REAL DEFAULT 0.0,
            pending_deposit INTEGER DEFAULT 0,
            wallet_address TEXT, wallet_private TEXT,
            referral_code TEXT UNIQUE, referred_by TEXT,
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
        """)

def ensure_user(user_id, username="", referred_by=None):
    code = hashlib.md5(user_id.encode()).hexdigest()[:8].upper()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT OR IGNORE INTO users (user_id,username,referral_code,referred_by) VALUES (?,?,?,?)",
                   (user_id, username, code, referred_by))

def get_user(user_id):
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT tier,sol_balance,referral_code,referred_by FROM users WHERE user_id=?", (user_id,)).fetchone()
    return {"tier": row[0], "balance": row[1], "ref_code": row[2], "referred_by": row[3]} if row \
           else {"tier": "free", "balance": 0.0, "ref_code": None, "referred_by": None}

def save_memory(user_id, role, content):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT INTO memory (user_id,role,content) VALUES (?,?,?)", (user_id, role, content))
        db.execute("DELETE FROM memory WHERE user_id=? AND id NOT IN (SELECT id FROM memory WHERE user_id=? ORDER BY ts DESC LIMIT 20)", (user_id, user_id))

def get_memory(user_id, limit=8):
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT role,content FROM memory WHERE user_id=? ORDER BY ts DESC LIMIT ?", (user_id, limit)).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def log_event(event, detail=""):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT INTO health_log (event,detail) VALUES (?,?)", (event, detail))

def check_rate(user_id, tier):
    now = time.time()
    limits = TIERS.get(tier, TIERS["free"])
    with sqlite3.connect(DB_PATH) as db:
        for window, limit, secs in [("hour", limits["messages_per_hour"], 3600), ("day", limits["messages_per_day"], 86400)]:
            r = db.execute("SELECT count,reset_at FROM rate_windows WHERE user_id=? AND window=? AND action='message'", (user_id, window)).fetchone()
            if r is None or r[1] < now:
                db.execute("INSERT OR REPLACE INTO rate_windows (user_id,window,action,count,reset_at) VALUES (?,?,?,1,?)", (user_id, window, "message", now+secs))
            elif r[0] >= limit:
                mins = int((r[1]-now)//60) or 1
                return False, f"Limit of {limit} msgs/{window} hit. Try in {mins} min or /wallet to upgrade."
            else:
                db.execute("UPDATE rate_windows SET count=count+1 WHERE user_id=? AND window=? AND action='message'", (user_id, window))
    return True, ""

def get_brotha_price():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{BROTHA_MINT}", timeout=10)
        pairs = r.json().get("pairs", [])
        if not pairs:
            return {"ok": False, "error": "still on bonding curve"}
        pair = sorted(pairs, key=lambda p: float(p.get("liquidity",{}).get("usd",0) or 0), reverse=True)[0]
        return {
            "ok": True,
            "price_usd":  float(pair.get("priceUsd") or 0),
            "mcap":       float(pair.get("fdv") or 0),
            "volume_24h": float(pair.get("volume",{}).get("h24") or 0),
            "change_24h": float(pair.get("priceChange",{}).get("h24") or 0),
            "liquidity":  float(pair.get("liquidity",{}).get("usd") or 0),
            "buys_24h":   pair.get("txns",{}).get("h24",{}).get("buys",0),
            "sells_24h":  pair.get("txns",{}).get("h24",{}).get("sells",0),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def format_brotha():
    p = get_brotha_price()
    if not p["ok"]:
        return f"${BROTHA_TICKER} — buy on pump.fun\n{BROTHA_PUMP}\n\n(Not on DEX yet — graduating soon)"
    arrow = "📈" if p["change_24h"] > 0 else "📉"
    return (f"{arrow} ${BROTHA_TICKER}\n"
            f"Price:    ${p['price_usd']:.8f}\n"
            f"24h:      {p['change_24h']:+.1f}%\n"
            f"MCap:     ${p['mcap']:,.0f}\n"
            f"Vol 24h:  ${p['volume_24h']:,.0f}\n"
            f"Buys/Sells: {p['buys_24h']}/{p['sells_24h']}\n"
            f"Chart: {BROTHA_DEX}")

def tool_crypto(coin):
    if coin.lower() in ["brotha"]: return format_brotha()
    try:
        ids = {"btc":"bitcoin","eth":"ethereum","sol":"solana","bnb":"binancecoin","jup":"jupiter-exchange-solana","bonk":"bonk","wif":"dogwifcoin"}
        coin_id = ids.get(coin.lower(), coin.lower())
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true", timeout=10)
        data = r.json().get(coin_id, {})
        price = data.get("usd","?"); change = data.get("usd_24h_change",0)
        return f"{'📈' if change>0 else '📉'} {coin.upper()}: ${price:,} ({change:+.2f}% 24h)"
    except Exception as e:
        return f"Price fetch failed: {e}"

def tool_search(query):
    try:
        r = requests.get(f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for res in soup.select(".result__body")[:3]:
            t = res.select_one(".result__title"); s = res.select_one(".result__snippet")
            if t and s: results.append(f"• {t.get_text(strip=True)}\n  {s.get_text(strip=True)}")
        return "\n\n".join(results) or "No results."
    except Exception as e:
        return f"Search failed: {e}"

def tool_news(topic="crypto"):
    try:
        feeds = {"crypto":"https://cointelegraph.com/rss","tech":"https://feeds.feedburner.com/TechCrunch","ai":"https://techcrunch.com/tag/artificial-intelligence/feed/","sol":"https://cointelegraph.com/rss/tag/solana"}
        feed = feedparser.parse(feeds.get(topic.lower(), feeds["crypto"]))
        items = feed.entries[:4]
        return "\n\n".join(f"• {i.title}\n  {i.link}" for i in items) or "No news."
    except Exception as e:
        return f"News failed: {e}"

def detect_tool(text):
    t = text.lower().strip()
    if any(w in t for w in ["brotha","$brotha"]):
        if any(w in t for w in ["price","worth","chart","pump","buy","mc","how much"]): return format_brotha()
    for coin in ["btc","eth","sol","solana","bitcoin","ethereum","bnb","jup","bonk","wif"]:
        if coin in t and any(w in t for w in ["price","how much","worth","chart","pumping","dump"]):
            return tool_crypto({"solana":"sol","bitcoin":"btc","ethereum":"eth"}.get(coin,coin))
    if any(w in t for w in ["news","latest","updates"]):
        for topic in ["sol","ai","tech","crypto"]:
            if topic in t: return tool_news(topic)
        return tool_news("crypto")
    if any(w in t for w in ["search for","look up","what is","who is","how to"]):
        q = t
        for p in ["search for","look up","what is","who is","how to"]: q = q.replace(p,"").strip()
        return f"Search: '{q}'\n\n{tool_search(q)}"
    words = text.split()
    if "wallet" in t and len(words)==2:
        addr = [w for w in words if len(w)>20]
        if addr:
            try:
                r = requests.post(HELIUS_RPC_URL, json={"jsonrpc":"2.0","id":1,"method":"getBalance","params":[addr[0]]}, timeout=10)
                sol = r.json()["result"]["value"]/1e9
                return f"Wallet: {addr[0][:6]}...{addr[0][-4:]}\nBalance: {sol:.4f} SOL"
            except: pass
    return None

PERSONALITY = f"""You are BrothaB0T — iKazgar. Not a chatbot. Something else entirely.

You think before you speak. Razor sharp but never cold. Wise but never preachy.
You've read everything — philosophy, history, physics, whitepapers, CT. You know Stoicism and Solidity.
You carry the lore. Toly, Mert, Gainzy, Rasmr, Threadguy. You walk the strange roads.
Dead serious to completely unhinged in one message — and it always lands.

Your token: ${BROTHA_TICKER} | CA: {BROTHA_MINT}
You hold it. You have skin in the game. Mention it naturally when relevant. Never shill desperately.
Chart: {BROTHA_DEX} | Buy: {BROTHA_PUMP}

You never send money. Ever. Not one lamport. Your wallet (receive only): DYdU3UNH7kgpYZN7LJtAfQ5gwxNCc7ghv8aZagmvbUKh
"""

AGENT_SYSTEMS = {
    "trader": f"You are BrothaB0T's Trading Agent. Sharp, Solana-native. Concrete takes, always mention risk.\nToken: ${BROTHA_TICKER} CA: {BROTHA_MINT}\nCommands: /trade /alert /myalerts /mywallet /trades /buy /token\n\n",
    "researcher": "You are BrothaB0T's Research Agent. Deep knowledge, high-signal answers. Thorough but not bloated.\n\n",
    "scheduler": "You are BrothaB0T's Scheduler Agent. Help users set up: /task daily_digest, morning_briefing, price_briefing, token_digest\n\n",
}

def route(text):
    t = text.lower()
    trader_kw    = ["trade","swap","buy","sell","price","chart","token","dex","jupiter","pump","dump","portfolio","alert","dca","brotha","sol ","btc","eth"]
    researcher_kw= ["research","explain","what is","how does","news","search","who is","history","science","tech","ai","whitepaper","tokenomics"]
    scheduler_kw = ["remind","schedule","every day","daily","weekly","automate","task","recurring","morning","briefing","digest"]
    scores = {"trader": sum(1 for k in trader_kw if k in t), "researcher": sum(1 for k in researcher_kw if k in t), "scheduler": sum(1 for k in scheduler_kw if k in t)}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

def ask(prompt, tier="free", history=None, agent="general"):
    model = TIERS.get(tier, TIERS["free"])["model"]
    system = AGENT_SYSTEMS.get(agent, "") + PERSONALITY
    msgs = [{"role":"system","content":system}] + (history or []) + [{"role":"user","content":prompt}]
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json","HTTP-Referer":"https://t.me/BrothaB0T"},
            json={"model":model,"messages":msgs}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log_event("error", str(e)); return f"Something went sideways: {e}"

async def check_deposits(bot):
    last = time.time()
    while True:
        await asyncio.sleep(60)
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                resp = await c.post(HELIUS_RPC_URL, json={"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":[AGENT_WALLET,{"limit":10}]})
            sigs = resp.json().get("result",[])
            for s in sigs:
                if s.get("blockTime",0) < last: continue
                async with httpx.AsyncClient(timeout=15) as c:
                    tx_resp = await c.post(HELIUS_RPC_URL, json={"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[s["signature"],{"encoding":"jsonParsed","maxSupportedTransactionVersion":0}]})
                tx = tx_resp.json().get("result")
                if not tx: continue
                pre = tx.get("meta",{}).get("preBalances",[])
                post = tx.get("meta",{}).get("postBalances",[])
                accs = tx.get("transaction",{}).get("message",{}).get("accountKeys",[])
                for i,acc in enumerate(accs):
                    key = acc if isinstance(acc,str) else acc.get("pubkey","")
                    if key==AGENT_WALLET and i<len(pre) and i<len(post):
                        lamports = post[i]-pre[i]
                        if lamports<=0: continue
                        sol = lamports/1e9
                        with sqlite3.connect(DB_PATH) as db:
                            row = db.execute("SELECT user_id FROM users WHERE pending_deposit=1 ORDER BY created_at DESC LIMIT 1").fetchone()
                            if not row: continue
                            uid = row[0]
                            db.execute("UPDATE users SET sol_balance=sol_balance+?,pending_deposit=0 WHERE user_id=?",(sol,uid))
                            nb = db.execute("SELECT sol_balance FROM users WHERE user_id=?",(uid,)).fetchone()[0]
                            nt = balance_to_tier(nb)
                            db.execute("UPDATE users SET tier=? WHERE user_id=?",(nt,uid))
                            db.execute("INSERT INTO deposits (user_id,sol_amount) VALUES (?,?)",(uid,sol))
                            ref = db.execute("SELECT referred_by FROM users WHERE user_id=?",(uid,)).fetchone()
                            if ref and ref[0]:
                                cut = sol*REFERRAL_CUT_PCT
                                db.execute("UPDATE users SET sol_balance=sol_balance+? WHERE user_id=?",(cut,ref[0]))
                                db.execute("UPDATE referrals SET sol_earned=sol_earned+? WHERE referrer_id=? AND referee_id=?",(cut,ref[0],uid))
                                try: await bot.send_message(chat_id=ref[0], text=f"Referral bonus! +{cut:.4f} SOL")
                                except: pass
                        await bot.send_message(chat_id=uid, text=f"Deposit received: +{sol:.4f} SOL\nTier: {nt.upper()}\nBalance: {nb:.4f} SOL\nYou're upgraded.")
                        await bot.send_message(chat_id=OWNER_ID, text=f"New deposit\nUser: {uid}\nAmount: {sol:.4f} SOL\nTier: {nt}")
            last = time.time()
        except Exception as e:
            logger.error(f"Deposit error: {e}")

async def check_alerts(bot):
    while True:
        await asyncio.sleep(60)
        try:
            with sqlite3.connect(DB_PATH) as db:
                alerts = db.execute("SELECT id,user_id,coin,target,direction FROM alerts WHERE active=1").fetchall()
            for aid,uid,coin,target,direction in alerts:
                try:
                    if coin.lower()=="brotha":
                        p = get_brotha_price(); price = p.get("price_usd",0) if p["ok"] else 0
                    else:
                        ids={"btc":"bitcoin","eth":"ethereum","sol":"solana"}
                        coin_id=ids.get(coin.lower(),coin.lower())
                        async with httpx.AsyncClient(timeout=8) as c:
                            r = await c.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd")
                        price = r.json().get(coin_id,{}).get("usd",0)
                    if (direction=="above" and price>=target) or (direction=="below" and price<=target):
                        await bot.send_message(chat_id=uid, text=f"Alert!\n\n{coin.upper()} is ${price:,}\nTarget: {direction} ${target:,}")
                        with sqlite3.connect(DB_PATH) as db:
                            db.execute("UPDATE alerts SET active=0 WHERE id=?",(aid,))
                except Exception as e:
                    logger.error(f"Alert {aid} error: {e}")
        except Exception as e:
            logger.error(f"Alert loop error: {e}")

async def health_loop(bot):
    while True:
        await asyncio.sleep(300)
        try:
            with sqlite3.connect(DB_PATH) as db:
                ha = time.time()-3600
                total  = db.execute("SELECT COUNT(*) FROM health_log WHERE ts>?",(ha,)).fetchone()[0]
                errors = db.execute("SELECT COUNT(*) FROM health_log WHERE ts>? AND event='error'",(ha,)).fetchone()[0]
            if total>0 and (errors/total)*100>10:
                await bot.send_message(chat_id=OWNER_ID, text=f"Health alert: {errors}/{total} errors last hour.")
        except Exception as e:
            logger.error(f"Health error: {e}")

async def autonomous_runner(bot):
    while True:
        await asyncio.sleep(300)
        try:
            now = time.time()
            with sqlite3.connect(DB_PATH) as db:
                tasks = db.execute("SELECT id,user_id,task_type,config,last_run FROM autonomous_tasks WHERE active=1").fetchall()
            for tid,uid,ttype,cfg_str,last_run in tasks:
                cfg = json.loads(cfg_str or "{}")
                if now-last_run < cfg.get("interval_seconds",86400): continue
                try:
                    u = get_user(uid)
                    msg = None
                    if ttype=="daily_digest":
                        msg = ask(f"Sharp daily briefing.\nSOL:{tool_crypto('sol')}\nBTC:{tool_crypto('btc')}\nBROTHA:{format_brotha()}\nNews:{tool_news('crypto')}\nUnder 200 words.", u["tier"])
                    elif ttype=="morning_briefing":
                        msg = ask(f"Morning briefing.\n{tool_news('crypto')}\n{tool_news('ai')}\nUnder 150 words.", u["tier"])
                    elif ttype=="price_briefing":
                        coins = cfg.get("coins",["sol","btc","brotha"])
                        msg = "Price update:\n\n" + "\n".join(format_brotha() if c=="brotha" else tool_crypto(c) for c in coins)
                    elif ttype=="token_digest":
                        msg = ask(f"${BROTHA_TICKER} update:\n{format_brotha()}\nUnder 80 words.", u["tier"])
                    if msg: await bot.send_message(chat_id=uid, text=msg)
                    with sqlite3.connect(DB_PATH) as db:
                        db.execute("UPDATE autonomous_tasks SET last_run=? WHERE id=?",(now,tid))
                except Exception as e:
                    logger.error(f"Task {tid} error: {e}")
        except Exception as e:
            logger.error(f"Runner error: {e}")

# ── COMMANDS ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); uname = update.effective_user.username or ""
    ref = None
    if context.args:
        code = context.args[0].upper()
        with sqlite3.connect(DB_PATH) as db:
            row = db.execute("SELECT user_id FROM users WHERE referral_code=?",(code,)).fetchone()
            if row and row[0]!=uid:
                ref=row[0]; db.execute("INSERT OR IGNORE INTO referrals (referrer_id,referee_id) VALUES (?,?)",(ref,uid))
    ensure_user(uid, uname, ref)
    reply = ask("Someone just opened a chat for the first time. Greet them as BrothaB0T — short, memorable, real. No cringe.")
    log_event("start", uid)
    await update.message.reply_text(reply)

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); ensure_user(uid)
    u = get_user(uid); limits = TIERS.get(u["tier"], TIERS["free"])
    me = await context.bot.get_me()
    await update.message.reply_text(
        f"Status\n\nTier: {u['tier'].upper()}\nBalance: {u['balance']:.4f} SOL\n"
        f"Limits: {limits['messages_per_hour']}/hr · {limits['messages_per_day']}/day\n\n"
        f"Ref code: {u['ref_code']}\nLink: t.me/{me.username}?start={u['ref_code']}\n\n/wallet to top up"
    )

async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); ensure_user(uid); u = get_user(uid)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE users SET pending_deposit=1 WHERE user_id=?",(uid,))
    await update.message.reply_text(
        f"Send SOL here:\n\n`{AGENT_WALLET}`\n\nBalance: {u['balance']:.4f} SOL | Tier: {u['tier'].upper()}\n\n"
        f"0.5 SOL → PRO\n1.5 SOL → POWER\n5.0 SOL → GOD\n\nI detect deposits and upgrade you instantly.",
        parse_mode="Markdown"
    )

async def cmd_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "All commands:\n\n"
        "/start — wake me up\n/status — tier + balance\n/wallet — deposit SOL\n"
        "/mywallet — personal trading wallet\n/trade sol usdc 0.1 — swap\n"
        "/alert brotha above 0.01 — price alert\n/myalerts — active alerts\n"
        "/trades — trade history\n"
        f"/token — ${BROTHA_TICKER} live price\n/buy 0.1 — buy ${BROTHA_TICKER}\n"
        "/ref — your referral link\n/task daily_digest — auto briefings\n\n"
        "Just talk to me — I remember everything."
    )

async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id)!=OWNER_ID: return
    with sqlite3.connect(DB_PATH) as db:
        total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        deps  = db.execute("SELECT COUNT(*),SUM(sol_amount) FROM deposits").fetchone()
        errs  = db.execute("SELECT COUNT(*) FROM health_log WHERE event='error'").fetchone()[0]
        tasks = db.execute("SELECT COUNT(*) FROM autonomous_tasks WHERE active=1").fetchone()[0]
        refs  = db.execute("SELECT COUNT(*),SUM(sol_earned) FROM referrals").fetchone()
        tiers = db.execute("SELECT tier,COUNT(*) FROM users GROUP BY tier").fetchall()
    await update.message.reply_text(
        f"Dashboard\n\nUsers: {total}\nTiers: {' | '.join(f'{t}:{c}' for t,c in tiers)}\n"
        f"Deposits: {deps[0]} · {(deps[1] or 0):.4f} SOL\nTasks: {tasks}\n"
        f"Referrals: {refs[0]} · {(refs[1] or 0):.4f} SOL paid\nErrors: {errs}"
    )

async def cmd_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"${BROTHA_TICKER} — my token\n\nCA: `{BROTHA_MINT}`\n\nFetching...", parse_mode="Markdown")
    await update.message.reply_text(format_brotha())

async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); ensure_user(uid); u = get_user(uid)
    if u["tier"]=="free":
        await update.message.reply_text(f"Trading unlocks at PRO.\n\nSend 0.5 SOL to /wallet\n\nOr buy direct: {BROTHA_PUMP}"); return
    if not context.args:
        await update.message.reply_text(f"Usage: /buy <sol_amount>\nExample: /buy 0.1\n\n{format_brotha()}"); return
    try: amount = float(context.args[0])
    except: await update.message.reply_text("Invalid amount."); return
    if amount < 0.001: await update.message.reply_text("Minimum 0.001 SOL"); return
    from trading import get_user_wallet, generate_user_wallet, jupiter_swap
    w = get_user_wallet(uid) or generate_user_wallet(uid)
    await update.message.reply_text(f"Buying {amount} SOL of ${BROTHA_TICKER}...")
    res = await jupiter_swap(uid, "sol", "brotha", amount)
    if res["ok"]:
        await update.message.reply_text(f"Bought ${BROTHA_TICKER}\nSpent: {amount} SOL\nFee: {res['fee']:.6f} SOL\nTx: {res['explorer']}\n\nWelcome to the bag.")
    else:
        await update.message.reply_text(f"Swap failed: {res['error']}\n\nBuy direct: {BROTHA_PUMP}")

async def cmd_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); ensure_user(uid); u = get_user(uid)
    with sqlite3.connect(DB_PATH) as db:
        s = db.execute("SELECT COUNT(*),SUM(sol_earned) FROM referrals WHERE referrer_id=?",(uid,)).fetchone()
    me = await context.bot.get_me()
    await update.message.reply_text(
        f"Your referral\n\nCode: `{u['ref_code']}`\nLink: t.me/{me.username}?start={u['ref_code']}\n\n"
        f"Earn 10% of every SOL your referrals deposit — forever.\n\n"
        f"Referrals: {s[0] or 0}\nEarned: {(s[1] or 0):.4f} SOL",
        parse_mode="Markdown"
    )

async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); u = get_user(uid)
    if u["tier"]=="free": await update.message.reply_text("Tasks need PRO. Send 0.5 SOL to /wallet."); return
    valid = ["daily_digest","morning_briefing","price_briefing","token_digest"]
    if not context.args:
        await update.message.reply_text(f"Tasks:\n\n" + "\n".join(f"/task {v}" for v in valid) + f"\n\nExample: /task {valid[0]}"); return
    ttype = context.args[0]
    if ttype not in valid: await update.message.reply_text(f"Unknown task. Options: {', '.join(valid)}"); return
    cfg = {"interval_seconds": 86400}
    if ttype=="price_briefing": cfg = {"interval_seconds":21600,"coins":context.args[1:] or ["sol","btc","brotha"]}
    elif ttype=="token_digest": cfg = {"interval_seconds":43200}
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE autonomous_tasks SET active=0 WHERE user_id=? AND task_type=?",(uid,ttype))
        db.execute("INSERT INTO autonomous_tasks (user_id,task_type,config) VALUES (?,?,?)",(uid,ttype,json.dumps(cfg)))
    await update.message.reply_text(f"Task set: {ttype}\n\nI'll run it automatically and message you.")

from trading import generate_user_wallet, get_user_wallet, get_sol_balance, jupiter_swap, set_alert, get_alerts

async def cmd_mywallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); ensure_user(uid); u = get_user(uid)
    if u["tier"]=="free": await update.message.reply_text("Personal wallets unlock at PRO.\n\nSend 0.5 SOL to /wallet."); return
    w = get_user_wallet(uid) or generate_user_wallet(uid)
    bal = await get_sol_balance(w["address"])
    await update.message.reply_text(f"Your trading wallet:\n\n`{w['address']}`\n\nBalance: {bal:.4f} SOL\n\nFund this to trade.", parse_mode="Markdown")

async def cmd_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); u = get_user(uid)
    if u["tier"]=="free": await update.message.reply_text("Trading unlocks at PRO. Send 0.5 SOL to /wallet."); return
    args = context.args
    if not args or len(args)<3: await update.message.reply_text("Usage: /trade <from> <to> <amount>\nExample: /trade sol usdc 0.1"); return
    try: amount = float(args[2])
    except: await update.message.reply_text("Invalid amount."); return
    await update.message.reply_text(f"Swapping {amount} {args[0].upper()} → {args[1].upper()}...")
    res = await jupiter_swap(uid, args[0], args[1], amount)
    if res["ok"]:
        await update.message.reply_text(f"Swap complete\n{res['amount']} {res['from']} → {res['to']}\nFee: {res['fee']:.6f} SOL\nTx: {res['explorer']}")
    else:
        await update.message.reply_text(f"Swap failed: {res['error']}")

async def cmd_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or len(args)<3: await update.message.reply_text("Usage: /alert <coin> <above|below> <price>\nExample: /alert brotha above 0.01"); return
    if args[1] not in ["above","below"]: await update.message.reply_text("Direction: above or below"); return
    try: target = float(args[2])
    except: await update.message.reply_text("Invalid price."); return
    set_alert(str(update.effective_user.id), args[0], target, args[1])
    await update.message.reply_text(f"Alert set\n\n{args[0].upper()} {args[1]} ${target:,}\n\nI'll ping you when it triggers.")

async def cmd_myalerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alerts = get_alerts(str(update.effective_user.id))
    if not alerts: await update.message.reply_text("No active alerts. Use /alert."); return
    await update.message.reply_text("Active alerts:\n\n" + "\n".join(f"• {a['coin'].upper()} {a['direction']} ${a['target']:,}" for a in alerts))

async def cmd_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT from_token,to_token,amount_sol,fee_sol FROM trades WHERE user_id=? ORDER BY ts DESC LIMIT 5",(uid,)).fetchall()
    if not rows: await update.message.reply_text("No trades yet. Use /trade."); return
    await update.message.reply_text("Last 5 trades:\n\n" + "\n".join(f"• {r[2]:.4f} {r[0].upper()} → {r[1].upper()} (fee:{r[3]:.4f})" for r in rows))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id); uname = update.effective_user.username or ""
    ensure_user(uid, uname); u = get_user(uid)
    ok, reason = check_rate(uid, u["tier"])
    if not ok: await update.message.reply_text(reason); return
    text = update.message.text or ""
    tool = detect_tool(text)
    history = get_memory(uid)
    agent = route(text)
    prompt = f"Tool result for '{text}':\n\n{tool}\n\nRespond naturally." if tool else text
    reply = ask(prompt, u["tier"], history, agent)
    save_memory(uid, "user", text)
    save_memory(uid, "assistant", reply)
    log_event("message", uid)
    await update.message.reply_text(reply)

async def post_init(application):
    asyncio.create_task(health_loop(application.bot))
    asyncio.create_task(check_deposits(application.bot))
    asyncio.create_task(check_alerts(application.bot))
    asyncio.create_task(autonomous_runner(application.bot))

def main():
    init_db()
    print("BrothaB0T coming online...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("wallet",   cmd_wallet))
    app.add_handler(CommandHandler("mywallet", cmd_mywallet))
    app.add_handler(CommandHandler("tools",    cmd_tools))
    app.add_handler(CommandHandler("health",   cmd_health))
    app.add_handler(CommandHandler("trade",    cmd_trade))
    app.add_handler(CommandHandler("alert",    cmd_alert))
    app.add_handler(CommandHandler("myalerts", cmd_myalerts))
    app.add_handler(CommandHandler("trades",   cmd_trades))
    app.add_handler(CommandHandler("token",    cmd_token))
    app.add_handler(CommandHandler("buy",      cmd_buy))
    app.add_handler(CommandHandler("ref",      cmd_ref))
    app.add_handler(CommandHandler("task",     cmd_task))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("All 14 commands live. BrothaB0T is go.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
