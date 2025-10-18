import streamlit as st
import requests
from datetime import datetime, date

from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


st.set_page_config(page_title="Travel Assistant AI", page_icon="🌐", layout="wide")

# Initialize Session State for cross-interaction state
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.show_register = False
    st.session_state.selected_offering = None
    st.session_state.selected_offering_title = None
    st.session_state.success_msg = ""

# Show login or registration form if not logged in
if not st.session_state.logged_in:
    if st.session_state.show_register:
        # Registration form
        st.title("User Registration")
        with st.form("register_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Registration Type", ["Tourist", "Service Provider"])
            provider_name = ""
            category = ""
            if role == "Service Provider":
                provider_name = st.text_input("Provider Name")
                category = st.text_input("Service Category (e.g. Hotel, Attraction, etc.)")
            submit = st.form_submit_button("Register")
        if submit:
            if not name or not email or not password:
                st.error("Please fill out all required fields")
            elif role == "Service Provider" and not provider_name:
                st.error("Please enter provider name")
            else:
                # Assemble registration payload
                role_value = "Tourist" if role == "Tourist" else "ServiceProvider"
                payload = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "role": role_value,
                    "phone": None
                }
                if role_value == "ServiceProvider":
                    payload["provider_name"] = provider_name
                    payload["category"] = category
                # Send registration request
                try:
                    resp = requests.post("http://127.0.0.1:5000/api/register", json=payload)
                    data = resp.json()
                except Exception as e:
                    st.error("Unable to connect to server. Please ensure the Flask backend is running.")
                else:
                    if resp.status_code != 200 or not data.get("success"):
                        st.error(data.get("message", "Registration failed"))
                    else:
                        st.session_state.user = data["user"]
                        st.session_state.logged_in = True
                        st.session_state.show_register = False
                        st.session_state.success_msg = "Registration successful! Logged in automatically."
                        st.rerun()
        if st.button("Already have an account? Click here to login"):
            st.session_state.show_register = False
            st.rerun()
    else:
        # Login form
        st.title("User Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
        if submit:
            if not email or not password:
                st.error("Please enter email and password")
            else:
                try:
                    resp = requests.post("http://127.0.0.1:5000/api/login", json={"email": email, "password": password})
                    data = resp.json()
                except Exception as e:
                    st.error("Unable to connect to server. Please ensure the Flask backend is running.")
                else:
                    if resp.status_code != 200 or not data.get("success"):
                        st.error(data.get("message", "Login failed"))
                    else:
                        st.session_state.user = data["user"]
                        st.session_state.logged_in = True
                        st.session_state.show_register = False
                        st.rerun()
        if st.button("No account? Click here to register"):
            st.session_state.show_register = True
            st.rerun()
else:
    user = st.session_state.user
    role = user["role"]
    st.sidebar.title("Account")
    st.sidebar.write(f"Welcome, {user['name']}!")
    st.sidebar.write(f"Role: {'Service Provider' if role == 'ServiceProvider' else 'Tourist'}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.logged_in = False
        st.session_state.show_register = False
        st.session_state.selected_offering = None
        st.session_state.selected_offering_title = None
        st.session_state.success_msg = ""
        st.rerun()

    if role == "Tourist":
        st.header("Available Travel Services")
        try:
            resp = requests.get("http://127.0.0.1:5000/api/service_offerings")
            data = resp.json()
        except Exception as e:
            st.error("Unable to fetch service list. Please ensure backend is running")
        else:
            if resp.status_code != 200 or not data.get("success"):
                st.error("Failed to get service list")
            else:
                offerings = data["offerings"]
                if not offerings:
                    st.info("No services available to browse.")
                else:
                    for off in offerings:
                        st.subheader(off["title"])
                        st.write(f"Category: {off['category']}  |  Provider: {off['provider_name']}")
                        st.write(off["description"])
                        st.markdown("---")
    elif role == "ServiceProvider":
        st.header("Service Provider Dashboard")
        if st.session_state.selected_offering is None:
            if st.session_state.success_msg:
                st.success(st.session_state.success_msg)
                st.session_state.success_msg = ""
            try:
                resp = requests.get(f"http://127.0.0.1:5000/api/service_offerings?user_id={user['user_id']}")
                data = resp.json()
            except Exception as e:
                st.error("Unable to fetch service list. Please check network connection")
            else:
                if resp.status_code != 200 or not data.get("success"):
                    st.error("Failed to get service list")
                else:
                    offerings = data["offerings"]
                    st.subheader("My Services")
                    if not offerings:
                        st.info("You have not published any services. Use the form below to add.")
                    else:
                        for off in offerings:
                            st.write(f"**{off['title']}** (Category: {off['category']}, Status: {off['status']})")
                            st.write(off["description"])
                            col1, col2 = st.columns(2)
                            if col1.button("Manage Inventory", key=f"manage_{off['offering_id']}"):
                                st.session_state.selected_offering = off["offering_id"]
                                st.session_state.selected_offering_title = off["title"]
                                st.rerun()
                            if col2.button("Delete Service", key=f"delete_{off['offering_id']}"):
                                try:
                                    del_resp = requests.post("http://127.0.0.1:5000/api/delete_offering",
                                                             json={"user_id": user["user_id"], "offering_id": off["offering_id"]})
                                    del_data = del_resp.json()
                                except Exception as e:
                                    st.error("Delete failed. Cannot connect to server")
                                else:
                                    if del_resp.status_code != 200 or not del_data.get("success"):
                                        st.error(del_data.get("message", "Failed to delete service"))
                                    else:
                                        st.session_state.success_msg = "Service deleted"
                                        st.rerun()
                            st.markdown("---")
                    st.subheader("Add New Service")
                    with st.form("add_offering_form"):
                        new_title = st.text_input("Service Title")
                        new_desc = st.text_area("Service Description")
                        new_category = st.text_input("Service Category")
                        submitted = st.form_submit_button("Submit")
                    if submitted:
                        if not new_title or not new_desc:
                            st.error("Please fill in the service title and description")
                        else:
                            payload = {
                                "user_id": user["user_id"],
                                "title": new_title,
                                "description": new_desc,
                                "category": new_category
                            }
                            try:
                                add_resp = requests.post("http://127.0.0.1:5000/api/add_offering", json=payload)
                                add_data = add_resp.json()
                            except Exception as e:
                                st.error("Add failed. Cannot connect to server")
                            else:
                                if add_resp.status_code != 200 or not add_data.get("success"):
                                    st.error(add_data.get("message", "Failed to add service"))
                                else:
                                    st.session_state.success_msg = "Service added"
                                    st.rerun()
        else:
            offering_id = st.session_state.selected_offering
            offering_title = st.session_state.selected_offering_title
            st.subheader(f"Manage Inventory - {offering_title}")
            if st.button("Back"):
                st.session_state.selected_offering = None
                st.session_state.selected_offering_title = None
                st.rerun()
            if st.session_state.success_msg:
                st.success(st.session_state.success_msg)
                st.session_state.success_msg = ""
            try:
                inv_resp = requests.get(f"http://127.0.0.1:5000/api/inventory?offering_id={offering_id}")
                inv_data = inv_resp.json()
            except Exception as e:
                st.error("Unable to fetch inventory. Please check network connection")
            else:
                if inv_resp.status_code != 200 or not inv_data.get("success"):
                    st.error("Failed to get inventory")
                else:
                    records = inv_data["inventory"]
                    if not records:
                        st.info("No inventory records. Please add inventory.")
                    else:
                        try:
                            import pandas as pd
                            df = pd.DataFrame(records)
                            df["date"] = pd.to_datetime(df["date"]).dt.date
                        except Exception:
                            df = None
                        if df is not None:
                            df = df[["date", "capacity", "available", "status"]].sort_values("date")
                            st.table(df.set_index("date"))
                        else:
                            for rec in records:
                                st.write(f"{rec['date']}: Capacity {rec['capacity']}, Available {rec['available']}, Status {rec['status']}")
                    st.subheader("Add/Update Inventory")
                    with st.form("inventory_form"):
                        date_input = st.date_input("Date", value=date.today())
                        cap_input = st.number_input("Capacity", min_value=0, step=1)
                        avail_input = st.number_input("Available", min_value=0, step=1)
                        submit_inv = st.form_submit_button("Submit")
                    if submit_inv:
                        if not date_input:
                            st.error("Please select a date")
                        else:
                            date_str = date_input.strftime("%Y-%m-%d")
                            payload = {
                                "user_id": user["user_id"],
                                "offering_id": offering_id,
                                "date": date_str,
                                "capacity": int(cap_input),
                                "available": int(avail_input)
                            }
                            try:
                                api_resp = requests.post("http://127.0.0.1:5000/api/inventory", json=payload)
                                api_data = api_resp.json()
                            except Exception as e:
                                st.error("Action failed. Cannot connect to server")
                            else:
                                if api_resp.status_code != 200 or not api_data.get("success"):
                                    st.error(api_data.get("message", "Failed to update inventory"))
                                else:
                                    action = api_data.get("action", "")
                                    if action == "updated":
                                        st.session_state.success_msg = "Inventory updated"
                                    else:
                                        st.session_state.success_msg = "Inventory added"
                                    st.rerun()
