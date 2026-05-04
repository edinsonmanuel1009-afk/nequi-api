import os
import telebot
from telebot import types
from database import *

BOT_TOKEN = "8462739141:AAFhKATM8xWk-sgbDxpNyDCdT4ZDiQOxP4E"
OWNER_ID = 8410759793

bot = telebot.TeleBot(BOT_TOKEN)
init_db()
add_admin(OWNER_ID, "LDSDARK")

pending = {}

def fmt_balance(b):
    return f"$ {b:,.0f}".replace(",", ".")

def user_card(u):
    return (
        f"👤 *Información del Usuario*\n\n"
        f"💎 *Nombre:* {u[2]}\n"
        f"📱 *Teléfono:* {u[1]}\n"
        f"🔒 *PIN:* {u[3]}\n"
        f"💰 *Balance:* {fmt_balance(u[4])}\n"
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

@bot.message_handler(commands=["start"])
def start(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ No tienes permisos para usar este bot.")
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
    bot.send_message(msg.chat.id,
        "🤖 *Panel Nequi VIP*\n\nSelecciona una opción:",
        parse_mode="Markdown", reply_markup=kb
    )

@bot.message_handler(commands=["addadmin"])
def addadmin(msg):
    if msg.from_user.id != OWNER_ID:
        bot.send_message(msg.chat.id, "❌ Solo el owner puede añadir admins.")
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "Uso: /addadmin TELEGRAM_ID")
        return
    tid = int(args[1])
    if add_admin(tid, "Admin"):
        bot.send_message(msg.chat.id, f"✅ Admin `{tid}` añadido.", parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, "❌ Ya es admin.")

@bot.message_handler(commands=["deladmin"])
def deladmin(msg):
    if msg.from_user.id != OWNER_ID:
        bot.send_message(msg.chat.id, "❌ Solo el owner puede quitar admins.")
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "Uso: /deladmin TELEGRAM_ID")
        return
    tid = int(args[1])
    remove_admin(tid)
    bot.send_message(msg.chat.id, f"✅ Admin `{tid}` eliminado.", parse_mode="Markdown")

@bot.message_handler(commands=["create"])
def create_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ No tienes permisos.")
        return
    uid = msg.from_user.id
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
    bot.send_message(msg.chat.id,
        "✨ *Crear Nuevo Usuario*\n\n"
        "👤 Nombre: _No establecido_\n"
        "📱 Teléfono: _No establecido_\n"
        "🔒 PIN: _No establecido_\n"
        "💰 Balance: _$0_\n\n"
        "_Completa los datos y toca Crear Usuario_",
        parse_mode="Markdown", reply_markup=kb
    )

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
    user = get_user(args[1])
    if not user:
        bot.send_message(msg.chat.id, "❌ Número no registrado.")
        return
    bot.send_message(msg.chat.id, user_card(user), parse_mode="Markdown", reply_markup=user_keyboard(args[1]))

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
            "✨ *Crear Nuevo Usuario*\n\n"
            "👤 Nombre: _No establecido_\n"
            "📱 Teléfono: _No establecido_\n"
            "🔒 PIN: _No establecido_\n"
            "💰 Balance: _$0_\n\n"
            "_Completa los datos y toca Crear Usuario_",
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
        all_users = get_all_users()
        if not all_users:
            bot.send_message(c.message.chat.id, "No hay usuarios registrados.")
            return
        text = f"👥 *Usuarios ({len(all_users)}):*\n\n"
        for phone, name, balance in all_users:
            text += f"• {name} — `{phone}` — {fmt_balance(balance)}\n"
        bot.send_message(c.message.chat.id, text, parse_mode="Markdown")
        return

    if data == "menu_admins":
        bot.answer_callback_query(c.id)
        admins_list = get_admins()
        text = "👥 *Admins:*\n\n"
        for tid, name in admins_list:
            text += f"• {name} — `{tid}`\n"
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
        prompts = {
            "name": "✏️ Escribe el nombre:",
            "phone": "📱 Escribe el teléfono:",
            "pin": "🔒 Escribe el PIN (4 dígitos):",
            "balance": "💰 Escribe el balance inicial:",
        }
        bot.send_message(c.message.chat.id, prompts[data.replace("set_", "")])
        return

    if data == "do_create":
        p = pending.get(uid, {})
        d = p.get("data", {})
        if not d.get("name") or not d.get("phone") or not d.get("pin"):
            bot.answer_callback_query(c.id, "⚠️ Completa nombre, teléfono y PIN.", show_alert=True)
            return
        balance = float(d.get("balance", 0))
        if create_user(d["phone"], d["name"], d["pin"], balance):
            bot.answer_callback_query(c.id)
            bot.edit_message_text(
                f"✅ *Usuario creado exitosamente*\n\n"
                f"👤 Nombre: {d['name']}\n"
                f"📱 Teléfono: {d['phone']}\n"
                f"🔒 PIN: {d['pin']}\n"
                f"💰 Balance: {fmt_balance(balance)}",
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
        delete_user(phone)
        bot.answer_callback_query(c.id)
        bot.edit_message_text(f"✅ Usuario `{phone}` eliminado.", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        return

@bot.message_handler(func=lambda m: m.from_user.id in pending)
def handle_input(msg):
    uid = msg.from_user.id
    p = pending.get(uid, {})
    text = msg.text.strip()

    if p.get("step") == "searching":
        user = get_user(text)
        if not user:
            bot.send_message(msg.chat.id, "❌ Número no registrado.")
        else:
            bot.send_message(msg.chat.id, user_card(user), parse_mode="Markdown", reply_markup=user_keyboard(text))
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
        update_user_name(p["phone"], text)
        pending.pop(uid, None)
        bot.send_message(msg.chat.id, f"✅ Nombre actualizado: {text}")
    elif p.get("step") == "editphone":
        if update_user_phone(p["phone"], text):
            bot.send_message(msg.chat.id, f"✅ Teléfono actualizado: {text}")
        else:
            bot.send_message(msg.chat.id, "❌ Ese teléfono ya está en uso.")
        pending.pop(uid, None)
    elif p.get("step") == "balance":
        try:
            bal = float(text.replace(".", "").replace(",", "."))
        except:
            bal = 0
        update_balance(p["phone"], bal)
        pending.pop(uid, None)
        bot.send_message(msg.chat.id, f"✅ Balance actualizado: {fmt_balance(bal)}")

if __name__ == "__main__":
    print("🤖 Bot Nequi VIP iniciado...")
    bot.infinity_polling()
