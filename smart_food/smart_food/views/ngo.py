import streamlit as st

import services


@st.fragment(run_every=5)  # auto-refresh every 5 s, like the original polling
def live_board():
    user = st.session_state["user"]

    st.subheader("🟢 Available Now")
    available = services.list_listings(status="listed")
    if not available:
        st.caption("No active listings")
    for l in available:
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(
                f"**{l['quantity_kg']:g} kg {l['food_type']}** from **{l['provider_name']}**  \n"
                f"📍 {l['address'] or 'Location set'}  \n⏰ Safe until {services.fmt_time(l['safe_until_time'])}"
            )
            if b.button("Accept", key=f"accept_{l['id']}", type="primary"):
                try:
                    services.accept_listing(l["id"], user)
                    st.toast("Listing accepted ✅")
                except services.ServiceError as e:
                    st.toast(str(e), icon="⚠️")
                st.rerun(scope="fragment")

    st.subheader("📦 My Accepted Pickups")
    mine = services.list_listings(accepted_by=user["id"])
    if not mine:
        st.caption("Nothing accepted yet.")
    for l in mine:
        with st.container(border=True):
            st.markdown(f"**{l['quantity_kg']:g} kg from {l['provider_name']}** — status: `{l['status']}`")
            c1, c2, _ = st.columns([1, 1, 4])
            done = l["status"] == "delivered"
            if c1.button("Mark Picked Up", key=f"pick_{l['id']}", disabled=done or l["status"] == "picked_up"):
                _change(l["id"], "picked_up", user)
            if c2.button("Mark Delivered", key=f"deliv_{l['id']}", disabled=done):
                _change(l["id"], "delivered", user)


def _change(listing_id, status, user):
    try:
        services.update_status(listing_id, status, user)
    except services.ServiceError as e:
        st.toast(str(e), icon="⚠️")
    st.rerun(scope="fragment")


def render():
    st.title("🤝 NGO Dashboard — Live Listings")
    live_board()
