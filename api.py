from flask import Flask, request, jsonify
from database import *
from database import save_token, get_phone_by_token, token_exists
import secrets

app = Flask(__name__)
init_db()

# Agregar owner como admin al iniciar
add_admin(8410759793, "LDSDARK")



def get_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None

def auth_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token()
        if not token_exists(token):
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/v2/admin/check/<int:tid>", methods=["GET"])
def check_admin(tid):
    return jsonify({"is_admin": is_admin(tid)})

@app.route("/api/v2/admins", methods=["GET"])
def list_admins():
    admins = get_admins()
    return jsonify({"admins": [{"telegram_id": a[0], "name": a[1]} for a in admins]})

@app.route("/api/v2/users", methods=["GET"])
def list_users():
    users = get_all_users()
    return jsonify({"users": [{"phone": u[0], "name": u[1], "balance": u[2]} for u in users]})

@app.route("/api/v2/user/<phone>", methods=["GET"])
def get_user_by_phone(phone):
    user = get_user(phone)
    if not user:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify({"user": {"id": user[0], "phone": user[1], "name": user[2], "pin": user[3], "balance": user[4]}})

@app.route("/api/v2/user/<phone>", methods=["DELETE"])
def delete_user_by_phone(phone):
    delete_user(phone)
    return jsonify({"success": True})

@app.route("/api/v2/user/<phone>/name", methods=["PATCH"])
def update_name_by_phone(phone):
    update_user_name(phone, request.json.get("name", ""))
    return jsonify({"success": True})

@app.route("/api/v2/user/<phone>/phone", methods=["PATCH"])
def update_phone_by_phone(phone):
    new_phone = request.json.get("phone", "")
    if update_user_phone(phone, new_phone):
        return jsonify({"success": True})
    return jsonify({"error": "Teléfono en uso"}), 400

@app.route("/api/v2/admin/balance/<phone>", methods=["POST"])
def admin_set_balance(phone):
    bal = float(request.json.get("balance", 0))
    update_balance(phone, bal)
    return jsonify({"success": True})

@app.route("/api/v2/auth/check-phone", methods=["POST"])
def check_phone():
    data = request.json
    user = get_user(data.get("phone", ""))
    return jsonify({"exists": user is not None})

@app.route("/api/v2/auth/login", methods=["POST"])
def login():
    data = request.json
    user = get_user(data.get("phone", ""))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    if user[3] != data.get("pin", ""):
        return jsonify({"error": "PIN incorrecto"}), 401
    token = secrets.token_hex(32)
    save_token(data["phone"], token)
    return jsonify({"token": token})

@app.route("/api/v2/auth/register", methods=["POST"])
def register():
    data = request.json
    if create_user(data.get("phone",""), data.get("name",""), data.get("pin",""), 0):
        return jsonify({"success": True})
    return jsonify({"error": "El teléfono ya existe"}), 400

@app.route("/api/v2/user/profile", methods=["GET"])
@auth_required
def profile():
    token = get_token()
    phone = get_phone_by_token(token)
    user = get_user(phone)
    if not user:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify({"user": {"id": user[0], "phone": user[1], "name": user[2], "balance": user[4], "accountType": "personal", "biometricLogin": False}})

@app.route("/api/v2/user/name", methods=["PATCH"])
@auth_required
def update_name():
    token = get_token()
    phone = get_phone_by_token(token)
    update_user_name(phone, request.json.get("name", ""))
    return jsonify({"success": True})

@app.route("/api/v2/user/pin", methods=["PATCH"])
@auth_required
def update_pin():
    token = get_token()
    phone = get_phone_by_token(token)
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET pin = ? WHERE phone = ?", (request.json.get("newPin"), phone))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/v2/wallet", methods=["GET"])
@auth_required
def wallet():
    token = get_token()
    phone = get_phone_by_token(token)
    user = get_user(phone)
    return jsonify({"wallet": {"balance": user[4], "transactions": []}})

@app.route("/api/v2/wallet/deposit", methods=["POST"])
@auth_required
def deposit():
    token = get_token()
    phone = get_phone_by_token(token)
    user = get_user(phone)
    update_balance(phone, user[4] + float(request.json.get("amount", 0)))
    return jsonify({"transaction": {"id": "1", "type": "deposit", "amount": request.json.get("amount")}})

@app.route("/api/v2/wallet/withdraw", methods=["POST"])
@auth_required
def withdraw():
    token = get_token()
    phone = get_phone_by_token(token)
    user = get_user(phone)
    update_balance(phone, user[4] - float(request.json.get("amount", 0)))
    return jsonify({"transaction": {"id": "1", "type": "withdraw", "amount": request.json.get("amount")}})

@app.route("/api/v2/user/biometric", methods=["PATCH"])
@auth_required
def biometric():
    return jsonify({"success": True})

@app.route("/api/v2/user/account-type", methods=["PATCH"])
@auth_required
def account_type():
    return jsonify({"success": True})

@app.route("/api/v2/wallet/transaction/<id>", methods=["GET"])
@auth_required
def get_transaction(id):
    return jsonify({"transaction": {"id": id, "type": "deposit", "amount": 0}})

@app.route("/api/v2/wallet/transfer", methods=["POST"])
@auth_required
def transfer():
    return jsonify({"transaction": {"id": "1", "type": "transfer", "amount": 0}})

@app.route("/api/v2/wallet/income", methods=["POST"])
@auth_required
def income():
    return jsonify({"transaction": {"id": "1", "type": "income", "amount": 0}})

if __name__ == "__main__":
    print("🚀 API iniciada en puerto 8000")
    app.run(host="0.0.0.0", port=8000)
