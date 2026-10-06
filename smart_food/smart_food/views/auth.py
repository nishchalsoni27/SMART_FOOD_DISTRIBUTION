import streamlit as st

import services

ROLE_LABELS = {
    "provider": "Food Provider (Canteen/Hostel/Restaurant)",
    "ngo": "NGO",
    "volunteer": "Volunteer",
    "donor": "Individual Donor",
}


def render():
    st.title("🍱 Smart Food Redistribution")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        tab_login, tab_reg = st.tabs(["Login", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary", use_container_width=True):
                    try:
                        st.session_state["user"] = services.login(email, password)
                        st.rerun()
                    except services.ServiceError as e:
                        st.error(str(e))

        with tab_reg:
            with st.form("register_form"):
                name = st.text_input("Name")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_pw")
                role = st.selectbox("I am a...", list(ROLE_LABELS), format_func=ROLE_LABELS.get)
                phone = st.text_input("Phone")
                address = st.text_input("Address")
                if st.form_submit_button("Register", type="primary", use_container_width=True):
                    try:
                        st.session_state["user"] = services.register(name, email, password, role, phone, address)
                        st.rerun()
                    except services.ServiceError as e:
                        st.error(str(e))
