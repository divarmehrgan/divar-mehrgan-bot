import os
import logging
import sqlite3
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters,
)

TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL_USERNAME", "@divarmehrgan")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CITY, CATEGORY, SUBCATEGORY, TITLE, DESCRIPTION, PRICE, PHONE, PHOTO, CONFIRM = range(9)

CATEGORIES = {
    "🚗 خودرو": [
        "🚘 خودرو سواری", "🏍️ موتورسیکلت", "🚐 وانت و نیسان",
        "🚚 کامیون و کامیونت", "🚌 اتوبوس و مینی‌بوس", "🚜 ماشین‌آلات کشاورزی",
        "🔧 قطعات و لوازم یدکی", "🛞 لاستیک و رینگ", "🎵 لوازم جانبی خودرو",
        "🧰 خدمات خودرو", "➕ سایر"
    ],
    "🏠 مسکن": [
        "🏠 فروش خانه و آپارتمان", "🏢 فروش مغازه و تجاری", "🌳 فروش زمین",
        "🏗️ فروش کلنگی", "🏘️ اجاره خانه و آپارتمان", "🏪 اجاره مغازه و تجاری",
        "🏢 رهن و اجاره", "🏗️ پیش‌فروش", "🏡 ویلا و باغ"
    ],
    "📱 کالای دیجیتال": [
        "📱 موبایل", "💻 لپ‌تاپ", "🖥️ کامپیوتر", "🖨️ پرینتر و اسکنر",
        "📷 دوربین", "🎧 هدفون و هندزفری", "⌚ ساعت هوشمند", "🎮 کنسول و بازی",
        "📺 تلویزیون", "📡 مودم و تجهیزات شبکه", "💾 هارد و حافظه",
        "🔌 شارژر و کابل", "🧩 لوازم جانبی دیجیتال", "➕ سایر"
    ],
    "🍳 خانه و آشپزخانه": [
        "🛋️ مبلمان", "🪑 میز و صندلی", "🛏️ تخت و سرویس خواب",
        "🧺 فرش و قالی", "🪟 پرده", "🧊 یخچال و فریزر", "🧺 ماشین لباسشویی",
        "🍽️ ماشین ظرفشویی", "🔥 اجاق گاز", "🍳 لوازم آشپزخانه",
        "☕ ظروف و سرویس پذیرایی", "🧹 جاروبرقی و نظافت", "💡 لوازم روشنایی",
        "🪴 دکوراسیون و تزئینی", "🔧 ابزار و وسایل خانه", "➕ سایر"
    ],
    "🛠️ خدمات": [
        "🔧 تعمیرات لوازم خانگی", "🚗 تعمیرات خودرو", "💻 تعمیرات موبایل و کامپیوتر",
        "🏠 تعمیرات و بازسازی ساختمان", "🚰 لوله‌کشی", "⚡ برق‌کاری",
        "🎨 نقاشی ساختمان", "🧱 بنایی و کاشی‌کاری", "❄️ کولر و تأسیسات",
        "🚚 باربری و حمل‌ونقل", "🧹 نظافت", "🌳 باغبانی",
        "📸 عکاسی و فیلمبرداری", "💻 خدمات کامپیوتری", "📚 آموزش",
        "💇 خدمات زیبایی", "👨‍🔧 سایر خدمات"
    ],
    "👕 وسایل شخصی": [
        "👕 لباس", "👟 کفش", "👜 کیف", "💍 طلا و جواهر", "⌚ ساعت",
        "🕶️ عینک", "💄 لوازم آرایشی و بهداشتی", "👶 لوازم کودک و نوزاد",
        "🍼 کالسکه و وسایل نوزاد", "🧸 اسباب‌بازی", "🏋️ لوازم ورزشی شخصی",
        "🎒 لوازم سفر", "➕ سایر"
    ],
    "🎮 سرگرمی و فراغت": [
        "🎮 کنسول و بازی", "🎸 آلات موسیقی", "⚽ لوازم ورزشی", "🚲 دوچرخه",
        "🏕️ لوازم کمپ و سفر", "📚 کتاب و مجله", "🧩 بازی و سرگرمی",
        "🎬 فیلم و آثار هنری", "🎨 لوازم هنری", "🐦 حیوانات و ملزومات",
        "🌱 گل و گیاه", "➕ سایر"
    ],
    "💼 استخدام و کاریابی": [
        "👷 کارگر ساده", "🔨 کارگر فنی", "👨‍🔧 مکانیک و تعمیرکار",
        "🧱 ساختمانی", "🚚 راننده", "🏪 فروشنده", "🧑‍💼 کارمند اداری",
        "💻 کار در حوزه کامپیوتر", "📞 بازاریابی و فروش", "👩‍🍳 آشپز و رستوران",
        "🧹 خدمات و نظافت", "👶 پرستاری و مراقبت", "🏠 کار در منزل",
        "💻 دورکاری", "🎓 کارآموزی", "👥 استخدام نیروی کار", "➕ سایر"
    ],
    "🏭 تجهیزات و صنعتی": [
        "🔧 ابزارآلات", "⚙️ ماشین‌آلات صنعتی", "🏗️ تجهیزات ساختمانی",
        "🚜 تجهیزات کشاورزی", "⚡ تجهیزات برق", "🔌 تجهیزات الکترونیکی",
        "❄️ تجهیزات سرمایشی و گرمایشی", "🏪 تجهیزات فروشگاهی",
        "🍽️ تجهیزات رستوران و آشپزخانه صنعتی", "🏭 تجهیزات کارگاهی",
        "🔩 آهن‌آلات و فلزات", "🧰 تجهیزات ایمنی", "📦 تجهیزات انبارداری",
        "🚛 تجهیزات حمل‌ونقل", "➕ سایر"
    ],
}

