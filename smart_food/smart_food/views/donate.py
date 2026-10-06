import streamlit as st

import services

CHECKLIST = [
    "Food was freshly prepared and never served",
    "Preparation time recorded & within safe window",
    "Hot food kept >60°C / cold food <5°C",
    "Packed in clean covered containers",
    "Allergens declared",
    "Quantity & contact verified",
]


def _publish():
    """Button callback: runs before the page reruns, so we can safely reset the widgets."""
    user = st.session_state["user"]
    try:
        services.create_listing(
            user, st.session_state["d_type"], st.session_state["d_qty"], 4,
            st.session_state["d_addr"], is_community=True,
        )
    except services.ServiceError as e:
        st.session_state["d_msg"] = ("error", str(e))
        return
    st.session_state["d_msg"] = ("success", "✅ Listing published! Nearby volunteers notified.")
    st.session_state["d_type"], st.session_state["d_qty"], st.session_state["d_addr"] = "veg", 0.0, ""
    for i in range(len(CHECKLIST)):
        st.session_state[f"d_chk{i}"] = False


def render():
    st.title("🍱 Community Food Donation Portal")

    kind, text = st.session_state.pop("d_msg", (None, None))
    if kind:
        getattr(st, kind)(text)

    st.selectbox("Food type", services.FOOD_TYPES, key="d_type")
    st.number_input("Quantity (kg)", min_value=0.0, step=0.5, key="d_qty")
    st.text_input("Pickup address", key="d_addr")

    st.subheader("Safety Checklist")
    checks = [st.checkbox(item, key=f"d_chk{i}") for i, item in enumerate(CHECKLIST)]
    all_checked = all(checks)
    if not all_checked:
        st.caption("Complete all safety checks to publish.")
    st.button("Publish Listing", type="primary", disabled=not all_checked, on_click=_publish)
