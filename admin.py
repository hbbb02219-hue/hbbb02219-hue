"""
Admin Panel — Owner ke liye
Aapka Telegram ID: 7663073502
Har user activity aapke DM mein aayegi
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_connection, update_user_plan

# ─────────────────────────────────────────────
# OWNER ID — Aapka Telegram ID
# ─────────────────────────────────────────────
OWNER_ID = int(os.getenv("OWNER_TELEGRAM_ID", "7663073502"))


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# ─────────────────────────────────────────────
# Owner ko notification bhejo
# ─────────────────────────────────────────────
async def notify_owner(context, message: str):
    """Koi bhi event ho, owner ke DM mein message aata hai."""
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=message,
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"Owner notify error: {e}")


async def notify_new_user(context, user):
    """Naya user join kiya."""
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM users"
    ).fetchone()["cnt"]
    conn.close()

    await notify_owner(
        context,
        f"👤 *Naya User Aaya!*\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Naam: {user.first_name}\n"
        f"🔗 Username: @{user.username or 'N/A'}\n\n"
        f"📊 Total Users: *{total}*"
    )


async def notify_resume_generated(
    context, user, input_data: dict, result_data: dict
):
    """Koi resume banaya."""
    skills = result_data.get("keySkills", [])
    await notify_owner(
        context,
        f"📄 *Resume Banaya Gaya!*\n\n"
        f"👤 User: {user.first_name} (`{user.id}`)\n"
        f"🔗 @{user.username or 'N/A'}\n"
        f"💼 Job: {input_data.get('job', 'N/A')}\n"
        f"⚡ Skills: {', '.join(skills[:3])}\n"
        f"🎨 Style: {input_data.get('style', 'modern')}\n"
        f"🔗 Headline: _{result_data.get('linkedinHeadline', '')}_"
    )


async def notify_payment(context, user, plan: str, amount: int):
    """Payment aaya."""
    await notify_owner(
        context,
        f"💰 *PAYMENT AAYA!* 🎉\n\n"
        f"👤 User: {user.first_name} (`{user.id}`)\n"
        f"🔗 @{user.username or 'N/A'}\n"
        f"💎 Plan: *{plan.upper()}*\n"
        f"💵 Amount: *₹{amount}*\n\n"
        f"✅ Plan activate ho gaya!"
    )


# ─────────────────────────────────────────────
# /admin command — Sirf owner ke liye
# ─────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("❌ Aapke paas permission nahi hai.")
        return

    conn = get_connection()
    total_users = conn.execute(
        "SELECT COUNT(*) as c FROM users"
    ).fetchone()["c"]
    total_resumes = conn.execute(
        "SELECT COUNT(*) as c FROM resumes"
    ).fetchone()["c"]
    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as s FROM payments WHERE status='success'"
    ).fetchone()["s"]
    today_users = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE date(created_at)=date('now')"
    ).fetchone()["c"]
    today_resumes = conn.execute(
        "SELECT COUNT(*) as c FROM resumes WHERE date(created_at)=date('now')"
    ).fetchone()["c"]
    conn.close()

    keyboard = [
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("📄 Resumes", callback_data="admin_resumes"),
        ],
        [
            InlineKeyboardButton("💰 Payments", callback_data="admin_payments"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("🎁 Plan Do", callback_data="admin_giveplan"),
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"),
        ],
    ]

    await update.message.reply_text(
        f"👑 *Admin Panel*\n"
        f"{'─' * 28}\n\n"
        f"📊 *Overall Stats:*\n"
        f"👥 Total Users: *{total_users}*\n"
        f"📄 Total Resumes: *{total_resumes}*\n"
        f"💰 Total Revenue: *₹{total_revenue}*\n\n"
        f"📅 *Aaj Ka:*\n"
        f"👤 Naye Users: *{today_users}*\n"
        f"📝 Resumes Bane: *{today_resumes}*\n\n"
        f"_Neeche se manage karo_ 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if not is_owner(query.from_user.id):
        await query.answer("❌ Permission nahi!", show_alert=True)
        return
    await query.answer()

    back_btn = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_refresh")]]

    # ── Users list ──
    if query.data == "admin_users":
        conn = get_connection()
        rows = conn.execute(
            "SELECT user_id, first_name, username, plan, created_at "
            "FROM users ORDER BY created_at DESC LIMIT 15"
        ).fetchall()
        conn.close()

        text = "👥 *Recent 15 Users:*\n\n"
        for r in rows:
            plan_icon = "🆓" if r["plan"] == "free" else "💎"
            text += (
                f"{plan_icon} *{r['first_name']}* (`{r['user_id']}`)\n"
                f"   @{r['username'] or 'N/A'} | {r['plan']}\n"
            )
        if not rows:
            text += "_Koi user nahi abhi._"

        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    # ── Resumes list ──
    elif query.data == "admin_resumes":
        conn = get_connection()
        rows = conn.execute("""
            SELECT r.user_id, r.style, r.created_at, u.first_name,
                   json_extract(r.input_data, '$.job') as job
            FROM resumes r
            LEFT JOIN users u ON r.user_id = u.user_id
            ORDER BY r.created_at DESC LIMIT 15
        """).fetchall()
        conn.close()

        text = "📄 *Recent 15 Resumes:*\n\n"
        for r in rows:
            text += (
                f"• *{r['first_name'] or 'User'}* (`{r['user_id']}`)\n"
                f"  💼 {r['job'] or 'N/A'} | 🎨 {r['style']}\n"
            )
        if not rows:
            text += "_Koi resume nahi abhi._"

        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    # ── Payments list ──
    elif query.data == "admin_payments":
        conn = get_connection()
        rows = conn.execute(
            "SELECT user_id, plan, amount, status, created_at "
            "FROM payments ORDER BY created_at DESC LIMIT 15"
        ).fetchall()
        total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as s "
            "FROM payments WHERE status='success'"
        ).fetchone()["s"]
        conn.close()

        text = f"💰 *Payments — Total: ₹{total}*\n\n"
        for r in rows:
            icon = "✅" if r["status"] == "success" else "⏳"
            text += (
                f"{icon} `{r['user_id']}` — "
                f"*{r['plan']}* ₹{r['amount']}\n"
            )
        if not rows:
            text += "_Koi payment nahi abhi._"

        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    # ── Broadcast ──
    elif query.data == "admin_broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.edit_message_text(
            "📢 *Broadcast Message*\n\n"
            "Woh message likhein jo *sabhi users* ko bhejna hai:\n\n"
            "_/cancel se cancel karo_",
            parse_mode="Markdown",
        )

    # ── Free plan do kisi ko ──
    elif query.data == "admin_giveplan":
        context.user_data["awaiting_giveplan"] = True
        await query.edit_message_text(
            "🎁 *Plan Do Kisi Ko*\n\n"
            "Format mein likhein:\n"
            "`USER_ID PLAN`\n\n"
            "Example:\n"
            "`123456789 premium`\n\n"
            "_Plans: basic, premium, unlimited_",
            parse_mode="Markdown",
        )

    # ── Refresh / Back ──
    elif query.data == "admin_refresh":
        conn = get_connection()
        total_users = conn.execute(
            "SELECT COUNT(*) as c FROM users"
        ).fetchone()["c"]
        total_resumes = conn.execute(
            "SELECT COUNT(*) as c FROM resumes"
        ).fetchone()["c"]
        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as s "
            "FROM payments WHERE status='success'"
        ).fetchone()["s"]
        today_users = conn.execute(
            "SELECT COUNT(*) as c FROM users "
            "WHERE date(created_at)=date('now')"
        ).fetchone()["c"]
        today_resumes = conn.execute(
            "SELECT COUNT(*) as c FROM resumes "
            "WHERE date(created_at)=date('now')"
        ).fetchone()["c"]
        conn.close()

        keyboard = [
            [
                InlineKeyboardButton("👥 Users", callback_data="admin_users"),
                InlineKeyboardButton("📄 Resumes", callback_data="admin_resumes"),
            ],
            [
                InlineKeyboardButton("💰 Payments", callback_data="admin_payments"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton("🎁 Plan Do", callback_data="admin_giveplan"),
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"),
            ],
        ]
        await query.edit_message_text(
            f"👑 *Admin Panel*\n{'─'*28}\n\n"
            f"👥 Total Users: *{total_users}*\n"
            f"📄 Total Resumes: *{total_resumes}*\n"
            f"💰 Total Revenue: *₹{total_revenue}*\n\n"
            f"📅 *Aaj Ka:*\n"
            f"👤 Naye Users: *{today_users}*\n"
            f"📝 Resumes Bane: *{today_resumes}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ─────────────────────────────────────────────
# Broadcast handler
# ─────────────────────────────────────────────
async def handle_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["awaiting_broadcast"] = False
    broadcast_text = update.message.text

    conn = get_connection()
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()

    sent, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u["user_id"],
                text=f"📢 *Announcement:*\n\n{broadcast_text}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ *Broadcast Complete!*\n\n"
        f"📤 Sent: *{sent}*\n"
        f"❌ Failed: *{failed}*",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# Give plan handler
# ─────────────────────────────────────────────
async def handle_giveplan(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["awaiting_giveplan"] = False
    try:
        parts = update.message.text.strip().split()
        target_id = int(parts[0])
        plan = parts[1].lower()

        from datetime import datetime, timedelta
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        update_user_plan(target_id, plan, expiry)

        await update.message.reply_text(
            f"✅ *Plan Diya Gaya!*\n\n"
            f"👤 User ID: `{target_id}`\n"
            f"💎 Plan: *{plan}*\n"
            f"📅 Expiry: 1 saal",
            parse_mode="Markdown",
        )
        # User ko bhi batao
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎁 *Congratulations!*\n\n"
                 f"Aapko *{plan.upper()}* plan gift kiya gaya hai!\n"
                 f"Enjoy karo! 🚀",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: `{e}`\n\nFormat: `USER_ID PLAN`",
            parse_mode="Markdown",
        )