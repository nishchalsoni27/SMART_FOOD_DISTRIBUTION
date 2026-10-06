import streamlit as st

import services


def render():
    user = st.session_state["user"]
    st.title("🎉 Social Event Food Requests")

    if user["role"] == "ngo":
        with st.form("request_form", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input("Event name")
            qty = c2.number_input("Quantity (kg)", min_value=0.0, step=1.0)
            address = st.text_input("Location / Address", value=user.get("address") or "")
            if st.form_submit_button("Create Request", type="primary"):
                try:
                    services.create_request(user, name, qty, address)
                    st.success("Request created")
                except services.ServiceError as e:
                    st.error(str(e))

    requests = services.list_requests()
    if not requests:
        st.caption("No event requests yet.")
    for r in requests:
        committed = sum(c["kg"] for c in r["commitments"])
        with st.container(border=True):
            st.markdown(f"**{r['event_name']}** — {r['quantity_kg']:g} kg needed")
            st.caption(f"By: {r['ngo_name']} | 📍 {r['address'] or '-'}")
            st.write(f"Commitments: {len(r['commitments'])} ({committed:g} kg)")
            if user["role"] == "provider":
                with st.form(f"commit_{r['id']}", clear_on_submit=True):
                    c1, c2 = st.columns([3, 1])
                    kg = c1.number_input("How many kg can you commit?", min_value=0.0, step=0.5,
                                         key=f"kg_{r['id']}")
                    c2.write("")
                    if c2.form_submit_button("Commit"):
                        try:
                            services.commit_to_request(r["id"], user, kg)
                            st.rerun()
                        except services.ServiceError as e:
                            st.error(str(e))
