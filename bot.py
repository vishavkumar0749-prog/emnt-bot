import json
import os
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

TOKEN = "8693628855:AAGFIErbyJVsUI9PxD0hozZhv_q8R66kGj4"
ADMIN_ID = 8593936230

DEPOSIT_ADDRESS = "3emTg6qi7aXiiRNRvG75Bo6HDgPXnF32WnyPNoPjGURM"
CHAIN_NAME = "Solana"

MAX_LIMIT = 500000000
REF_BONUS = 0.1
REF_BUY_COMMISSION_PERCENT = 5
FILE_NAME = "data.json"

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},
        "buy": [],
        "withdraw": []
    }

def save_data():
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_data()

def ensure_user(uid):
    uid = str(uid)
    if uid not in db["users"]:
        db["users"][uid] = {
            "bal": 0.0,
            "ref": 0,
            "by": None,
            "state": "",
            "temp_wallet": ""
        }
        save_data()
    return uid

def mask_address(addr):
    if len(addr) <= 12:
        return addr
    return addr[:6] + "......" + addr[-6:]

def get_latest_pending_buy(uid):
    uid = str(uid)
    pending = [r for r in db["buy"] if r["u"] == uid and r["s"] == "pending_payment"]
    if not pending:
        return None
    return sorted(pending, key=lambda x: x["id"], reverse=True)[0]

def find_buy_request(rid):
    for r in db["buy"]:
        if r["id"] == rid:
            return r
    return None

def find_withdraw_request(rid):
    for r in db["withdraw"]:
        if r["id"] == rid:
            return r
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user.id)

    if context.args:
        try:
            ref = str(int(context.args[0]))
            if ref != uid and db["users"][uid]["by"] is None:
                ensure_user(ref)
                db["users"][uid]["by"] = ref
                db["users"][ref]["bal"] += REF_BONUS
                db["users"][ref]["ref"] += 1
                save_data()
        except:
            pass

    await update.message.reply_text(
        "EMNT Pre-Sale\n"
        "First Phase\n\n"
        "/balance - Check wallet\n"
        "/refer - Get referral link\n"
        "/buy - Buy EMNT\n"
        "/buyrequest amount - Create buy request\n"
        "/withdraw - Create withdraw request\n"
        "/myrequests - View your requests"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user.id)
    u = db["users"][uid]
    emnt_balance = u["bal"]
    usdt_value = emnt_balance * 1

    await update.message.reply_text(
        "EMNT Pre-Sale\n"
        "First Phase\n\n"
        f"Balance: {emnt_balance} EMNT\n"
        f"Equal To: {usdt_value} USDT\n"
        f"Referrals: {u['ref']}"
    )

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user.id)
    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}?start={uid}"

    await update.message.reply_text(
        f"EMNT Pre-Sale\n"
        f"First Phase\n\n"
        f"Your Referral Link:\n{link}\n\n"
        f"Signup Reward: {REF_BONUS} EMNT\n"
        f"Buy Commission: {REF_BUY_COMMISSION_PERCENT}%"
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    masked = mask_address(DEPOSIT_ADDRESS)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="Copy Deposit Address",
                copy_text=CopyTextButton(DEPOSIT_ADDRESS)
            )
        ]
    ])

    await update.message.reply_text(
        "EMNT Pre-Sale\n"
        "First Phase\n\n"
        "Buy EMNT\n"
        "Price: 1 EMNT = 1 USDT\n"
        "Maximum Buy Limit: 50,00,00,000 EMNT\n\n"
        f"Deposit Address:\n{masked}\n\n"
        f"Address Chain: {CHAIN_NAME}\n\n"
        "Step 1:\n"
        "/buyrequest amount\n\n"
        "Step 2:\n"
        "After payment, just send your real blockchain hash id directly in chat",
        reply_markup=keyboard
    )

