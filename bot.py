import os
import telebot
import requests
from telebot import types

BOT_TOKEN = "8462739141:AAFhKATM8xWk-sgbDxpNyDCdT4ZDiQOxP4E"
OWNER_ID = 8410759793
API_URL = "https://nequi-api-production-82b7.up.railway.app"

bot = telebot.TeleBot(BOT_TOKEN)
pending = {}

def fmt_balance(b):
    return f"$ {float(b):,.0f}".replace(",", ".")

def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}")
        return r.json()
    except:
        return None

def api_post(path, data):
    try:
        r = requests.post(f"{API_URL}{path}", json=data)
        return r.json()
    except:
        return None

def api_patch(path, data):
    try:
        r = requests.patch(f"{API_URL}{path}", json=data)
        return r.json()
    except:
        return None

def api_delete(path):
    try:
        r = requests.delete(f"{API_URL}{path}")
        return r.json()
    except:
        return None

def user_card(u):
    return (
        f"👤 *Información del Usuario*\n\n"
        f"💎 *Nombre:* {u['name']}\n"
        f"📱 *Teléfono:* {u['phone']}\n"
        f"🔒 *PIN:* {u['pin']}\n"
        f"💰 *Balance:* {fmt_balance(u['balance'])}\n"
    )

def user_keyboard(phone):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✏️ Editar Nombre", callback_data=f"editname_{phone}"),
        types.InlineKeyboardButton("📱 Editar Teléfono", callback_data=f"editphone_{phone}"),
    )
    kb.add(types.InlineKeyboardButton("💰 Ajustar Balance", callback_data=f"balance_{phone}"))
    kb.add(types.InlineKeyboardButton("🗑 Eliminar Usuario", callback_data=f"delete_{phone}"))
    kb.add(types.InlineKeyboardButton("« Volver", callback_data="cancel"))
    return kb

def is_admin(tid):
    r = api_get(f"/api/v2/admin/check/{tid}")
    return r and r.get("is_admin")

