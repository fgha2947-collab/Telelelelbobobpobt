# -*- coding: utf-8 -*-
# نسخة Render – لا تحتاج إلى Flask أو ngrok، تعمل 24/7

import asyncio
import edge_tts
import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===================== تكوينات =====================
BOT_TOKEN = '8790288252:AAE-oblZVJF2AagL0hqJ5-TpI_ZMbkEQzV4'
ADMIN_ID = 2079792781
FORCE_SUB_CHANNEL_DEFAULT = ""
# =================================================

DATA_FILE = "bot_data.json"

def load_data():
    default = {
        "users": {}, "total_conversions": 0, "total_chars": 0,
        "force_sub_enabled": bool(FORCE_SUB_CHANNEL_DEFAULT != ""),
        "force_sub_channel": FORCE_SUB_CHANNEL_DEFAULT,
        "premium_enabled": False, "premium_users": [],
        "earnings": {"donation_link": "", "ad_message": "", "premium_price": "5$ شهرياً"},
        "admin_settings": {"notify_start": True, "notify_block": True, "notify_conversion": True}
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            for k, v in default.items():
                if k not in loaded:
                    loaded[k] = v
            return loaded
    return default

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ------------------- قائمة الأصوات -------------------
VOICE_OPTIONS_FREE = {
    "العربية": [("ذكر (مصري)", "ar-EG-ShakirNeural"), ("أنثى (مصرية)", "ar-EG-SalmaNeural")],
    "English (US)": [("Male (Guy)", "en-US-GuyNeural"), ("Female (Jenny)", "en-US-JennyNeural")],
    "French": [("Male (Henri)", "fr-FR-HenriNeural"), ("Female (Denise)", "fr-FR-DeniseNeural")],
    "Turkish": [("Male (Ahmet)", "tr-TR-AhmetNeural"), ("Female (Emel)", "tr-TR-EmelNeural")]
}
VOICE_OPTIONS_PREMIUM_ONLY = {
    "العربية (إضافي)": [("ذكر (سعودي)", "ar-SA-HamedNeural"), ("أنثى (سعودية)", "ar-SA-ZariyahNeural")],
    "English (UK)": [("Male (Ryan)", "en-GB-RyanNeural"), ("Female (Sonia)", "en-GB-SoniaNeural")],
    "German": [("Male (Conrad)", "de-DE-ConradNeural"), ("Female (Katja)", "de-DE-KatjaNeural")],
    "Spanish": [("Male (Alvaro)", "es-ES-AlvaroNeural"), ("Female (Elvira)", "es-ES-ElviraNeural")]
}

def get_voice_options_for_user(user_id):
    if not data["premium_enabled"]:
        all_voices = dict(VOICE_OPTIONS_FREE)
        for lang, voices in VOICE_OPTIONS_PREMIUM_ONLY.items():
            all_voices[lang] = all_voices.get(lang, []) + voices
        return all_voices
    else:
        if str(user_id) in data["premium_users"]:
            all_voices = dict(VOICE_OPTIONS_FREE)
            for lang, voices in VOICE_OPTIONS_PREMIUM_ONLY.items():
                all_voices[lang] = all_voices.get(lang, []) + voices
            return all_voices
        else:
            return VOICE_OPTIONS_FREE

def is_premium_user(user_id):
    return data["premium_enabled"] and (str(user_id) in data["premium_users"])

def get_voice_code_to_name(user_id):
    mapping = {}
    for lang, items in get_voice_options_for_user(user_id).items():
        for name, code in items:
            mapping[code] = f"{lang} - {name}"
    return mapping

SUPPORTED_INTERFACE_LANGS = {"ar": "العربية", "en": "English"}

TEXTS = {
    "ar": {
        "main_title": "🎙️ **لوحة التحكم**",
        "current_voice": "الصوت الحالي",
        "speed": "السرعة",
        "pitch": "طبقة الصوت",
        "volume": "مستوى الصوت",
        "btn_change_voice": "🎤 تغيير الصوت",
        "btn_rate": "🎚️ السرعة: {}",
        "btn_pitch": "🎵 طبقة الصوت: {}",
        "btn_volume": "🔊 مستوى الصوت: {}",
        "btn_convert": "📝 تحويل نص",
        "btn_help": "❓ مساعدة",
        "btn_interface_lang": "🌍 تغيير لغة البوت",
        "enter_text": "✏️ أرسل النص",
        "converting": "⏳ جاري التحويل...",
        "success": "✅ تم التحويل",
        "error": "❌ خطأ: {}",
        "text_too_long": "النص طويل جداً",
        "help_text": "🎧 *كيفية الاستخدام:*\n- اختر الصوت\n- اضبط السرعة والطبقة\n- أرسل النص\n- /start للقائمة",
        "select_voice_lang": "🌐 اختر اللغة:",
        "select_voice": "🎤 اختر الصوت:",
        "select_interface_lang": "🌐 اختر لغة الواجهة:",
        "rate_menu_title": "⚡ السرعة (حالياً {}):",
        "pitch_menu_title": "🎼 طبقة الصوت (حالياً {}):",
        "volume_menu_title": "🔊 مستوى الصوت (حالياً {}):",
        "back": "🔙 رجوع",
        "back_to_main": "🔙 القائمة",
        "rate_changed": "السرعة: {}",
        "pitch_changed": "طبقة الصوت: {}",
        "volume_changed": "مستوى الصوت: {}",
        "voice_changed": "تم تغيير الصوت إلى {}",
        "interface_lang_changed": "تم تغيير اللغة",
        "admin_panel_title": "🔧 **لوحة الأدمن**",
        "stats": "📊 **إحصائيات**\n👥 مستخدمين: {users}\n🔄 تحويلات: {conversions}\n🔤 أحرف: {chars}\n⭐ مميزين: {premium_count}",
        "force_sub_status": "📢 الإشتراك الإجباري: {status}\nالقناة: {channel}",
        "earnings_menu": "💰 **الربح**\n🔗 تبرع: {donation}\n📢 إعلان: {ad}\n💎 سعر البريميوم: {price}",
        "btn_stats": "📊 إحصائيات",
        "btn_force_sub": "📢 إشتراك إجباري",
        "btn_earnings": "💰 الربح",
        "btn_premium_system": "⭐ البريميوم",
        "btn_broadcast": "📢 بث",
        "btn_back_admin": "🔙 رجوع",
        "enter_broadcast": "✏️ أرسل رسالة البث:",
        "broadcast_sent": "✅ تم البث لـ {count} مستخدم",
        "force_sub_toggle": "🔁 تفعيل/تعطيل",
        "force_sub_set": "✏️ تغيير القناة",
        "force_sub_changed": "✅ تم تغيير القناة",
        "force_sub_required": "⚠️ اشترك في القناة أولاً",
        "premium_status": "⭐ **البريميوم**\nالحالة: {enabled}\nنوعك: {type}\nالسعر: {price}",
        "premium_not_active": "نظام البريميوم معطل",
        "premium_already": "أنت مميز ✅",
        "premium_not": "أنت غير مميز",
        "admin_premium_panel": "⭐ **إدارة البريميوم**\nالحالة: {status}\nعدد المميزين: {count}\nالسعر: {price}",
        "btn_toggle_premium": "🔁 تفعيل/تعطيل النظام",
        "btn_list_premium": "📋 قائمة المميزين",
        "btn_add_premium": "➕ إضافة مميز",
        "btn_remove_premium": "➖ إزالة مميز",
        "enter_user_id_to_add": "✏️ أرسل معرف المستخدم",
        "enter_user_id_to_remove": "✏️ أرسل معرف المستخدم",
        "user_added_premium": "✅ المستخدم {uid} أصبح مميزاً",
        "user_removed_premium": "✅ المستخدم {uid} لم يعد مميزاً",
        "invalid_user_id": "⚠️ معرف غير صالح",
        "premium_users_list": "⭐ **المميزين**\n{list}\nالإجمالي: {count}",
        "no_premium_users": "لا يوجد مميزين",
        "premium_price_updated": "✅ تم تحديث السعر",
        "donation_updated": "✅ تم تحديث رابط التبرع",
        "ad_updated": "✅ تم تحديث رسالة الإعلان"
    },
    "en": {
        "main_title": "🎙️ **Control Panel**",
        "current_voice": "Current voice",
        "speed": "Speed",
        "pitch": "Pitch",
        "volume": "Volume",
        "btn_change_voice": "🎤 Change voice",
        "btn_rate": "🎚️ Speed: {}",
        "btn_pitch": "🎵 Pitch: {}",
        "btn_volume": "🔊 Volume: {}",
        "btn_convert": "📝 Convert",
        "btn_help": "❓ Help",
        "btn_interface_lang": "🌍 Language",
        "enter_text": "✏️ Send text",
        "converting": "⏳ Converting...",
        "success": "✅ Success",
        "error": "❌ Error: {}",
        "text_too_long": "Text too long",
        "help_text": "🎧 *How to use:*\n- Choose voice\n- Adjust speed/pitch\n- Send text",
        "select_voice_lang": "🌐 Choose language:",
        "select_voice": "🎤 Choose voice:",
        "select_interface_lang": "🌐 Choose language:",
        "rate_menu_title": "⚡ Speed (current {}):",
        "pitch_menu_title": "🎼 Pitch (current {}):",
        "volume_menu_title": "🔊 Volume (current {}):",
        "back": "🔙 Back",
        "back_to_main": "🔙 Main",
        "rate_changed": "Speed: {}",
        "pitch_changed": "Pitch: {}",
        "volume_changed": "Volume: {}",
        "voice_changed": "Voice changed",
        "interface_lang_changed": "Language changed",
        "admin_panel_title": "🔧 **Admin Panel**",
        "stats": "📊 **Stats**\n👥 Users: {users}\n🔄 Conversions: {conversions}\n🔤 Chars: {chars}\n⭐ Premium: {premium_count}",
        "force_sub_status": "📢 Force Subscribe: {status}\nChannel: {channel}",
        "earnings_menu": "💰 **Earnings**\n🔗 Donation: {donation}\n📢 Ad: {ad}\n💎 Price: {price}",
        "btn_stats": "📊 Stats",
        "btn_force_sub": "📢 Force Sub",
        "btn_earnings": "💰 Earnings",
        "btn_premium_system": "⭐ Premium",
        "btn_broadcast": "📢 Broadcast",
        "btn_back_admin": "🔙 Back",
        "enter_broadcast": "✏️ Send broadcast:",
        "broadcast_sent": "✅ Sent to {count} users",
        "force_sub_toggle": "🔁 Toggle",
        "force_sub_set": "✏️ Change channel",
        "force_sub_changed": "✅ Channel changed",
        "force_sub_required": "⚠️ Subscribe first",
        "premium_status": "⭐ **Premium**\nStatus: {enabled}\nYou are: {type}\nPrice: {price}",
        "premium_not_active": "Premium disabled",
        "premium_already": "You are premium ✅",
        "premium_not": "Not premium",
        "admin_premium_panel": "⭐ **Premium Mgmt**\nStatus: {status}\nCount: {count}\nPrice: {price}",
        "btn_toggle_premium": "🔁 Toggle",
        "btn_list_premium": "📋 List",
        "btn_add_premium": "➕ Add",
        "btn_remove_premium": "➖ Remove",
        "enter_user_id_to_add": "✏️ Send user ID",
        "enter_user_id_to_remove": "✏️ Send user ID",
        "user_added_premium": "✅ User {uid} is premium",
        "user_removed_premium": "✅ User {uid} removed",
        "invalid_user_id": "⚠️ Invalid ID",
        "premium_users_list": "⭐ **Premium Users**\n{list}\nTotal: {count}",
        "no_premium_users": "No premium users",
        "premium_price_updated": "✅ Price updated",
        "donation_updated": "✅ Donation link updated",
        "ad_updated": "✅ Ad updated"
    }
}

def get_text(user_id, key, **kwargs):
    lang = data["users"].get(str(user_id), {}).get("lang", "ar")
    if lang not in TEXTS:
        lang = "ar"
    text = TEXTS[lang].get(key, TEXTS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text

def save_user_settings(user_id, key, value):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {"first_name": "Unknown", "join_date": time.time(), "blocked": False, "lang": "ar",
                              "voice_code": "ar-EG-SalmaNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}
    data["users"][uid][key] = value
    save_data(data)

def get_user_setting(user_id, key, default=None):
    return data["users"].get(str(user_id), {}).get(key, default)

def detect_interface_lang(telegram_lang_code):
    if not telegram_lang_code:
        return "ar"
    lang = telegram_lang_code.split("-")[0].lower()
    return lang if lang in SUPPORTED_INTERFACE_LANGS else "ar"

async def is_forced_subscribed(user_id, context):
    if not data["force_sub_enabled"] or not data["force_sub_channel"]:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=data["force_sub_channel"], user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ------------------- دوال الواجهة -------------------
def main_menu(user_id):
    voice_code = get_user_setting(user_id, "voice_code", "ar-EG-SalmaNeural")
    voice_name = get_voice_code_to_name(user_id).get(voice_code, voice_code)
    rate = get_user_setting(user_id, "rate", "+0%")
    pitch = get_user_setting(user_id, "pitch", "+0Hz")
    volume = get_user_setting(user_id, "volume", "+0%")
    text = f"{get_text(user_id, 'main_title')}\n\n🗣️ {get_text(user_id, 'current_voice')}: {voice_name}\n🎚️ {get_text(user_id, 'speed')}: {rate}\n🎵 {get_text(user_id, 'pitch')}: {pitch}\n🔊 {get_text(user_id, 'volume')}: {volume}\n\n✏️ {get_text(user_id, 'enter_text')}"
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, "btn_change_voice"), callback_data="change_voice")],
        [InlineKeyboardButton(get_text(user_id, "btn_rate").format(rate), callback_data="rate"), InlineKeyboardButton(get_text(user_id, "btn_pitch").format(pitch), callback_data="pitch")],
        [InlineKeyboardButton(get_text(user_id, "btn_volume").format(volume), callback_data="volume")],
        [InlineKeyboardButton(get_text(user_id, "btn_convert"), callback_data="convert_now")],
        [InlineKeyboardButton(get_text(user_id, "btn_interface_lang"), callback_data="change_interface_lang")],
        [InlineKeyboardButton(get_text(user_id, "btn_help"), callback_data="help")],
    ]
    return text, InlineKeyboardMarkup(keyboard)

