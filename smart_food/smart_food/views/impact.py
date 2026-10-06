import pandas as pd
import streamlit as st

import services


@st.fragment(run_every=5)
def dashboard():
    d = services.impact_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("🍽️ Meals Served", d["meals"])
    c2.metric("⚖️ kg Rescued", f"{d['kg']:.1f}")
    c3.metric("🌱 kg CO₂e Prevented", f"{d['co2e']:.1f}")

    st.subheader("Recent Rescues (kg)")
    if d["recent"]:
        df = pd.DataFrame(reversed(d["recent"]))
        df["name"] = df["provider_name"].fillna("N/A") + " #" + df["id"].astype(str)
        st.bar_chart(df.set_index("name")["kg_rescued"], color="#15803d")
    else:
        st.caption("No deliveries yet — mark a listing as delivered to see impact here.")


def render():
    st.title("📊 Real-Time Impact Dashboard")
    dashboard()