async def buyrequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user.id)

    if len(context.args) < 1:
        await update.message.reply_text("Use: /buyrequest amount")
        return

    try:
        amt = float(context.args[0])
    except:
        await update.message.reply_text("Invalid amount")
        return

    if amt <= 0:
        await update.message.reply_text("Amount must be greater than 0")
        return

    if amt > MAX_LIMIT:
        await update.message.reply_text("Maximum buy limit is 50,00,00,000 EMNT")
        return

    rid = len(db["buy"]) + 1
    db["buy"].append({
        "id": rid,
        "u": uid,
        "amt": amt,
        "tx": "",
        "s": "pending_payment"
    })
    save_data()

    masked = mask_address(DEPOSIT_ADDRESS)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="Copy Deposit Address",
                copy_text=CopyTextButton(DEPOSIT_ADDRESS)
            )
        ]
    ])

    await update.message.reply_text(
        "EMNT Pre-Sale\n"
        "First Phase\n\n"
        f"Buy Request Created\n"
        f"Request ID: {rid}\n"
        f"Requested EMNT: {amt}\n"
        f"Required USDT: {amt}\n\n"
        f"Deposit Address:\n{masked}\n\n"
        f"Address Chain: {CHAIN_NAME}\n\n"
        "Now send your real blockchain hash id directly in chat.\n"
        "You do not need to type any command.",
        reply_markup=keyboard
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user.id)
    db["users"][uid]["state"] = "withdraw_wallet"
    db["users"][uid]["temp_wallet"] = ""
    save_data()

    await update.message.reply_text(
        "EMNT Pre-Sale\n"
        "First Phase\n\n"
        "Withdrawal Request\n"
        "Please send your SOL chain wallet address."
    )

async def myrequests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    text = "EMNT Pre-Sale\nFirst Phase\n\nYOUR REQUESTS\n\nBUY:\n"
    buy_found = False
    for r in db["buy"]:
        if r["u"] == uid:
            buy_found = True
            text += f"ID {r['id']} | {r['amt']} | {r['s']}\n"
    if not buy_found:
        text += "No buy requests\n"

    text += "\nWITHDRAW:\n"
    wd_found = False
    for r in db["withdraw"]:
        if r["u"] == uid:
            wd_found = True
            text += f"ID {r['id']} | {r['amt']} | {r['s']}\n"
    if not wd_found:
        text += "No withdraw requests\n"

    await update.message.reply_text(text)