async def voice_lang_menu(update, query, user_id):
    voices = get_voice_options_for_user(user_id)
    keyboard = [[InlineKeyboardButton(lang, callback_data=f"vlang_{lang}")] for lang in voices.keys()]
    keyboard.append([InlineKeyboardButton(get_text(user_id, "back"), callback_data="main")])
    await query.edit_message_text(get_text(user_id, "select_voice_lang"), reply_markup=InlineKeyboardMarkup(keyboard))

async def voice_select_menu(update, query, user_id, lang):
    voices = get_voice_options_for_user(user_id)
    items = voices.get(lang, [])
    keyboard = [[InlineKeyboardButton(name, callback_data=f"setvoice_{code}")] for name, code in items]
    keyboard.append([InlineKeyboardButton(get_text(user_id, "back"), callback_data="change_voice")])
    await query.edit_message_text(f"{get_text(user_id, 'select_voice')} ({lang})", reply_markup=InlineKeyboardMarkup(keyboard))

async def rate_menu(update, query, user_id):
    current = get_user_setting(user_id, "rate", "+0%")
    keyboard = [[InlineKeyboardButton("-30%", "rate_-30%"), InlineKeyboardButton("-20%", "rate_-20%"), InlineKeyboardButton("-10%", "rate_-10%")],
                [InlineKeyboardButton("+0%", "rate_+0%")],
                [InlineKeyboardButton("+10%", "rate_+10%"), InlineKeyboardButton("+20%", "rate_+20%"), InlineKeyboardButton("+30%", "rate_+30%")],
                [InlineKeyboardButton(get_text(user_id, "back"), "main")]]
    await query.edit_message_text(get_text(user_id, "rate_menu_title").format(current), reply_markup=InlineKeyboardMarkup(keyboard))

