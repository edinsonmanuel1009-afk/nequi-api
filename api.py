from flask import Flask, request, jsonify
from database import *
import secrets

app = Flask(__name__)
init_db()

tokens = {}

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
        if token not in tokens.values():
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorated

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
    tokens[data["phone"]] = token
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
    phone = next((p for p, t in tokens.items() if t == token), None)
    user = get_user(phone)
    if not user:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify({"user": {"id": user[0], "phone": user[1], "name": user[2], "balance": user[4], "accountType": "personal", "biometricLogin": False}})

@app.route("/api/v2/user/name", methods=["PATCH"])
@auth_required
def update_name():
    token = get_token()
    phone = next((p for p, t in tokens.items() if t == token), None)
    update_user_name(phone, request.json.get("name", ""))
    return jsonify({"success": True})

@app.route("/api/v2/user/pin", methods=["PATCH"])
@auth_required
def update_pin():
    token = get_token()
    phone = next((p for p, t in tokens.items() if t == token), None)
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
    phone = next((p for p, t in tokens.items() if t == token), None)
    user = get_user(phone)
    return jsonify({"wallet": {"balance": user[4], "transactions": []}})

@app.route("/api/v2/wallet/deposit", methods=["POST"])
@auth_required
def deposit():
    token = get_token()
    phone = next((p for p, t in tokens.items() if t == token), None)
    user = get_user(phone)
    update_balance(phone, user[4] + float(request.json.get("amount", 0)))
    return jsonify({"transaction": {"id": "1", "type": "deposit", "amount": request.json.get("amount")}})

@app.route("/api/v2/wallet/withdraw", methods=["POST"])
@auth_required
def withdraw():
    token = get_token()
    phone = next((p for p, t in tokens.items() if t == token), None)
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
