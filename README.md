# 🤖 AI Resume + Banner Bot

Telegram pe professional resume aur LinkedIn banner generate karne wala bot — Claude AI se powered!

## ✨ Features

- 📄 **AI Resume** — Claude se professional content
- 🖼️ **LinkedIn Banner** — Custom 4 styles
- 💰 **Razorpay Payments** — India ke liye
- 👑 **Admin Panel** — Owner ko har cheez ka DM
- 🗃️ **SQLite Database** — User data store
- 📢 **Broadcast** — Sabhi users ko message

## 💰 Pricing Plans

| Plan | Price | Limit |
|------|-------|-------|
| Free | ₹0 | 1 Resume |
| Basic | ₹99 | 1 Resume + PDF |
| Premium | ₹299 | 5 Resumes + Cover Letter |
| Unlimited | ₹499/month | Unlimited |

---

## 🚀 Setup Guide

### Step 1 — Telegram Bot Token Lo

1. Telegram mein `@BotFather` open karo
2. `/newbot` bhejo
3. Naam do — e.g. `ResumeAI Bot`
4. Username do — e.g. `resumeai_bot`
5. Token copy karo

### Step 2 — Anthropic API Key Lo

1. https://console.anthropic.com pe jao
2. `API Keys` → `Create Key`
3. Key copy karo

### Step 3 — Razorpay Keys Lo (Optional)

1. https://dashboard.razorpay.com pe account banao
2. Settings → API Keys → Generate
3. Key ID aur Secret copy karo

### Step 4 — Local Run Karo

```bash
# 1. Clone karo
git clone https://github.com/YOUR_USERNAME/resume-banner-bot.git
cd resume-banner-bot

# 2. Virtual environment
python -m venv venv
source venv/bin/activate
# Windows pe: venv\Scripts\activate

# 3. Libraries install karo
pip install -r requirements.txt

# 4. .env file banao
cp .env.example .env
# .env mein apni keys dalo

# 5. Chalao!
python bot.py