async def pitch_menu(update, query, user_id):
    current = get_user_setting(user_id, "pitch", "+0Hz")
    keyboard = [[InlineKeyboardButton("-20Hz", "pitch_-20Hz"), InlineKeyboardButton("-10Hz", "pitch_-10Hz"), InlineKeyboardButton("-5Hz", "pitch_-5Hz")],
                [InlineKeyboardButton("+0Hz", "pitch_+0Hz")],
                [InlineKeyboardButton("+5Hz", "pitch_+5Hz"), InlineKeyboardButton("+10Hz", "pitch_+10Hz"), InlineKeyboardButton("+20Hz", "pitch_+20Hz")],
                [InlineKeyboardButton(get_text(user_id, "back"), "main")]]
    await query.edit_message_text(get_text(user_id, "pitch_menu_title").format(current), reply_markup=InlineKeyboardMarkup(keyboard))

async def volume_menu(update, query, user_id):
    current = get_user_setting(user_id, "volume", "+0%")
    keyboard = [[InlineKeyboardButton("-50%", "volume_-50%"), InlineKeyboardButton("-20%", "volume_-20%"), InlineKeyboardButton("-10%", "volume_-10%")],
                [InlineKeyboardButton("+0%", "volume_+0%")],
                [InlineKeyboardButton("+10%", "volume_+10%"), InlineKeyboardButton("+20%", "volume_+20%"), InlineKeyboardButton("+50%", "volume_+50%")],
                [InlineKeyboardButton(get_text(user_id, "back"), "main")]]
    await query.edit_message_text(get_text(user_id, "volume_menu_title").format(current), reply_markup=InlineKeyboardMarkup(keyboard))

