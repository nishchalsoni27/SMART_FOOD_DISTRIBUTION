"""Smart Food Waste Redistribution - entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from views import auth, donate, events, home, impact, ngo, provider

st.set_page_config(page_title="Smart Food Redistribution", page_icon="🍱", layout="wide")

user = st.session_state.get("user")

if not user:
    # Not logged in: only the login/register page exists.
    pg = st.navigation([st.Page(auth.render, title="Login", icon="🔐")], position="hidden")
else:
    pages = [st.Page(home.render, title="Home", icon="🏠", default=True)]
    if user["role"] == "provider":
        pages.append(st.Page(provider.render, title="Provider", icon="🍽️", url_path="provider"))
    if user["role"] == "ngo":
        pages.append(st.Page(ngo.render, title="NGO", icon="🤝", url_path="ngo"))
    pages += [
        st.Page(donate.render, title="Donate", icon="🍱", url_path="donate"),
        st.Page(events.render, title="Events", icon="🎉", url_path="events"),
        st.Page(impact.render, title="Impact", icon="📊", url_path="impact"),
    ]
    pg = st.navigation(pages)

    with st.sidebar:
        st.markdown(f"**{user['name']}**  \n`{user['role']}`")
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

pg.run()