CITIES = ["🏘️ مهرگان", "🏘️ زیباشهر", "🏘️ الوند", "🏙️ قزوین"]


def kb(items, cols=2):
    rows = []
    for i in range(0, len(items), cols):
        rows.append([InlineKeyboardButton(x, callback_data=x) for x in items[i:i+cols]])
    return InlineKeyboardMarkup(rows)


def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ بازگشت", callback_data="__back")]
    ])


def user_data(update):
    return update.effective_user.id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🤖 به ربات آگهی دیوار مهرگان خوش آمدید.\n\n"
        "ابتدا شهر محل آگهی را انتخاب کنید:",
        reply_markup=kb(CITIES),
    )
    return CITY


async def choose_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data not in CITIES:
        return CITY
    context.user_data["city"] = q.data
    await q.edit_message_text(
        f"📍 شهر: {q.data}\n\nحالا دسته‌بندی آگهی را انتخاب کنید:",
        reply_markup=kb(list(CATEGORIES.keys())),
    )
    return CATEGORY


async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data not in CATEGORIES:
        return CATEGORY
    context.user_data["category"] = q.data
    await q.edit_message_text(
        f"📍 {context.user_data['city']}\n"
        f"📂 {q.data}\n\n"
        "زیرمجموعه را انتخاب کنید:",
        reply_markup=kb(CATEGORIES[q.data]),
    )
    return SUBCATEGORY


async def choose_subcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["subcategory"] = q.data
    await q.edit_message_text("📝 عنوان آگهی را بنویسید:")
    return TITLE


async def title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text("📄 توضیحات آگهی را بنویسید:")
    return DESCRIPTION


async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text.strip()
    await update.message.reply_text(
        "💰 قیمت را وارد کنید.\n"
        "اگر رایگان است بنویسید «رایگان»."
    )
    return PRICE


async def price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text.strip()
    await update.message.reply_text("📞 شماره تماس را وارد کنید:")
    return PHONE


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(
        "📷 حالا عکس آگهی را ارسال کنید.\n"
        "اگر عکس ندارید، دکمه زیر را بزنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بدون عکس", callback_data="__no_photo")]
        ]),
    )
    return PHOTO


async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("لطفاً یک عکس ارسال کنید یا «بدون عکس» را بزنید.")
        return PHOTO
    context.user_data["photo_id"] = update.message.photo[-1].file_id
    return await show_preview(update, context)


async def no_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["photo_id"] = None
    await q.edit_message_text("در حال آماده‌سازی پیش‌نمایش...")
    fake_update = None
    text = build_ad_text(context.user_data)
    await q.message.reply_text(
        "👀 پیش‌نمایش آگهی:\n\n" + text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ ارسال برای بررسی", callback_data="__submit")],
            [InlineKeyboardButton("❌ لغو", callback_data="__cancel")],
        ]),
    )
    return CONFIRM