# ------------------- دوال الأدمن -------------------
async def admin_panel(update, query=None):
    if (query and query.from_user.id != ADMIN_ID) or (not query and update.effective_user.id != ADMIN_ID):
        return
    keyboard = [
        [InlineKeyboardButton(get_text(ADMIN_ID, "btn_stats"), callback_data="admin_stats")],
        [InlineKeyboardButton(get_text(ADMIN_ID, "btn_force_sub"), callback_data="admin_force_sub")],
        [InlineKeyboardButton(get_text(ADMIN_ID, "btn_earnings"), callback_data="admin_earnings")],
        [InlineKeyboardButton(get_text(ADMIN_ID, "btn_premium_system"), callback_data="admin_premium_system")],
        [InlineKeyboardButton(get_text(ADMIN_ID, "btn_broadcast"), callback_data="admin_broadcast")],
        [InlineKeyboardButton(get_text(ADMIN_ID, "btn_back_main"), callback_data="main")],
    ]
    text = get_text(ADMIN_ID, "admin_panel_title")
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_stats(update, query=None):
    users = len(data["users"])
    blocked = sum(1 for u in data["users"].values() if u.get("blocked"))
    premium = len(data["premium_users"])
    text = get_text(ADMIN_ID, "stats", users=users, conversions=data["total_conversions"], chars=data["total_chars"], premium_count=premium)
    kb = [[InlineKeyboardButton(get_text(ADMIN_ID, "btn_back_admin"), callback_data="admin_panel")]]
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def admin_force_sub_menu(update, query=None):
    status = "✅ مفعل" if data["force_sub_enabled"] else "❌ معطل"
    text = get_text(ADMIN_ID, "force_sub_status", status=status, channel=data["force_sub_channel"])
    kb = [[InlineKeyboardButton(get_text(ADMIN_ID, "force_sub_toggle"), callback_data="force_sub_toggle")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "force_sub_set"), callback_data="force_sub_set")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "btn_back_admin"), callback_data="admin_panel")]]
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def admin_earnings_menu(update, query=None):
    donation = data["earnings"].get("donation_link", "")
    ad = data["earnings"].get("ad_message", "")
    price = data["earnings"].get("premium_price", "5$")
    text = get_text(ADMIN_ID, "earnings_menu", donation=donation, ad=ad, price=price)
    kb = [[InlineKeyboardButton("💸 تعديل التبرع", callback_data="set_donation")],
          [InlineKeyboardButton("📢 تعديل الإعلان", callback_data="set_ad")],
          [InlineKeyboardButton("💎 تعديل سعر البريميوم", callback_data="set_premium_price")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "btn_back_admin"), callback_data="admin_panel")]]
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def admin_premium_panel(update, query=None):
    status = "✅ مفعل" if data["premium_enabled"] else "❌ معطل"
    text = get_text(ADMIN_ID, "admin_premium_panel", status=status, count=len(data["premium_users"]), price=data["earnings"].get("premium_price", "5$"))
    kb = [[InlineKeyboardButton(get_text(ADMIN_ID, "btn_toggle_premium"), callback_data="toggle_premium_system")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "btn_list_premium"), callback_data="list_premium_users")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "btn_add_premium"), callback_data="add_premium_user")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "btn_remove_premium"), callback_data="remove_premium_user")],
          [InlineKeyboardButton(get_text(ADMIN_ID, "btn_back_admin"), callback_data="admin_panel")]]
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def list_premium_users(update, query=None):
    if not data["premium_users"]:
        text = get_text(ADMIN_ID, "no_premium_users")
    else:
        lst = []
        for uid in data["premium_users"]:
            name = data["users"].get(uid, {}).get("first_name", "مجهول")
            lst.append(f"• `{uid}` - {name}")
        text = get_text(ADMIN_ID, "premium_users_list", list="\n".join(lst), count=len(lst))
    kb = [[InlineKeyboardButton(get_text(ADMIN_ID, "btn_back_admin"), callback_data="admin_premium_system")]]
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ------------------- تحويل النص -------------------
async def text_to_audio(text, user_id):
    voice = get_user_setting(user_id, "voice_code", "ar-EG-SalmaNeural")
    rate = get_user_setting(user_id, "rate", "+0%")
    pitch = get_user_setting(user_id, "pitch", "+0Hz")
    volume = get_user_setting(user_id, "volume", "+0%")
    out = f"speech_{user_id}.mp3"
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
    await com.save(out)
    return out

