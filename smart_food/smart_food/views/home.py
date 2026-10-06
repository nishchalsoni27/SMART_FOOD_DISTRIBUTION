import streamlit as st

HINTS = {
    "provider": "Create surplus listings on the **Provider** page.",
    "ngo": "Accept live listings on the **NGO** page and create requests on **Events**.",
    "volunteer": "Browse **Events** and watch the **Impact** dashboard.",
    "donor": "Share leftover food through the **Donate** page.",
}


def render():
    user = st.session_state["user"]
    st.title(f"Welcome {user['name']}!")
    st.write(f"Role: **{user['role']}**")
    st.info(HINTS.get(user["role"], "Use the sidebar to explore features."))