async def capture_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = ensure_user(update.effective_user.id)

    if text.startswith("/"):
        return

    user_data = db["users"][uid]

    # WITHDRAW STEP 1: wallet address
    if user_data["state"] == "withdraw_wallet":
        user_data["temp_wallet"] = text
        user_data["state"] = "withdraw_amount"
        save_data()

        await update.message.reply_text(
            "EMNT Pre-Sale\n"
            "First Phase\n\n"
            "Wallet address received.\n"
            "Now send withdrawal amount."
        )
        return

    # WITHDRAW STEP 2: amount
    if user_data["state"] == "withdraw_amount":
        try:
            amt = float(text)
        except:
            await update.message.reply_text("Invalid amount. Please send a number.")
            return

        if amt <= 0:
            await update.message.reply_text("Amount must be greater than 0")
            return

        if amt > MAX_LIMIT:
            await update.message.reply_text("Maximum withdraw limit is 50,00,00,000 EMNT")
            return

        if user_data["bal"] < amt:
            await update.message.reply_text("Low balance")
            return

        wallet = user_data["temp_wallet"]

        rid = len(db["withdraw"]) + 1
        db["withdraw"].append({
            "id": rid,
            "u": uid,
            "amt": amt,
            "w": wallet,
            "s": "pending"
        })

        user_data["state"] = ""
        user_data["temp_wallet"] = ""
        save_data()

        await update.message.reply_text(
            "EMNT Pre-Sale\n"
            "First Phase\n\n"
            f"Withdraw Request Created\n"
            f"Request ID: {rid}\n"
            f"Wallet Address: {wallet}\n"
            f"Amount: {amt}\n"
            f"Chain: {CHAIN_NAME}\n"
            f"Status: Pending Approval"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Approve", callback_data=f"wd_approve_{rid}"),
                InlineKeyboardButton("Reject", callback_data=f"wd_reject_{rid}")
            ]
        ])

        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_ID),
                text=(
                    f"WITHDRAW APPROVAL REQUIRED\n\n"
                    f"Request ID: {rid}\n"
                    f"User ID: {uid}\n"
                    f"Wallet Address: {wallet}\n"
                    f"Amount: {amt}\n"
                    f"Chain: {CHAIN_NAME}"
                ),
                reply_markup=keyboard
            )
        except Exception as e:
            await update.message.reply_text(f"Admin message failed: {e}")
        return

    # HASH CAPTURE FOR BUY
    latest = get_latest_pending_buy(uid)
    if latest is None:
        return

    txid = text

    for r in db["buy"]:
        if r["tx"] == txid:
            await update.message.reply_text("This hash id is already used")
            return

    latest["tx"] = txid
    latest["s"] = "pending_review"
    save_data()

    await update.message.reply_text(
        "EMNT Pre-Sale\n"
        "First Phase\n\n"
        f"Hash Submitted Successfully\n"
        f"Request ID: {latest['id']}\n"
        f"Status: Pending Admin Approval"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Approve", callback_data=f"buy_approve_{latest['id']}"),
            InlineKeyboardButton("Reject", callback_data=f"buy_reject_{latest['id']}")
        ]
    ])

    try:
        await context.bot.send_message(
            chat_id=int(ADMIN_ID),
            text=(
                f"BUY APPROVAL REQUIRED\n\n"
                f"Request ID: {latest['id']}\n"
                f"User ID: {uid}\n"
                f"Requested EMNT: {latest['amt']}\n"
                f"Required USDT: {latest['amt']}\n"
                f"Hash ID: {txid}\n"
                f"Chain: {CHAIN_NAME}"
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        await update.message.reply_text(f"Admin message failed: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != int(ADMIN_ID):
        await query.edit_message_text("Only admin can use this button")
        return

    data_cb = query.data

    if data_cb.startswith("buy_approve_"):
        rid = int(data_cb.split("_")[-1])
        r = find_buy_request(rid)

        if r is None or r["s"] != "pending_review":
            await query.edit_message_text("Buy request not found or already processed")
            return

        db["users"][r["u"]]["bal"] += r["amt"]

        referrer = db["users"][r["u"]].get("by")
        commission_text = ""

        if referrer:
            ensure_user(referrer)
            commission = (r["amt"] * REF_BUY_COMMISSION_PERCENT) / 100
            db["users"][referrer]["bal"] += commission
            commission_text = f"\nReferrer Commission: {commission} EMNT"

            try:
                await context.bot.send_message(
                    chat_id=int(referrer),
                    text=(
                        "EMNT Pre-Sale\n"
                        "First Phase\n\n"
                        "Referral Buy Commission Added\n"
                        f"User Buy Amount: {r['amt']} EMNT\n"
                        f"Your Commission: {commission} EMNT"
                    )
                )
            except:
                pass

        r["s"] = "approved"
        save_data()

        await query.edit_message_text(f"Buy Request #{rid} Approved{commission_text}")
        await context.bot.send_message(
            chat_id=int(r["u"]),
            text=f"Your Buy Request Approved\nCredited: {r['amt']} EMNT"
        )
        return

    if data_cb.startswith("buy_reject_"):
        rid = int(data_cb.split("_")[-1])
        r = find_buy_request(rid)

        if r is None or r["s"] not in ["pending_payment", "pending_review"]:
            await query.edit_message_text("Buy request not found or already processed")
            return

        r["s"] = "rejected"
        save_data()

        await query.edit_message_text(f"Buy Request #{rid} Rejected")
        await context.bot.send_message(
            chat_id=int(r["u"]),
            text=f"Your Buy Request #{rid} Rejected"
        )
        return

    if data_cb.startswith("wd_approve_"):
        rid = int(data_cb.split("_")[-1])
        r = find_withdraw_request(rid)

        if r is None or r["s"] != "pending":
            await query.edit_message_text("Withdraw request not found or already processed")
            return

        if db["users"][r["u"]]["bal"] < r["amt"]:
            await query.edit_message_text("User balance low")
            return

        db["users"][r["u"]]["bal"] -= r["amt"]
        r["s"] = "approved"
        save_data()

        await query.edit_message_text(f"Withdraw Request #{rid} Approved")
        await context.bot.send_message(
            chat_id=int(r["u"]),
            text=f"Your Withdraw Approved\nDeducted: {r['amt']} EMNT"
        )
        return

    if data_cb.startswith("wd_reject_"):
        rid = int(data_cb.split("_")[-1])
        r = find_withdraw_request(rid)

        if r is None or r["s"] != "pending":
            await query.edit_message_text("Withdraw request not found or already processed")
            return

        r["s"] = "rejected"
        save_data()

        await query.edit_message_text(f"Withdraw Request #{rid} Rejected")
        await context.bot.send_message(
            chat_id=int(r["u"]),
            text=f"Your Withdraw Request #{rid} Rejected"
        )
        return

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("refer", refer))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("buyrequest", buyrequest))
app.add_handler(CommandHandler("withdraw", withdraw))
app.add_handler(CommandHandler("myrequests", myrequests))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_text))

print("Bot running...")
app.run_polling()
