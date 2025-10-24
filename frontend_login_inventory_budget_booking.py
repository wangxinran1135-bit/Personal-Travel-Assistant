import json
import requests
from datetime import datetime, date
import random
import streamlit as st
import pandas as pd

st.set_page_config(page_title="PTA — Admin & User Frontend", page_icon="🧭", layout="wide")

# =============================
# Session state bootstrapping
# =============================
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.show_register = False

# Local data for Budget & Booking (no database)
for key, default in [
    ("budget_total", 1000.0),
    ("budget_daily", 150.0),
    ("expenses", []),  # list of {id, date, category, note, amount}
    ("bookings", []),  # list of {id, activity, provider, date, start, end, price, status, createdAt}
    ("calendar", []),  # list of {id, bookingId, title, start, end, syncStatus}
]:
    if key not in st.session_state:
        st.session_state[key] = default

API_BASE = "http://127.0.0.1:5000"  # Change if your Flask runs elsewhere

# =============================
# Utility helpers (local only)
# =============================

def uid():
    """Generate a simple unique id."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

# ---- Budget helpers ----

def expense_sum():
    return sum(float(e["amount"]) for e in st.session_state.expenses)

def expenses_by_day():
    m = {}
    for e in st.session_state.expenses:
        d = e["date"]
        m[d] = m.get(d, 0.0) + float(e["amount"])
    return dict(sorted(m.items(), key=lambda x: x[0]))

def reset_budget():
    st.session_state.budget_total = 1000.0
    st.session_state.budget_daily = 150.0
    st.session_state.expenses = []

# ---- Booking helpers ----

def create_booking_local(b):
    st.session_state.bookings.append(b)
    if b["status"] == "Confirmed":
        st.session_state.calendar.append({
            "id": uid(),
            "bookingId": b["id"],
            "title": f"Booking: {b['activity']}",
            "start": f"{b['date']}T{b['start']}",
            "end":   f"{b['date']}T{b['end']}",
            "syncStatus": "Synced"
        })

def cancel_booking_local(bid):
    for b in st.session_state.bookings:
        if b["id"] == bid:
            b["status"] = "Cancelled"
    for ev in st.session_state.calendar:
        if ev["bookingId"] == bid:
            ev["syncStatus"] = "Failed"

# ---- Import/Export (local JSON) ----

def export_json():
    data = {
        "budget_total": st.session_state.budget_total,
        "budget_daily": st.session_state.budget_daily,
        "expenses": st.session_state.expenses,
        "bookings": st.session_state.bookings,
        "calendar": st.session_state.calendar,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def import_json(txt):
    data = json.loads(txt)
    st.session_state.budget_total = float(data.get("budget_total", 1000.0))
    st.session_state.budget_daily = float(data.get("budget_daily", 150.0))
    st.session_state.expenses = list(data.get("expenses", []))
    st.session_state.bookings = list(data.get("bookings", []))
    st.session_state.calendar = list(data.get("calendar", []))

# =============================
# Auth views (login/register)
# =============================

def view_auth():
    st.title("PTA — Login / Register")

    # Toggle register/login view
    colA, colB = st.columns(2)
    with colA:
        if st.button("I have an account (Login)"):
            st.session_state.show_register = False
    with colB:
        if st.button("Create an account (Register)"):
            st.session_state.show_register = True

    st.markdown("---")

    if not st.session_state.show_register:
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
        if submit:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                try:
                    resp = requests.post(f"{API_BASE}/api/login", json={"email": email, "password": password})
                    data = resp.json()
                except Exception:
                    st.error("Unable to connect to server. Please ensure the Flask backend is running.")
                else:
                    if resp.status_code != 200 or not data.get("success"):
                        st.error(data.get("message", "Login failed."))
                    else:
                        st.session_state.user = data["user"]
                        st.session_state.logged_in = True
                        st.success("Login successful.")
                        st.experimental_rerun()
    else:
        # Register form
        with st.form("register_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Register as", ["Tourist", "Service Provider"]) 
            provider_name = st.text_input("Provider name (for Service Provider)") if role == "Service Provider" else ""
            category = st.text_input("Provider category") if role == "Service Provider" else ""
            submit = st.form_submit_button("Register", use_container_width=True)
        if submit:
            if not name or not email or not password:
                st.error("Please fill out all required fields.")
            elif role == "Service Provider" and not provider_name:
                st.error("Please enter provider name for Service Provider registration.")
            else:
                payload = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": ("ServiceProvider" if role == "Service Provider" else "Tourist"),
                    "phone": None,
                }
                if role == "Service Provider":
                    payload["provider_name"] = provider_name
                    payload["category"] = category
                try:
                    resp = requests.post(f"{API_BASE}/api/register", json=payload)
                    data = resp.json()
                except Exception:
                    st.error("Unable to connect to server. Please ensure the Flask backend is running.")
                else:
                    if resp.status_code != 200 or not data.get("success"):
                        st.error(data.get("message", "Registration failed."))
                    else:
                        st.session_state.user = data["user"]
                        st.session_state.logged_in = True
                        st.success("Registration successful.")
                        st.experimental_rerun()

# =============================
# Budget page (local only)
# =============================

def page_budget():
    st.header("Budget Management")
    colA, colB = st.columns([2, 1], gap="large")

    with colA:
        st.subheader("Budget Overview")
        total = float(st.session_state.budget_total)
        spent = float(expense_sum())
        remaining = max(total - spent, 0.0)
        pct = 0 if total <= 0 else min(int(round(spent / total * 100)), 100)

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Budget", f"${total:,.2f}")
        k2.metric("Spent", f"${spent:,.2f}")
        k3.metric("Remaining", f"${remaining:,.2f}")

        st.caption("Usage")
        st.progress(pct)
        if total > 0 and (spent / total) >= 0.8:
            st.warning(f"Warning: Projected total expenses will reach {spent/total:.0%} of the budget.")

        st.divider()
        st.subheader("Daily Breakdown")
        daily = expenses_by_day()
        if daily:
            df = pd.DataFrame([
                {
                    "Date": d,
                    "Spent": round(v, 2),
                    "Daily Limit": float(st.session_state.budget_daily),
                    "Status": "Over" if (float(st.session_state.budget_daily) > 0 and v > float(st.session_state.budget_daily)) else "OK"
                }
                for d, v in daily.items()
            ])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No expenses yet.")

    with colB:
        st.subheader("Budget Settings")
        st.session_state.budget_total = st.number_input("Total Limit ($)", value=float(st.session_state.budget_total), step=50.0)
        st.session_state.budget_daily = st.number_input("Daily Limit ($)", value=float(st.session_state.budget_daily), step=10.0)
        if st.button("Reset All", use_container_width=True):
            reset_budget()
            st.experimental_rerun()

        st.divider()
        st.subheader("Add Expense")
        with st.form("add_expense"):
            d = st.date_input("Date", value=date.today())
            cat = st.selectbox("Category", ["Food", "Transport", "Attraction", "Hotel", "Shopping", "Other"])
            note = st.text_input("Note", "")
            amt = st.number_input("Amount ($)", min_value=0.0, step=1.0, value=0.0, format="%.2f")
            if st.form_submit_button("Add", use_container_width=True):
                st.session_state.expenses.append({
                    "id": uid(),
                    "date": d.isoformat(),
                    "category": cat,
                    "note": note,
                    "amount": float(amt)
                })
                st.experimental_rerun()

        st.divider()
        st.subheader("Expenses")
        if st.session_state.expenses:
            for e in reversed(st.session_state.expenses):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**${float(e['amount']):.2f} • {e['category']}**")
                    st.caption(f"{e['date']}" + (f" • {e['note']}" if e['note'] else ""))
                with c2:
                    if st.button("Delete", key=f"del_{e['id']}"):
                        st.session_state.expenses = [x for x in st.session_state.expenses if x["id"] != e["id"]]
                        st.experimental_rerun()

# =============================
# Booking page (local only)
# =============================

def page_booking():
    st.header("Booking")
    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        st.subheader("Bookings")
        if not st.session_state.bookings:
            st.info("No bookings yet.")
        else:
            for b in reversed(st.session_state.bookings):
                box = st.container()
                with box:
                    st.write(f"### {b['activity']}")
                    st.caption(f"Provider: {b['provider']} • ${float(b['price']):.2f} • {b['date']} {b['start']}-{b['end']}")
                    status = b["status"]
                    if status == "Confirmed":
                        st.success("Status: Confirmed")
                    elif status == "Pending":
                        st.warning("Status: Pending")
                    elif status == "Cancelled":
                        st.error("Status: Cancelled")
                    else:
                        st.info(f"Status: {status}")
                    if status != "Cancelled":
                        if st.button("Cancel", key=f"cancel_{b['id']}"):
                            cancel_booking_local(b["id"])
                            st.experimental_rerun()

    with col2:
        st.subheader("New Booking")
        with st.form("new_booking"):
            activity = st.text_input("Activity", "Sydney Opera House Tour")
            provider = st.text_input("Provider", "Provider A")
            d = st.date_input("Date", date.today())
            c1, c2 = st.columns(2)
            with c1:
                start = st.time_input("Start", value=datetime.strptime("10:00","%H:%M").time())
            with c2:
                end = st.time_input("End", value=datetime.strptime("12:00","%H:%M").time())
            price = st.number_input("Price ($)", min_value=0.0, step=1.0, value=120.0, format="%.2f")
            if st.form_submit_button("Create Booking", use_container_width=True):
                status = "Confirmed" if random.random() < 0.6 else "Pending"
                create_booking_local({
                    "id": uid(),
                    "activity": activity,
                    "provider": provider,
                    "date": d.isoformat(),
                    "start": start.strftime("%H:%M"),
                    "end": end.strftime("%H:%M"),
                    "price": float(price),
                    "status": status,
                    "createdAt": datetime.now().isoformat()
                })
                st.experimental_rerun()

        st.divider()
        st.subheader("Calendar (Synced)")
        if st.session_state.calendar:
            for ev in reversed(st.session_state.calendar):
                st.write(f"**{ev['title']}**")
                st.caption(f"{ev['start']} → {ev['end']}")
                if ev["syncStatus"] == "Synced":
                    st.success("Synced")
                else:
                    st.error(ev["syncStatus"])
        else:
            st.info("No calendar entries yet.")

# =============================
# Admin inventory pages (kept minimal; still call your Flask API)
# =============================

def page_inventory_provider():
    st.header("🧰 Provider — Service & Inventory")

    # Fetch current offerings for this provider
    try:
        resp = requests.get(f"{API_BASE}/api/service_offerings", params={"user_id": st.session_state.user["user_id"]})
        data = resp.json()
    except Exception:
        st.error("Unable to fetch service list. Please ensure backend is running.")
        return

    if resp.status_code != 200 or not data.get("success"):
        st.error(data.get("message", "Failed to get service list."))
        return

    offerings = data.get("offerings", [])
    if not offerings:
        st.info("No services yet. Add below.")
    else:
        for off in offerings:
            st.markdown(f"**#{off['offering_id']} — {off['title']}**  ")
            st.caption(off.get("description", ""))
            st.caption(f"Category: {off.get('category','-')} • Status: {off.get('status','-')}")
            st.markdown("---")

    st.subheader("Add New Service")
    with st.form("add_offering_form"):
        new_title = st.text_input("Service Title")
        new_desc = st.text_area("Service Description")
        new_category = st.text_input("Service Category")
        submitted = st.form_submit_button("Submit")
    if submitted:
        if not new_title or not new_desc:
            st.error("Please fill in the service title and description.")
        else:
            payload = {
                "user_id": st.session_state.user["user_id"],
                "title": new_title,
                "description": new_desc,
                "category": new_category
            }
            try:
                add_resp = requests.post(f"{API_BASE}/api/add_offering", json=payload)
                add_data = add_resp.json()
            except Exception:
                st.error("Add failed. Cannot connect to server.")
            else:
                if add_resp.status_code != 200 or not add_data.get("success"):
                    st.error(add_data.get("message", "Failed to add service."))
                else:
                    st.success("Service added.")
                    st.experimental_rerun()

    st.subheader("Inventory Management")
    with st.form("inventory_form"):
        offering_id = st.number_input("Offering ID", min_value=1, step=1)
        date_input = st.date_input("Date", value=date.today())
        cap_input = st.number_input("Capacity", min_value=0, step=1)
        avail_input = st.number_input("Available", min_value=0, step=1)
        submit_inv = st.form_submit_button("Submit")
    if submit_inv:
        if not date_input:
            st.error("Please select a date.")
        else:
            date_str = date_input.strftime("%Y-%m-%d")
            payload = {
                "user_id": st.session_state.user["user_id"],
                "offering_id": int(offering_id),
                "date": date_str,
                "capacity": int(cap_input),
                "available": int(avail_input)
            }
            try:
                api_resp = requests.post(f"{API_BASE}/api/inventory", json=payload)
                api_data = api_resp.json()
            except Exception:
                st.error("Action failed. Cannot connect to server.")
            else:
                if api_resp.status_code != 200 or not api_data.get("success"):
                    st.error(api_data.get("message", "Failed to update inventory."))
                else:
                    action = api_data.get("action", "")
                    st.success("Inventory updated" if action == "updated" else "Inventory added")


def page_inventory_tourist():
    st.header("🧭 Tourist — Browse Services")
    try:
        resp = requests.get(f"{API_BASE}/api/service_offerings")
        data = resp.json()
    except Exception:
        st.error("Unable to fetch service list. Please ensure backend is running.")
        return

    if resp.status_code != 200 or not data.get("success"):
        st.error("Failed to get service list.")
        return

    offerings = data.get("offerings", [])
    if not offerings:
        st.info("No services available to browse.")
        return

    for off in offerings:
        st.markdown(f"**{off['title']}**  ")
        st.caption(off.get("description", ""))
        st.caption(f"Category: {off.get('category','-')} • Status: {off.get('status','-')}")
        st.markdown("---")

# =============================
# Main app (routing after login)
# =============================

if not st.session_state.logged_in:
    view_auth()
else:
    user = st.session_state.user
    role = user.get("role")

    # Sidebar account
    st.sidebar.title("Account")
    st.sidebar.write(f"Welcome, {user.get('name','User')}!")
    st.sidebar.write(f"Role: {'Service Provider' if role == 'ServiceProvider' else 'Tourist'}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.logged_in = False
        st.experimental_rerun()

    # Sidebar navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("Navigation")
    page = st.sidebar.radio(
        "Go to",
        options=(
            "Budget",
            "Booking",
            "Inventory (Provider)" if role == "ServiceProvider" else "Browse (Tourist)",
            "Import/Export",
        ),
        index=0,
    )

    # Route to pages
    if page == "Budget":
        page_budget()
    elif page == "Booking":
        page_booking()
    elif page == "Inventory (Provider)":
        page_inventory_provider()
    elif page == "Browse (Tourist)":
        page_inventory_tourist()
    elif page == "Import/Export":
        st.header("🧰 Import / Export (Local)")
        st.subheader("Export")
        st.download_button("Download JSON", export_json(), file_name="pta_demo_data.json", mime="application/json")
        st.divider()
        st.subheader("Import")
        up = st.file_uploader("Upload JSON", type=["json"]) 
        if up is not None:
            txt = up.read().decode("utf-8")
            import_json(txt)
            st.success("Imported.")
