# Quant Strategy Desk — User Guide

> How to set up, run, and personalise this system. Written for a new user receiving this folder.

---

## What Is This?

A structured monthly investment process powered by a team of 15 AI "agent personas" — each modelled on a real-world hedge fund role (macro strategist, risk officer, compliance, execution, etc.). Once a month, you open a chat, run a command, and receive specific, actionable trade instructions tailored to your investor profile and the current macro environment.

**This is not automated trading.** You place the trades manually through your own broker. The system helps you decide *what* to buy and *why*, with proper risk controls and documentation.

**Time commitment**: ~2–3 hours per month.

---

## Prerequisites

### 1. Claude Code

This system runs inside Claude Code — Anthropic's AI coding assistant. You have two ways to run it:

**Option A — Claude Desktop App (recommended)**
The Claude desktop app includes Claude Code natively. Open the app, navigate to this folder, and start a session. No terminal, no API key, no extra cost — it runs against your existing Claude Pro or Max subscription quota.

> **Note**: The War Room's parallel sub-agent pattern (where 15 agents run simultaneously for Phase 7 sign-off) may run sequentially rather than in parallel on the desktop app. The output is identical — it just takes a few minutes longer.

**Option B — CLI**
```
npm install -g @anthropic-ai/claude-code
claude
```
If you prefer the terminal. Still uses your Claude subscription when you log in — no separate API key needed unless you want to pay per-token via the Anthropic API directly (not necessary for normal use).

**Claude Dispatch** (macOS, Claude Max only): If you have Dispatch, you can assign a War Room from your phone and let your desktop complete it autonomously. Claude Pro users do not have access yet.

> **Model requirement**: Always start your session with **Claude Opus** selected. The monthly War Room requires Opus as orchestrator — it delegates to cheaper models internally, but you must start there. Do not use Sonnet as your starting model for War Rooms.

### 2. A Broker Account

You need a real brokerage account to place the trades. Recommended (all accessible from Europe):

| Broker | Best For | Notes |
|---|---|---|
| **Interactive Brokers (IBKR)** | Serious investors | Lowest commissions at scale. Annual statements perfect for tax filing. |
| **Degiro** | Cost-conscious beginners | No inactivity fees. Limited to European markets mostly. |
| **Trading212** | Small amounts | Fractional shares. Good for low starting capital. |
| **XTB** | Mid-range | No commission on stocks/ETFs up to €100k/month. |

### 3. This Folder

Copy the entire folder to your local machine. You do not need to install any Python libraries to run the monthly War Room — that's all handled by Claude. Python will only matter if you later build automated data pipelines (advanced, optional, listed in the backlog).

---

## First-Time Setup

When you open Claude Code in this folder for the first time and start a session, the system will automatically detect that `INVESTOR_PROFILE.md` is missing and walk you through a short questionnaire (5 questions). It takes about 5 minutes.

The questionnaire covers:
1. Your country of residence (determines tax rates and regulator)
2. Your broker(s)
3. Your approximate monthly investment budget
4. Any existing holdings to import
5. Any sectors/instruments you want to exclude (optional)

Claude will then generate your `INVESTOR_PROFILE.md` — the single file that personalises the entire system. All 15 agent personas read this file automatically. **You only ever need to edit one file to change your profile.**

### If You're Taking Over From Someone Else

When the questionnaire asks if this is your first time, choose option **B — Taking over from someone else**. Claude will ask what needs to change (country, tax rates, broker, etc.) and update your profile accordingly. You do not need to clear the previous user's trade history from `PORTFOLIO.md` unless you want a clean start — previous trades won't affect the agent recommendations unless you choose to carry them forward.

---

## Passing This to Someone Else (Anonymising Your Profile)

If you want to share this system with someone without exposing your personal financial details:

