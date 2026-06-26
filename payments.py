"""
Payment System — UPI QR Code Scanner
Razorpay hataya, ab direct UPI QR se payment hogi
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import save_payment, update_user_plan, get_connection
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# OWNER INFO
# ─────────────────────────────────────────────
OWNER_ID = int(os.getenv("OWNER_TELEGRAM_ID", "7663073502"))

# ─────────────────────────────────────────────
# QR CODE — Telegram File ID ya URL
# Apna QR image bot pe bhejo, file_id copy karo
# ─────────────────────────────────────────────
UPI_QR_FILE_PATH = "qr_code.jpg"  # Local file

PLAN_DURATIONS = {
    "basic":     365,   # 1 saal
    "premium":   365,   # 1 saal
    "unlimited": 30,    # 1 mahina
}

PLANS = {
    "basic":     {"name": "Basic",     "price": 99,  "limit": 1},
    "premium":   {"name": "Premium",   "price": 299, "limit": 5},
    "unlimited": {"name": "Unlimited", "price": 499, "limit": 999},
}


# ─────────────────────────────────────────────
# QR Code bhejo user ko
# ─────────────────────────────────────────────
async def send_payment_qr(
    context, chat_id: int, user, plan_key: str
):
    plan = PLANS[plan_key]
    amount = plan["price"]
    plan_name = plan["name"]

    caption = (
        f"💳 *Payment — {plan_name} Plan*\n"
        f"{'─' * 28}\n\n"
        f"💵 Amount: *₹{amount}*\n"
        f"📱 UPI se scan karo aur pay karo\n\n"
        f"✅ *Pay karne ke baad:*\n"
        f"Screenshot lo aur /paid command bhejo\n\n"
        f"_GPay • PhonePe • Paytm • BHIM — sab chalega_ 🇮🇳"
    )

    keyboard = [[
        InlineKeyboardButton(
            "✅ Maine Pay Kar Diya!", 
            callback_data=f"paid_{plan_key}_{amount}"
        )
    ],[
        InlineKeyboardButton("❌ Cancel", callback_data="back_home")
    ]]

    try:
        with open(UPI_QR_FILE_PATH, "rb") as qr:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=qr,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    except FileNotFoundError:
        # Agar file nahi mili toh text message bhejo
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption + "\n\n⚠️ _QR code load nahi hua, owner se contact karo_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ─────────────────────────────────────────────
# User ne pay kar diya — Owner ko verify karne bhejo
# ─────────────────────────────────────────────
async def handle_paid_claim(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    plan_key: str,
    amount: int,
):
    user = update.effective_user
    query = update.callback_query

    # User ko wait message
    await query.edit_message_caption(
        caption=(
            f"⏳ *Payment Verify Ho Rahi Hai...*\n\n"
            f"👤 Naam: {user.first_name}\n"
            f"💵 Amount: ₹{amount}\n"
            f"💎 Plan: {plan_key.upper()}\n\n"
            f"_Owner verify karega — 5-10 min mein activate hoga_ ✅"
        ),
        parse_mode="Markdown",
    )

    # Owner ko approval request bhejo
    keyboard = [[
        InlineKeyboardButton(
            "✅ Approve Karo",
            callback_data=f"approve_{user.id}_{plan_key}_{amount}"
        ),
        InlineKeyboardButton(
            "❌ Reject Karo",
            callback_data=f"reject_{user.id}"
        ),
    ]]

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=(
            f"💰 *Payment Claim Aaya!*\n"
            f"{'─' * 28}\n\n"
            f"👤 User: {user.first_name} (`{user.id}`)\n"
            f"🔗 @{user.username or 'N/A'}\n"
            f"💎 Plan: *{plan_key.upper()}*\n"
            f"💵 Amount: *₹{amount}*\n\n"
            f"_Screenshot check karo phir approve/reject karo_ 👇"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─────────────────────────────────────────────
# Owner ne Approve kiya
# ─────────────────────────────────────────────
async def approve_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    target_user_id: int,
    plan_key: str,
    amount: int,
):
    # Plan activate karo
    days = PLAN_DURATIONS.get(plan_key, 30)
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    update_user_plan(target_user_id, plan_key, expiry)
    save_payment(target_user_id, plan_key, amount, "upi_manual", "success")

    query = update.callback_query

    # Owner ko confirm
    await query.edit_message_text(
        f"✅ *Approved!*\n\n"
        f"👤 User ID: `{target_user_id}`\n"
        f"💎 Plan: *{plan_key.upper()}*\n"
        f"📅 {days} din ke liye active",
        parse_mode="Markdown",
    )

    # User ko notify karo
    await context.bot.send_message(
        chat_id=target_user_id,
        text=(
            f"🎉 *Payment Approved!*\n\n"
            f"✅ Aapka *{plan_key.upper()}* plan activate ho gaya!\n"
            f"📅 {days} din tak valid rahega\n\n"
            f"Ab /resume se naya resume banao! 🚀"
        ),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# Owner ne Reject kiya
# ─────────────────────────────────────────────
async def reject_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    target_user_id: int,
):
    query = update.callback_query

    await query.edit_message_text(
        f"❌ *Rejected!*\n\nUser ID: `{target_user_id}`",
        parse_mode="Markdown",
    )

    await context.bot.send_message(
        chat_id=target_user_id,
        text=(
            "❌ *Payment Verify Nahi Hui*\n\n"
            "Sahi screenshot bhejo ya dobara try karo.\n"
            "Problem ho toh @oye_babyy pe contact karo."
        ),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# /paid command — Screenshot bhejne ke baad
# ─────────────────────────────────────────────
async def paid_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "📸 *Payment Screenshot Bhejo*\n\n"
        "Apna payment screenshot is message ke reply mein bhejo.\n"
        "Owner verify karega aur plan activate karega! ✅",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# Screenshot receive karo
# ─────────────────────────────────────────────
async def receive_screenshot(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    photo = update.message.photo[-1]

    # Owner ko forward karo
    keyboard = [[
        InlineKeyboardButton(
            "✅ Basic Approve (₹99)",
            callback_data=f"approve_{user.id}_basic_99"
        )],[
        InlineKeyboardButton(
            "✅ Premium Approve (₹299)",
            callback_data=f"approve_{user.id}_premium_299"
        )],[
        InlineKeyboardButton(
            "✅ Unlimited Approve (₹499)",
            callback_data=f"approve_{user.id}_unlimited_499"
        )],[
        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{user.id}"
        ),
    ]]

    await context.bot.send_photo(
        chat_id=OWNER_ID,
        photo=photo.file_id,
        caption=(
            f"📸 *Payment Screenshot*\n\n"
            f"👤 {user.first_name} (`{user.id}`)\n"
            f"🔗 @{user.username or 'N/A'}\n\n"
            f"Kaunsa plan approve karna hai? 👇"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    await update.message.reply_text(
        "✅ *Screenshot mil gaya!*\n\n"
        "Owner verify kar raha hai...\n"
        "_5-10 minute mein plan activate hoga_ ⏳",
        parse_mode="Markdown",
    )


def create_payment_link(user_id: int, plan: str, amount: int) -> str:
    """Backward compatibility ke liye — ab use nahi hota."""
    return ""


def activate_plan(
    user_id: int, plan: str, payment_id: str, amount: int
):
    days = PLAN_DURATIONS.get(plan, 30)
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    update_user_plan(user_id, plan, expiry)
    save_payment(user_id, plan, amount, payment_id, "success")