@bot.message_handler(commands=["start"])
def start(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ No tienes permisos.")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✨ Crear Usuario", callback_data="menu_create"),
        types.InlineKeyboardButton("🔍 Buscar Usuario", callback_data="menu_search"),
    )
    kb.add(
        types.InlineKeyboardButton("👥 Ver Usuarios", callback_data="menu_users"),
        types.InlineKeyboardButton("⚙️ Admins", callback_data="menu_admins"),
    )
    bot.send_message(msg.chat.id, "🤖 *Panel Nequi VIP*\n\nSelecciona una opción:", parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(commands=["search"])
def search_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ No tienes permisos.")
        return
    args = msg.text.split()
    if len(args) < 2:
        pending[msg.from_user.id] = {"step": "searching"}
        bot.send_message(msg.chat.id, "📱 Escribe el número de teléfono:")
        return
    r = api_get(f"/api/v2/user/{args[1]}")
    if not r or r.get("error"):
        bot.send_message(msg.chat.id, "❌ Número no registrado.")
        return
    bot.send_message(msg.chat.id, user_card(r["user"]), parse_mode="Markdown", reply_markup=user_keyboard(args[1]))

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid = c.from_user.id
    data = c.data

    if data == "menu_create":
        pending[uid] = {"step": "create", "data": {}}
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("👤 Nombre", callback_data="set_name"),
            types.InlineKeyboardButton("📱 Teléfono", callback_data="set_phone"),
        )
        kb.add(
            types.InlineKeyboardButton("🔒 PIN", callback_data="set_pin"),
            types.InlineKeyboardButton("💰 Balance", callback_data="set_balance"),
        )
        kb.add(types.InlineKeyboardButton("✅ Crear Usuario", callback_data="do_create"))
        kb.add(types.InlineKeyboardButton("❌ Cancelar", callback_data="cancel"))
        bot.edit_message_text(
            "✨ *Crear Nuevo Usuario*\n\n👤 Nombre: _No establecido_\n📱 Teléfono: _No establecido_\n🔒 PIN: _No establecido_\n💰 Balance: _$0_",
            c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=kb
        )
        return

    if data == "menu_search":
        pending[uid] = {"step": "searching"}
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "📱 Escribe el número de teléfono:")
        return

    if data == "menu_users":
        bot.answer_callback_query(c.id)
        r = api_get("/api/v2/users")
        if not r or not r.get("users"):
            bot.send_message(c.message.chat.id, "No hay usuarios registrados.")
            return
        users = r["users"]
        text = f"👥 *Usuarios ({len(users)}):*\n\n"
        for u in users:
            text += f"• {u['name']} — `{u['phone']}` — {fmt_balance(u['balance'])}\n"
        bot.send_message(c.message.chat.id, text, parse_mode="Markdown")
        return

    if data == "menu_admins":
        bot.answer_callback_query(c.id)
        r = api_get("/api/v2/admins")
        admins = r.get("admins", []) if r else []
        text = "👥 *Admins:*\n\n"
        for a in admins:
            text += f"• {a['name']} — `{a['telegram_id']}`\n"
        bot.send_message(c.message.chat.id, text, parse_mode="Markdown")
        return

    if data == "cancel":
        pending.pop(uid, None)
        bot.delete_message(c.message.chat.id, c.message.message_id)
        return

    if data in ["set_name", "set_phone", "set_pin", "set_balance"]:
        pending.setdefault(uid, {"step": "create", "data": {}})
        pending[uid]["waiting"] = data.replace("set_", "")
        bot.answer_callback_query(c.id)
        prompts = {"name": "✏️ Escribe el nombre:", "phone": "📱 Escribe el teléfono:", "pin": "🔒 Escribe el PIN:", "balance": "💰 Escribe el balance:"}
        bot.send_message(c.message.chat.id, prompts[data.replace("set_", "")])
        return

    if data == "do_create":
        p = pending.get(uid, {})
        d = p.get("data", {})
        if not d.get("name") or not d.get("phone") or not d.get("pin"):
            bot.answer_callback_query(c.id, "⚠️ Completa nombre, teléfono y PIN.", show_alert=True)
            return
        balance = float(d.get("balance", 0))
        r = api_post("/api/v2/auth/register", {"phone": d["phone"], "name": d["name"], "pin": d["pin"]})
        if r and r.get("success"):
            if balance > 0:
                api_post(f"/api/v2/admin/balance/{d['phone']}", {"balance": balance})
            bot.answer_callback_query(c.id)
            bot.edit_message_text(
                f"✅ *Usuario creado*\n\n👤 {d['name']}\n📱 {d['phone']}\n🔒 {d['pin']}\n💰 {fmt_balance(balance)}",
                c.message.chat.id, c.message.message_id, parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(c.id, "❌ El teléfono ya está registrado.", show_alert=True)
        pending.pop(uid, None)
        return

    if data.startswith("editname_"):
        phone = data.split("_", 1)[1]
        pending[uid] = {"step": "editname", "phone": phone}
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "✏️ Escribe el nuevo nombre:")
        return

    if data.startswith("editphone_"):
        phone = data.split("_", 1)[1]
        pending[uid] = {"step": "editphone", "phone": phone}
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "📱 Escribe el nuevo teléfono:")
        return

    if data.startswith("balance_"):
        phone = data.split("_", 1)[1]
        pending[uid] = {"step": "balance", "phone": phone}
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "💰 Escribe el nuevo balance:")
        return

    if data.startswith("delete_"):
        phone = data.split("_", 1)[1]
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Confirmar", callback_data=f"confirmdelete_{phone}"),
            types.InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
        )
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, f"⚠️ ¿Eliminar usuario `{phone}`?", parse_mode="Markdown", reply_markup=kb)
        return

    if data.startswith("confirmdelete_"):
        phone = data.split("_", 1)[1]
        api_delete(f"/api/v2/user/{phone}")
        bot.answer_callback_query(c.id)
        bot.edit_message_text(f"✅ Usuario `{phone}` eliminado.", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        return

@bot.message_handler(func=lambda m: m.from_user.id in pending)
def handle_input(msg):
    uid = msg.from_user.id
    p = pending.get(uid, {})
    text = msg.text.strip()

    if p.get("step") == "searching":
        r = api_get(f"/api/v2/user/{text}")
        if not r or r.get("error"):
            bot.send_message(msg.chat.id, "❌ Número no registrado.")
        else:
            bot.send_message(msg.chat.id, user_card(r["user"]), parse_mode="Markdown", reply_markup=user_keyboard(text))
        pending.pop(uid, None)
        return

    waiting = p.get("waiting")
    if waiting:
        if waiting == "balance":
            try:
                p.setdefault("data", {})["balance"] = float(text.replace(".", "").replace(",", "."))
            except:
                p.setdefault("data", {})["balance"] = 0
        else:
            p.setdefault("data", {})[waiting] = text
        p.pop("waiting")
        bot.send_message(msg.chat.id, f"✅ {waiting.capitalize()}: {text}")
        return

    if p.get("step") == "editname":
        api_patch(f"/api/v2/user/{p['phone']}/name", {"name": text})
        pending.pop(uid, None)
        bot.send_message(msg.chat.id, f"✅ Nombre actualizado: {text}")
    elif p.get("step") == "editphone":
        r = api_patch(f"/api/v2/user/{p['phone']}/phone", {"phone": text})
        if r and r.get("success"):
            bot.send_message(msg.chat.id, f"✅ Teléfono actualizado: {text}")
        else:
            bot.send_message(msg.chat.id, "❌ Ese teléfono ya está en uso.")
        pending.pop(uid, None)
    elif p.get("step") == "balance":
        try:
            bal = float(text.replace(".", "").replace(",", "."))
        except:
            bal = 0
        api_post(f"/api/v2/admin/balance/{p['phone']}", {"balance": bal})
        pending.pop(uid, None)
        bot.send_message(msg.chat.id, f"✅ Balance actualizado: {fmt_balance(bal)}")

if __name__ == "__main__":
    print("🤖 Bot Nequi VIP iniciado...")
    bot.infinity_polling()
