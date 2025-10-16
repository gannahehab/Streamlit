import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# ----------------------------
# App Config
# -----------------------------
st.set_page_config(
    page_title="Smart BMS Dashboard (Demo)",
    page_icon="🌆",
    layout="wide",
)

# -----------------------------
# Helpers: data simulation
# -----------------------------
FLOORS = [f"Floor {i}" for i in range(1, 6)]
ZONES = ["North", "South", "East", "West"]
METRICS = ["temperature", "humidity", "co2", "lighting", "motion", "power_kw"]

np.random.seed(42)


def init_state():
    if "data" not in st.session_state:
        now = datetime.now()
        ts = pd.date_range(now - timedelta(minutes=30), periods=31, freq="min")
        records = []
        for floor in FLOORS:
            for zone in ZONES:
                base_temp = np.random.uniform(22, 26)
                base_hum = np.random.uniform(40, 55)
                base_co2 = np.random.uniform(380, 520)
                base_light = np.random.uniform(100, 700)
                base_motion = 0
                base_power = np.random.uniform(5, 25)
                for t in ts:
                    records.append({
                        "timestamp": t,
                        "floor": floor,
                        "zone": zone,
                        "temperature": base_temp + np.random.normal(0, 0.4),
                        "humidity": base_hum + np.random.normal(0, 1.5),
                        "co2": base_co2 + np.random.normal(0, 8),
                        "lighting": max(0, base_light + np.random.normal(0, 20)),
                        "motion": np.random.binomial(1, 0.15),
                        "power_kw": max(0.1, base_power + np.random.normal(0, 0.5)),
                    })
        st.session_state.data = pd.DataFrame.from_records(records)
        st.session_state.last_update = ts.max()

    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False


def append_new_minute():
    """Append 1 minute of new readings for every floor-zone."""
    ts = st.session_state.last_update + timedelta(minutes=1)
    new_rows = []
    for floor in FLOORS:
        for zone in ZONES:
            # base around recent values for smoother continuity
            recent = st.session_state.data[(st.session_state.data["floor"] == floor) &
                                           (st.session_state.data["zone"] == zone)]
            recent = recent.tail(5)
            def base(col, default):
                return (recent[col].mean() if not recent.empty else default)

            new_rows.append({
                "timestamp": ts,
                "floor": floor,
                "zone": zone,
                "temperature": np.random.normal(base("temperature", 24), 0.35),
                "humidity": np.random.normal(base("humidity", 48), 1.2),
                "co2": np.random.normal(base("co2", 450), 7),
                "lighting": max(0, np.random.normal(base("lighting", 400), 18)),
                "motion": np.random.binomial(1, 0.15),
                "power_kw": max(0.1, np.random.normal(base("power_kw", 12), 0.45)),
            })
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(new_rows)], ignore_index=True)
    st.session_state.last_update = ts


# -----------------------------
# UI – Sidebar
# -----------------------------
init_state()