def build_ad_text(d):
    return (
        f"📍 شهر: {d.get('city','')}\n"
        f"📂 دسته: {d.get('category','')}\n"
        f"🔹 زیرمجموعه: {d.get('subcategory','')}\n\n"
        f"📌 {d.get('title','')}\n\n"
        f"📝 {d.get('description','')}\n\n"
        f"💰 قیمت: {d.get('price','')}\n"
        f"📞 تماس: {d.get('phone','')}"
    )


async def show_preview(update, context):
    d = context.user_data
    text = "👀 پیش‌نمایش آگهی:\n\n" + build_ad_text(d)
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ارسال برای بررسی", callback_data="__submit")],
        [InlineKeyboardButton("❌ لغو", callback_data="__cancel")],
    ])
    if d.get("photo_id"):
        await update.message.reply_photo(
            d["photo_id"], caption=text, reply_markup=markup
        )
    else:
        await update.message.reply_text(text, reply_markup=markup)
    return CONFIRM


async def submit_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not ADMIN_ID:
        await q.message.reply_text("⚠️ شناسه مدیر هنوز در تنظیمات ربات ثبت نشده است.")
        return ConversationHandler.END

    d = context.user_data.copy()
    d["user_id"] = update.effective_user.id
    d["username"] = update.effective_user.username or ""
    context.application.bot_data.setdefault("pending", {})
    pending = context.application.bot_data["pending"]
    ad_id = str(update.effective_user.id) + "_" + str(int(datetime.now().timestamp()))
    pending[ad_id] = d

    admin_text = "🆕 آگهی جدید برای بررسی\n\n" + build_ad_text(d)
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید انتشار", callback_data=f"approve:{ad_id}"),
            InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject:{ad_id}"),
        ]
    ])
    if d.get("photo_id"):
        await context.bot.send_photo(ADMIN_ID, d["photo_id"], caption=admin_text, reply_markup=markup)
    else:
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)

    await q.message.reply_text("✅ آگهی برای بررسی مدیر ارسال شد.")
    return ConversationHandler.END


async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        await q.answer("دسترسی ندارید.", show_alert=True)
        return

    action, ad_id = q.data.split(":", 1)
    pending = context.application.bot_data.setdefault("pending", {})
    d = pending.get(ad_id)

    if not d:
        await q.edit_message_reply_markup(reply_markup=None)
        await q.message.reply_text("⚠️ این آگهی دیگر در صف بررسی نیست.")
        return

    if action == "reject":
        pending.pop(ad_id, None)
        await q.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(d["user_id"], "❌ آگهی شما توسط مدیر رد شد.")
        return

    # approve
    post_text = (
        f"📍 {d['city']}\n"
        f"📂 {d['category']} | {d['subcategory']}\n\n"
        f"🔹 {d['title']}\n\n"
        f"📝 {d['description']}\n\n"
        f"💰 قیمت: {d['price']}\n"
        f"📞 تماس: {d['phone']}\n\n"
        f"📣 آگهی ثبت‌شده در دیوار مهرگان"
    )
    try:
        if d.get("photo_id"):
            await context.bot.send_photo(CHANNEL, d["photo_id"], caption=post_text)
        else:
            await context.bot.send_message(CHANNEL, post_text)
        await context.bot.send_message(d["user_id"], "✅ آگهی شما تأیید و در کانال منتشر شد.")
        await q.edit_message_reply_markup(reply_markup=None)
        await q.message.reply_text("✅ آگهی با موفقیت در کانال منتشر شد.")
    except Exception as e:
        logger.exception("Publish error")
        await q.message.reply_text(
            "⚠️ انتشار ناموفق بود. مطمئن شوید ربات در کانال ادمین است و اجازه ارسال پیام دارد."
        )
    finally:
        pending.pop(ad_id, None)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("❌ ثبت آگهی لغو شد. برای شروع دوباره /start را بزنید.")
    else:
        await update.message.reply_text("❌ ثبت آگهی لغو شد. برای شروع دوباره /start را بزنید.")
    return ConversationHandler.END


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY: [CallbackQueryHandler(choose_city)],
            CATEGORY: [CallbackQueryHandler(choose_category)],
            SUBCATEGORY: [CallbackQueryHandler(choose_subcategory)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_received)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_received)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_received)],
            PHOTO: [
                CallbackQueryHandler(no_photo, pattern="^__no_photo$"),
                MessageHandler(filters.PHOTO, photo_received),
            ],
            CONFIRM: [
                CallbackQueryHandler(submit_ad, pattern="^__submit$"),
                CallbackQueryHandler(cancel, pattern="^__cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_decision, pattern=r"^(approve|reject):"))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
