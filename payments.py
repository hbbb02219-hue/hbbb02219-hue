"""
Payment integration — Razorpay (India ke liye best)
"""

import os
import hmac
import hashlib
from datetime import datetime, timedelta
from database import save_payment, update_user_plan

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

PLAN_DURATIONS = {
    "basic": 365,       # 1 saal
    "premium": 365,     # 1 saal
    "unlimited": 30,    # 1 mahina
}


def get_razorpay_client():
    if not RAZORPAY_KEY_ID:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        return None


def create_payment_link(user_id: int, plan: str, amount: int) -> str:
    """
    Razorpay payment link banata hai.
    Agar keys set nahi hain, demo link return karta hai.
    """
    client = get_razorpay_client()
    if not client:
        return f"https://rzp.io/l/demo-{plan}"

    try:
        data = {
            "amount": amount * 100,  # Razorpay paise mein leta hai
            "currency": "INR",
            "description": f"ResumeAI Bot — {plan.capitalize()} Plan",
            "notify": {"sms": False, "email": False},
            "reminder_enable": False,
            "notes": {
                "user_id": str(user_id),
                "plan": plan,
            },
            "callback_url": os.getenv("WEBHOOK_URL", ""),
            "callback_method": "get",
        }
        link = client.payment_link.create(data)
        return link["short_url"]
    except Exception as e:
        print(f"Razorpay error: {e}")
        return "https://razorpay.com"


def verify_payment(payment_id: str, order_id: str, signature: str) -> bool:
    """Razorpay payment signature verify karta hai."""
    if not RAZORPAY_KEY_SECRET:
        return True  # Dev mode mein skip

    msg = f"{order_id}|{payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def check_payment(payment_id: str):
    """Razorpay se payment status check karo."""
    client = get_razorpay_client()
    if not client:
        return None
    try:
        return client.payment.fetch(payment_id)
    except Exception:
        return None


def activate_plan(user_id: int, plan: str, payment_id: str, amount: int):
    """Payment success ke baad plan activate karo."""
    days = PLAN_DURATIONS.get(plan, 30)
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    update_user_plan(user_id, plan, expiry)
    save_payment(user_id, plan, amount, payment_id, "success")
    print(f"✅ Plan activated: user={user_id}, plan={plan}, expiry={expiry}")