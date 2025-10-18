import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:5000/api")

st.set_page_config(page_title="PTA Auth", page_icon="🔐", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def api_post(path, payload):
    url = f"{API_BASE}{path}"
    r = requests.post(url, json=payload, timeout=15)
    return r.status_code, r.json()

def api_get(path):
    url = f"{API_BASE}{path}"
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    r = requests.get(url, headers=headers, timeout=15)
    return r.status_code, r.json()

st.title("Personal Travel Assistant — Sign Up / Sign In")

if st.session_state.user:
    st.success(f"Signed in as {st.session_state.user['name']} ({st.session_state.user['role']})")
    if st.button("Sign out"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()

    st.subheader("My Profile")
    st.code(st.session_state.user, language="json")
    st.divider()
    st.write("Verify current session via /api/me:")
    code_status, code_json = api_get("/me")
    st.write(code_status, code_json)

else:
    tab_reg, tab_log = st.tabs(["📝 Sign Up", "🔑 Sign In"])

    with tab_reg:
        with st.form("register_form"):
            name = st.text_input("Name", "")
            email = st.text_input("Email", "")
            password = st.text_input("Password", type="password")
            phone = st.text_input("Phone (optional)", "")
            role = st.selectbox("Role", ["Tourist", "ServiceProvider", "TechnicalAdmin"])
            submit = st.form_submit_button("Create account")
        if submit:
            status, data = api_post("/register", {
                "name": name, "email": email, "password": password, "phone": phone, "role": role
            })
            if status == 200 and data.get("ok"):
                st.success("Sign-up successful. You are now signed in.")
                st.session_state.token = data["token"]
                st.session_state.user = data["user"]
                st.rerun()
            else:
                st.error(data.get("error", f"Sign-up failed (HTTP {status})"))

    with tab_log:
        with st.form("login_form"):
            email2 = st.text_input("Email", key="login_email")
            password2 = st.text_input("Password", type="password", key="login_pwd")
            submit2 = st.form_submit_button("Sign in")
        if submit2:
            status, data = api_post("/login", {"email": email2, "password": password2})
            if status == 200 and data.get("ok"):
                st.success("Signed in.")
                st.session_state.token = data["token"]
                st.session_state.user = data["user"]
                st.rerun()
            else:
                st.error(data.get("error", f"Sign-in failed (HTTP {status})"))