with st.sidebar:
    st.header("🔧 Controls")
    selected_floor = st.selectbox("Floor", FLOORS)
    selected_zone = st.selectbox("Zone", ZONES)
    auto = st.toggle("Auto refresh (every ~2 sec)", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto

    st.markdown("---")
    st.caption("Thresholds for alerts")
    t_max = st.slider("Max Temperature (°C)", 18.0, 32.0, 27.0, 0.5)
    co2_max = st.slider("Max CO₂ (ppm)", 350, 1500, 900, 10)
    hum_min, hum_max = st.select_slider(
        "Comfort Humidity Range (%)",
        options=list(range(20, 81)),
        value=(35, 60),
    )
    st.markdown("---")
    st.caption("Data window")
    window_mins = st.slider("Minutes (history)", 10, 240, 60, 5)

# -----------------------------
# Header KPIs
# -----------------------------
st.title("🌆 Smart Building Management – Live Dashboard (Demo)")

# simulate live step if auto
if st.session_state.auto_refresh:
    # run a few update cycles to give the feeling of motion without blocking too long
    for _ in range(1):
        append_new_minute()
        # tiny sleep to allow rerender
        time.sleep(0.1)

# Always allow manual update
colA, colB = st.columns([1, 2])
with colA:
    if st.button("➕ Add latest minute"):
        append_new_minute()
with colB:
    st.caption(f"Last update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}  |  Records: {len(st.session_state.data):,}")

# filter to chosen floor/zone and time window
cutoff = st.session_state.last_update - timedelta(minutes=window_mins)
mask = (
    (st.session_state.data["timestamp"] >= cutoff) &
    (st.session_state.data["floor"] == selected_floor) &
    (st.session_state.data["zone"] == selected_zone)
)
view = st.session_state.data.loc[mask].sort_values("timestamp")

# KPIs
current = view.tail(1).iloc[0] if not view.empty else None

c1, c2, c3, c4, c5, c6 = st.columns(6)
if current is not None:
    c1.metric("Temp (°C)", f"{current['temperature']:.1f}")
    c2.metric("Humidity (%)", f"{current['humidity']:.0f}")
    c3.metric("CO₂ (ppm)", f"{current['co2']:.0f}")
    c4.metric("Lighting (lx)", f"{current['lighting']:.0f}")
    c5.metric("Motion", "Yes" if current['motion'] == 1 else "No")
    c6.metric("Power (kW)", f"{current['power_kw']:.2f}")
else:
    st.info("No data in the selected window. Try increasing minutes or clicking 'Add latest minute'.")

# Alerts
def alerts_for_row(row):
    issues = []
    if row["temperature"] > t_max:
        issues.append("High temperature")
    if row["co2"] > co2_max:
        issues.append("High CO₂")
    if not (hum_min <= row["humidity"] <= hum_max):
        issues.append("Humidity out of comfort")
    if (row["lighting"] > 200) and (row["motion"] == 0):
        issues.append("Lights on without occupancy")
    return issues

if current is not None:
    problems = alerts_for_row(current)
    if problems:
        st.error(" 🚨 Alerts: " + " | ".join(problems))
    else:
        st.success("✅ All systems normal in this zone.")

st.markdown("---")

# -----------------------------
# Charts
# -----------------------------
import altair as alt

if not view.empty:
    # Melt for compact plotting in Altair
    chart_df = view.melt(id_vars=["timestamp"], value_vars=["temperature", "humidity", "co2", "power_kw"],
                         var_name="metric", value_name="value")

    left, right = st.columns(2)

    with left:
        st.subheader("Environmental Metrics")
        line = alt.Chart(chart_df[chart_df["metric"].isin(["temperature", "humidity", "co2"])]) \
            .mark_line() \
            .encode(
                x=alt.X("timestamp:T", title="Time"),
                y=alt.Y("value:Q", title="Value"),
                color="metric:N",
                tooltip=["timestamp:T", "metric:N", alt.Tooltip("value:Q", format=".2f")]
            ).interactive()
        st.altair_chart(line, use_container_width=True)

    with right:
        st.subheader("Power Consumption (kW)")
        power = alt.Chart(view).mark_area(opacity=0.4).encode(
            x=alt.X("timestamp:T", title="Time"),
            y=alt.Y("power_kw:Q", title="kW"),
            tooltip=["timestamp:T", alt.Tooltip("power_kw:Q", format=".2f")]
        ).interactive()
        st.altair_chart(power, use_container_width=True)

    st.subheader("Raw Readings")
    st.dataframe(view.reset_index(drop=True))

# -----------------------------
# Floor overview heatmaps
# -----------------------------
st.markdown("---")
st.subheader("🏢 Floor Overview (last reading per zone)")
latest_mask = st.session_state.data.groupby(["floor", "zone"])['timestamp'].transform('max') == st.session_state.data['timestamp']
latest = st.session_state.data.loc[latest_mask, ["floor", "zone", "temperature", "co2", "power_kw", "lighting", "motion"]]

# Pivot like heatmap tables per floor
for floor in FLOORS:
    st.markdown(f"**{floor}**")
    fdf = latest[latest["floor"] == floor].copy()
    fdf["occupancy"] = np.where(fdf["motion"] == 1, "Occupied", "Empty")
    fdf = fdf.drop(columns=["motion"]).set_index("zone").sort_index()
    st.dataframe(fdf)

st.caption("Demo app: simulated data only. Replace simulation with your real IoT/DB sources later.")
