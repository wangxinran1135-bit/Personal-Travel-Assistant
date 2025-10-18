# backend/app.py
import os
import datetime as dt
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from dotenv import load_dotenv

# Load .env (expects DATABASE_URL, FLASK_SECRET, FLASK_PORT)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. postgresql+psycopg2://postgres:20020425@localhost:5433/pta_db
SECRET = os.getenv("FLASK_SECRET", "dev-secret-change-me")
PORT = int(os.getenv("FLASK_PORT", "5000"))

# --- SQLAlchemy setup ---
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

ALLOWED_ROLES = {"Tourist", "ServiceProvider", "TechnicalAdmin"}

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    user_role = Column(String(50), nullable=False)
    phone = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

# --- Flask app ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- JWT helpers (patched) ---
def create_token(user: User) -> str:
    payload = {
        "sub": str(user.user_id),  # make subject a string
        "name": user.name,
        "email": user.email,
        "role": user.user_role,
        "exp": dt.datetime.utcnow() + dt.timedelta(hours=24),
        "iat": dt.datetime.utcnow(),
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    if isinstance(token, bytes):  # PyJWT < 2.0
        token = token.decode("utf-8")
    return token

def current_user_payload():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if token.startswith("b'") and token.endswith("'"):  # tolerate Bearer b'xxx'
        token = token[2:-1]
    token = token.strip('"')
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

# --- Routes ---
@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/register")
def register():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip()
    phone = (data.get("phone") or "").strip() or None

    if not name or not email or not password or not role:
        return jsonify({"ok": False, "error": "name/email/password/role are required"}), 400
    if role not in ALLOWED_ROLES:
        return jsonify({"ok": False, "error": f"role must be one of {sorted(ALLOWED_ROLES)}"}), 400

    pw_hash = generate_password_hash(password)

    db = SessionLocal()
    try:
        user = User(name=name, email=email, password_hash=pw_hash, user_role=role, phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(user)
        return jsonify({
            "ok": True,
            "user": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "role": user.user_role,
                "phone": user.phone
            },
            "token": token
        })
    except IntegrityError:
        db.rollback()
        return jsonify({"ok": False, "error": "email already exists"}), 409
    finally:
        db.close()

@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"ok": False, "error": "email and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"ok": False, "error": "invalid email or password"}), 401
        token = create_token(user)
        return jsonify({
            "ok": True,
            "user": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "role": user.user_role,
                "phone": user.phone
            },
            "token": token
        })
    finally:
        db.close()

@app.get("/api/me")
def me():
    payload = current_user_payload()
    if not payload:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    # sub is a string; cast to int if numeric
    sub = payload.get("sub")
    try:
        sub_int = int(sub)
    except (TypeError, ValueError):
        sub_int = sub
    return jsonify({
        "ok": True,
        "user": {
            "user_id": sub_int,
            "name": payload.get("name"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
