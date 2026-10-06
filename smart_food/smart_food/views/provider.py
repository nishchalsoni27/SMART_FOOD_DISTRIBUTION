import streamlit as st

import services


def render():
    user = st.session_state["user"]
    st.title("🍽️ Provider Dashboard")
    st.warning(f"🤖 **AI Predicted Surplus Today:** {services.predict_surplus(user['id'])} kg")

    with st.form("listing_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        food_type = c1.selectbox("Food type", services.FOOD_TYPES)
        qty = c2.number_input("Quantity (kg)", min_value=0.0, step=0.5)
        hours = c1.number_input("Safe for (hours)", min_value=1, value=4)
        address = c2.text_input("Pickup address", value=user.get("address") or "")
        if st.form_submit_button("Create Surplus Listing", type="primary", use_container_width=True):
            try:
                services.create_listing(user, food_type, qty, hours, address)
                st.success("Listing created")
            except services.ServiceError as e:
                st.error(str(e))

    st.subheader("My Listings")
    mine = services.list_listings(provider_id=user["id"])
    if not mine:
        st.caption("No listings yet.")
    for l in mine:
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(f"**{l['quantity_kg']:g} kg {l['food_type']}**  \nSafe until: {services.fmt_time(l['safe_until_time'])}")
            icon = "✅" if l["status"] == "delivered" else "🟡"
            b.markdown(f"{icon} `{l['status']}`")