# ------------------- معالج الأزرار -------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_cb = query.data
    user_id = query.from_user.id
    await query.answer()

    if str(user_id) not in data["users"]:
        lang = detect_interface_lang(query.from_user.language_code)
        data["users"][str(user_id)] = {"first_name": query.from_user.first_name, "join_date": time.time(), "blocked": False, "lang": lang,
                                       "voice_code": "ar-EG-SalmaNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}
        save_data(data)
        if user_id != ADMIN_ID and data["admin_settings"]["notify_start"]:
            await context.bot.send_message(ADMIN_ID, get_text(ADMIN_ID, "start_notify", name=query.from_user.first_name))

    # أوامر الأدمن
    if user_id == ADMIN_ID and data_cb.startswith("admin_"):
        if data_cb == "admin_stats":
            await admin_stats(update, query)
        elif data_cb == "admin_force_sub":
            await admin_force_sub_menu(update, query)
        elif data_cb == "admin_earnings":
            await admin_earnings_menu(update, query)
        elif data_cb == "admin_premium_system":
            await admin_premium_panel(update, query)
        elif data_cb == "admin_broadcast":
            context.user_data["broadcast_mode"] = True
            await query.edit_message_text(get_text(ADMIN_ID, "enter_broadcast"))
        elif data_cb == "admin_panel":
            await admin_panel(update, query)
        return

    if user_id == ADMIN_ID and data_cb in ["force_sub_toggle", "force_sub_set", "set_donation", "set_ad", "set_premium_price",
                                           "toggle_premium_system", "list_premium_users", "add_premium_user", "remove_premium_user"]:
        if data_cb == "force_sub_toggle":
            data["force_sub_enabled"] = not data["force_sub_enabled"]
            save_data(data)
            await admin_force_sub_menu(update, query)
        elif data_cb == "force_sub_set":
            context.user_data["awaiting_channel"] = True
            await query.edit_message_text(get_text(ADMIN_ID, "force_sub_set"))
        elif data_cb == "set_donation":
            context.user_data["awaiting_donation"] = True
            await query.edit_message_text("أرسل رابط التبرع الجديد:")
        elif data_cb == "set_ad":
            context.user_data["awaiting_ad"] = True
            await query.edit_message_text("أرسل رسالة الإعلان الجديدة:")
        elif data_cb == "set_premium_price":
            context.user_data["awaiting_premium_price"] = True
            await query.edit_message_text("أرسل سعر البريميوم الجديد:")
        elif data_cb == "toggle_premium_system":
            data["premium_enabled"] = not data["premium_enabled"]
            save_data(data)
            await admin_premium_panel(update, query)
        elif data_cb == "list_premium_users":
            await list_premium_users(update, query)
        elif data_cb == "add_premium_user":
            context.user_data["awaiting_add_premium"] = True
            await query.edit_message_text(get_text(ADMIN_ID, "enter_user_id_to_add"))
        elif data_cb == "remove_premium_user":
            context.user_data["awaiting_remove_premium"] = True
            await query.edit_message_text(get_text(ADMIN_ID, "enter_user_id_to_remove"))
        return

    # أزرار المستخدم العادي
    if data_cb == "main":
        text, kb = main_menu(user_id)
        await query.edit_message_text(text, reply_markup=kb, parse_mode='Markdown')
    elif data_cb == "change_voice":
        await voice_lang_menu(update, query, user_id)
    elif data_cb.startswith("vlang_"):
        lang = data_cb.split("_", 1)[1]
        await voice_select_menu(update, query, user_id, lang)
    elif data_cb.startswith("setvoice_"):
        code = data_cb.split("_", 1)[1]
        save_user_settings(user_id, "voice_code", code)
        name = get_voice_code_to_name(user_id).get(code, code)
        await query.answer(get_text(user_id, "voice_changed").format(name))
        text, kb = main_menu(user_id)
        await query.edit_message_text(text, reply_markup=kb, parse_mode='Markdown')
    elif data_cb == "rate":
        await rate_menu(update, query, user_id)
    elif data_cb.startswith("rate_"):
        val = data_cb.split("_")[1]
        save_user_settings(user_id, "rate", val)
        await rate_menu(update, query, user_id)
    elif data_cb == "pitch":
        await pitch_menu(update, query, user_id)
    elif data_cb.startswith("pitch_"):
        val = data_cb.split("_")[1]
        save_user_settings(user_id, "pitch", val)
        await pitch_menu(update, query, user_id)
    elif data_cb == "volume":
        await volume_menu(update, query, user_id)
    elif data_cb.startswith("volume_"):
        val = data_cb.split("_")[1]
        save_user_settings(user_id, "volume", val)
        await volume_menu(update, query, user_id)
    elif data_cb == "change_interface_lang":
        kb = [[InlineKeyboardButton(name, callback_data=f"set_interface_lang_{code}")] for code, name in SUPPORTED_INTERFACE_LANGS.items()]
        kb.append([InlineKeyboardButton(get_text(user_id, "back"), callback_data="main")])
        await query.edit_message_text(get_text(user_id, "select_interface_lang"), reply_markup=InlineKeyboardMarkup(kb))
    elif data_cb.startswith("set_interface_lang_"):
        new = data_cb.split("_")[-1]
        save_user_settings(user_id, "lang", new)
        await query.answer(get_text(user_id, "interface_lang_changed"))
        text, kb = main_menu(user_id)
        await query.edit_message_text(text, reply_markup=kb, parse_mode='Markdown')
    elif data_cb == "convert_now":
        await query.edit_message_text(get_text(user_id, "enter_text"))
        context.user_data["awaiting_text"] = True
    elif data_cb == "help":
        help_text = get_text(user_id, "help_text")
        kb = [[InlineKeyboardButton(get_text(user_id, "back_to_main"), callback_data="main")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ------------------- معالج الرسائل -------------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not await is_forced_subscribed(user_id, context):
        await update.message.reply_text(get_text(user_id, "force_sub_required"))
        return

    if str(user_id) not in data["users"]:
        lang = detect_interface_lang(update.effective_user.language_code)
        data["users"][str(user_id)] = {"first_name": update.effective_user.first_name, "join_date": time.time(), "blocked": False, "lang": lang,
                                       "voice_code": "ar-EG-SalmaNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}
        save_data(data)
        if user_id != ADMIN_ID and data["admin_settings"]["notify_start"]:
            await context.bot.send_message(ADMIN_ID, get_text(ADMIN_ID, "start_notify", name=update.effective_user.first_name))

    # أوامر الأدمن النصية
    if user_id == ADMIN_ID:
        if context.user_data.get("broadcast_mode"):
            del context.user_data["broadcast_mode"]
            count = 0
            for uid, uinfo in data["users"].items():
                if not uinfo.get("blocked"):
                    try:
                        await update.message.copy(chat_id=int(uid))
                        count += 1
                        await asyncio.sleep(0.05)
                    except:
                        pass
            await update.message.reply_text(get_text(ADMIN_ID, "broadcast_sent", count=count))
            return
        if context.user_data.get("awaiting_channel"):
            del context.user_data["awaiting_channel"]
            data["force_sub_channel"] = text.strip()
            save_data(data)
            await update.message.reply_text(get_text(ADMIN_ID, "force_sub_changed"))
            return
        if context.user_data.get("awaiting_donation"):
            del context.user_data["awaiting_donation"]
            data["earnings"]["donation_link"] = text.strip()
            save_data(data)
            await update.message.reply_text(get_text(ADMIN_ID, "donation_updated"))
            return
        if context.user_data.get("awaiting_ad"):
            del context.user_data["awaiting_ad"]
            data["earnings"]["ad_message"] = text.strip()
            save_data(data)
            await update.message.reply_text(get_text(ADMIN_ID, "ad_updated"))
            return
        if context.user_data.get("awaiting_premium_price"):
            del context.user_data["awaiting_premium_price"]
            data["earnings"]["premium_price"] = text.strip()
            save_data(data)
            await update.message.reply_text(get_text(ADMIN_ID, "premium_price_updated"))
            return
        if context.user_data.get("awaiting_add_premium"):
            del context.user_data["awaiting_add_premium"]
            try:
                uid = int(text.strip())
                if str(uid) not in data["users"]:
                    await update.message.reply_text(get_text(ADMIN_ID, "invalid_user_id"))
                    return
                if str(uid) not in data["premium_users"]:
                    data["premium_users"].append(str(uid))
                    save_data(data)
                    await update.message.reply_text(get_text(ADMIN_ID, "user_added_premium", uid=uid))
                else:
                    await update.message.reply_text("المستخدم مميز بالفعل")
            except:
                await update.message.reply_text(get_text(ADMIN_ID, "invalid_user_id"))
            return
        if context.user_data.get("awaiting_remove_premium"):
            del context.user_data["awaiting_remove_premium"]
            try:
                uid = int(text.strip())
                if str(uid) in data["premium_users"]:
                    data["premium_users"].remove(str(uid))
                    save_data(data)
                    await update.message.reply_text(get_text(ADMIN_ID, "user_removed_premium", uid=uid))
                else:
                    await update.message.reply_text("المستخدم ليس مميزاً")
            except:
                await update.message.reply_text(get_text(ADMIN_ID, "invalid_user_id"))
            return

    # تحويل النص
    if context.user_data.get("awaiting_text"):
        del context.user_data["awaiting_text"]
        await update.message.reply_text(get_text(user_id, "converting"))
        try:
            audio = await text_to_audio(text, user_id)
            with open(audio, 'rb') as f:
                await update.message.reply_audio(audio=f, title="Audio", caption=get_text(user_id, "success"))
            os.remove(audio)
            data["total_conversions"] += 1
            data["total_chars"] += len(text)
            save_data(data)
            if user_id != ADMIN_ID and data["admin_settings"]["notify_conversion"]:
                await context.bot.send_message(ADMIN_ID, get_text(ADMIN_ID, "conversion_notify", name=update.effective_user.first_name, chars=len(text)))
            ad = data["earnings"].get("ad_message")
            if ad and not is_premium_user(user_id):
                await update.message.reply_text(ad)
        except Exception as e:
            await update.message.reply_text(get_text(user_id, "error").format(str(e)))
        return

    if len(text) < 1000:
        await update.message.reply_text(get_text(user_id, "converting"))
        try:
            audio = await text_to_audio(text, user_id)
            with open(audio, 'rb') as f:
                await update.message.reply_audio(audio=f, title="Audio", caption=get_text(user_id, "success"))
            os.remove(audio)
            data["total_conversions"] += 1
            data["total_chars"] += len(text)
            save_data(data)
            if user_id != ADMIN_ID and data["admin_settings"]["notify_conversion"]:
                await context.bot.send_message(ADMIN_ID, get_text(ADMIN_ID, "conversion_notify", name=update.effective_user.first_name, chars=len(text)))
            ad = data["earnings"].get("ad_message")
            if ad and not is_premium_user(user_id):
                await update.message.reply_text(ad)
        except Exception as e:
            await update.message.reply_text(get_text(user_id, "error").format(str(e)))
    else:
        await update.message.reply_text(get_text(user_id, "text_too_long"))

# ------------------- أوامر البوت -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_forced_subscribed(user_id, context):
        await update.message.reply_text(get_text(user_id, "force_sub_required"))
        return
    if str(user_id) not in data["users"]:
        lang = detect_interface_lang(update.effective_user.language_code)
        data["users"][str(user_id)] = {"first_name": update.effective_user.first_name, "join_date": time.time(), "blocked": False, "lang": lang,
                                       "voice_code": "ar-EG-SalmaNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}
        save_data(data)
        if user_id != ADMIN_ID and data["admin_settings"]["notify_start"]:
            await context.bot.send_message(ADMIN_ID, get_text(ADMIN_ID, "start_notify", name=update.effective_user.first_name))
    text, kb = main_menu(user_id)
    await update.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await admin_panel(update)
    else:
        await update.message.reply_text("⛔ غير مصرح.")

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kb = [[InlineKeyboardButton(name, callback_data=f"set_interface_lang_{code}")] for code, name in SUPPORTED_INTERFACE_LANGS.items()]
    kb.append([InlineKeyboardButton(get_text(user_id, "back"), callback_data="main")])
    await update.message.reply_text(get_text(user_id, "select_interface_lang"), reply_markup=InlineKeyboardMarkup(kb))

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not data["premium_enabled"]:
        await update.message.reply_text(get_text(user_id, "premium_not_active"))
        return
    prem = is_premium_user(user_id)
    price = data["earnings"].get("premium_price", "5$")
    status = "✅ مفعل" if data["premium_enabled"] else "❌ معطل"
    if prem:
        extra = get_text(user_id, "premium_already")
        utype = "مميز ⭐"
    else:
        extra = get_text(user_id, "premium_not")
        utype = "عادي"
    await update.message.reply_text(get_text(user_id, "premium_status", enabled=status, type=utype, price=price))

# ------------------- تشغيل البوت -------------------
async def main():
    if BOT_TOKEN == 'ضع_توكنك_هنا' or ADMIN_ID == 123456789:
        print("❌ يرجى تعديل BOT_TOKEN و ADMIN_ID")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("premium", premium_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.bot.set_my_commands([
        BotCommand("start", "بدء البوت"),
        BotCommand("admin", "لوحة الأدمن"),
        BotCommand("language", "تغيير اللغة"),
        BotCommand("premium", "معلومات البريميوم")
    ])
    print("✅ البوت يعمل الآن على Render 24/7")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