1. Delete `INVESTOR_PROFILE.md` — this is the only file with personal details (tax jurisdiction, brokers, budget range)
2. The trade history in `PORTFOLIO.md` is not personally identifiable (tickers and amounts, no names)
3. `docs/COMPLIANCE.md` contains Portugal-specific tax guidance — the recipient can keep it as reference but should get advice for their own jurisdiction
4. The `brainstorms/` folder contains your historical sessions — delete these if you'd rather start fresh, or keep them as reference material (they contain no personal data, just macro analysis and trade ideas)

Everything else (agents, strategy docs, risk framework, templates) is generic and can be shared as-is.

---

## Monthly Rhythm

### When to Run

Run your War Room **after the 15th of each month**, once key macro data has been released:

- US CPI (typically released 10th–15th of the month)
- US PPI (typically the day before CPI)
- Any ECB rate decision (check the ECB calendar — usually first or second week)

The 15th–20th window gives you a complete picture of the month's macro environment before committing capital. Running earlier means you're missing key inputs.

**Ideal day**: A Saturday or Sunday after the 15th. Markets are closed, you have time to read the output carefully, and you can place trades on Monday morning.

### The Monthly Process (Step by Step)

**Step 1 — Open Claude Code in this folder**
```
cd /path/to/this/folder
claude
```

Set the model to Opus at the start of your session.

**Step 2 — Run the War Room**
Type:
```
/war-room
```

Claude will:
- Review your current portfolio (`PORTFOLIO.md`)
- Check stop-losses from the past month
- Analyse the current macro regime
- Run 4–6 specialist agents in parallel
- Produce 3 specific, actionable trade instructions with entry prices, stop-losses, and plain-English explanations
- Run all 15 agents for a final sign-off check

This takes approximately 15–30 minutes of AI processing time.

**Step 3 — Read the output carefully**

The session is saved to `brainstorms/YYYY-MM.md`. Read:
- The **regime classification** (what macro environment are we in?)
- The **3 trade instructions** (what to buy, how much, what stop-loss to set)
- The **plain English** explanation for each trade (the "In Plain English" box)
- The **Phase 7 sign-off table** — if 3+ agents flagged the same trade, the Strike Team revised it before issuing the final recommendation

**Step 4 — Place the trades**

Within 2 days of the session, place the trades through your broker. Use the exact tickers, ISINs, and stop-loss levels specified.

> **Important**: Set your stop-loss orders as GTC (Good Till Cancelled) immediately at entry. Do not wait until next month's review to set them.

**Step 5 — Update PORTFOLIO.md**

After each trade, add a row to the `Current Holdings` and `Trade History` tables in `PORTFOLIO.md`. The agents read this file at the start of every session — if it's not updated, they cannot track performance or suggest pivots.

**Step 6 — Run the end-of-session commands**
```
/commemorate
/retro
```

This updates `PROGRESS.md` with what was done and logs any lessons learned.

---

## Understanding the Trade Instructions

Each session produces exactly 3 trade instructions. Here's how to read them:

| Field | What It Means |
|---|---|
| **Action** | BUY / SELL / HOLD |
| **Instrument** | The full name of the ETF or stock |
| **ISIN** | The unique identifier — use this to find it on your broker |
| **TER** | Annual fee (for ETFs). Lower is better. 0.2% is reasonable. |
| **Allocation** | What percentage of your total portfolio value to invest |
| **Entry** | Target entry price or "at market" |
| **Stop-loss** | The price at which you should sell to limit losses. Set as a GTC order immediately. |
| **Max you can lose** | The amount you invest. This system is long-only — you cannot lose more than you put in. |

### How Much to Invest Per Trade

If the instruction says "5% NAV" and your total portfolio is €10,000:
```
5% × €10,000 = €500 per trade
```

If you're just starting and the session recommends deploying 15% of NAV across 3 trades:
```
15% ÷ 3 = 5% per trade = €500 each (on a €10,000 portfolio)
```

---

## Stop-Losses — What to Set and How

Every trade instruction includes a stop-loss. This is the price below which you sell, no questions asked. Set it as a GTC (Good Till Cancelled) order on your broker immediately after buying.

**Why**: The system runs monthly. If a position drops significantly between sessions, a GTC stop-loss protects you automatically without requiring you to watch the market daily.

**Stop-loss types used in this system**:
- **ETF hard stop**: The wider of -3% from entry or `Entry − (2 × ATR₂₀)`. Avoids being stopped out by normal daily noise.
- **Single stock stop**: -8% to -12% from entry.
- **Trailing stop**: Activated once the position is +7% to +10%. Locks in profits.

---

## Customising Your Profile

All personalisation lives in `INVESTOR_PROFILE.md`. Edit it directly when your circumstances change:

| Change | What to Update |
|---|---|
| Moved to a different country | Update jurisdiction, tax rates, and regulator fields |
| Changed broker | Update the Brokers table |
| Budget changed significantly | Update the monthly investment budget range |
| New ethical exclusions | Add to Investment Constraints |

After editing `INVESTOR_PROFILE.md`, no other files need changing — all 15 agents reference it automatically.

---

## Key Files Reference

| File | Purpose | Edit? |
|---|---|---|
| `INVESTOR_PROFILE.md` | Your personal profile — jurisdiction, tax, broker, constraints | Yes — yours to own |
| `PORTFOLIO.md` | Live holdings, trade history, P&L, dividends | Yes — update after every trade |
| `AGENTS.md` | Governance rules and agent personas | No — system configuration |
| `PROGRESS.md` | Session log and roadmap | Auto-updated by `/commemorate` |
| `brainstorms/YYYY-MM.md` | Each month's War Room session output | Read-only after the session |
| `docs/RISK_FRAMEWORK.md` | Position sizing, stop-loss rules, drawdown limits | No — unless Risk Officer review |
| `docs/COMPLIANCE.md` | Tax and regulatory guidance (currently Portugal-specific) | Update for your jurisdiction |
| `agents/*.yml` | The 15 agent persona configurations | No — they read INVESTOR_PROFILE.md |

---

## What This System Is Not

- **Not a robo-advisor** — it does not connect to your broker or place trades automatically
- **Not financial advice** — it is an AI-assisted research and decision framework; you are responsible for every trade you place
- **Not a guarantee of returns** — past performance of the system is illustrative; markets are unpredictable
- **Not for active traders** — this is a monthly-cadence, long-only, buy-and-hold-until-stopped system; it is not designed for day trading, options, or short selling

---

## Getting Help

- For problems with Claude Code: open a session and describe the issue — the system is designed to be self-explanatory
- For broker-specific questions: contact your broker's support
- For tax questions specific to your jurisdiction: consult a qualified local tax advisor

---

## Frequently Asked Questions

**Q: Do I need to run the War Room every single month?**
A: No, but consistency improves quality. If you skip a month, the next session will review your existing positions and suggest whether to hold or exit before making new recommendations.

**Q: What if I can't afford to invest the recommended amount?**
A: The allocations are expressed as percentages of your NAV. If your War Room recommends 5% NAV per trade and you have €1,000 invested, that's €50. The system scales to any portfolio size.

**Q: Can I use this with US stocks or crypto?**
A: The system prefers European-accessible instruments (ETFs on Euronext, XETRA, LSE). US stocks are permitted if clearly superior and available on your broker. Crypto is not covered by default.

**Q: What happens if my stop-loss is triggered between monthly sessions?**
A: Your GTC order fires automatically on your broker. At the next War Room, the position will show as CLOSED in `PORTFOLIO.md` (update it first), and the agents will factor in the freed-up cash.

**Q: The AI keeps recommending the same types of trades. Is that normal?**
A: The system has anti-bias rules built in (see `brainstorms/_TEMPLATE.md` — the Anti-Bias Rule and Anti-Assumption Rule). If recommendations feel repetitive, mention it during the session and ask the orchestrator to rotate the Strike Team.
