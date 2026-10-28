from pathlib import Path
import math
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
st.set_page_config(page_title="StockSense | Inventory Dashboard", page_icon="📦", layout="wide")
st.title("StockSense: Demand Forecasting & Inventory Optimization")
st.caption("Weeks 5–7 | Sales-based planning prototype | Historical inventory position is not present in the source dataset")

@st.cache_data
def load_data():
    hist = pd.read_csv(DATA / "historical_weekly_demand.csv", parse_dates=["week_start"])
    fc = pd.read_csv(DATA / "future_13_week_forecast.csv", parse_dates=["week_start"])
    rec = pd.read_csv(DATA / "dashboard_recommendations.csv")
    rec["store"] = rec["store"].astype(int); rec["item"] = rec["item"].astype(int)
    return hist, fc, rec

hist, fc, base_rec = load_data()
with st.sidebar:
    st.header("Planning assumptions")
    lead = st.slider("Supplier lead time (weeks)", 1, 8, 2)
    review = st.slider("Review period (weeks)", 1, 4, 1)
    sl_label = st.selectbox("Cycle service-level target", ["90%", "95%", "97.5%", "99%"], index=1)
    z_map = {"90%":1.281551565545, "95%":1.644853626951, "97.5%":1.959963984540, "99%":2.326347874041}
    z = z_map[sl_label]
    st.markdown("---")
    st.info("Lead time and review period are editable assumptions. Replace them with measured supplier values before using thresholds operationally.")
    inv_file = st.file_uploader("Upload actual inventory position CSV (optional)", type=["csv"])

fc_p = fc.pivot_table(index=["store","item"], columns="horizon_week", values="forecast_units", aggfunc="sum")
fc_p.columns = [f"forecast_wk_{int(c)}" for c in fc_p.columns]
fc_p = fc_p.reset_index()
# Residual SDs and item data are in recommendations; calculate parameter-sensitive thresholds.
recs = base_rec.drop(columns=[c for c in ["recommended_reorder_point_units","recommended_order_up_to_units","safety_stock_lead_time_units","safety_stock_protection_period_units","order_qty_if_inventory_position_zero"] if c in base_rec.columns]).copy()
recs = recs.merge(fc_p, on=["store","item"], how="left")
lead_cols = [f"forecast_wk_{i}" for i in range(1, min(lead,13)+1)]
protection_cols = [f"forecast_wk_{i}" for i in range(1, min(lead+review,13)+1)]
recs["forecast_lead_time_demand_units"] = recs[lead_cols].sum(axis=1)
recs["forecast_protection_period_demand_units"] = recs[protection_cols].sum(axis=1)
recs["safety_stock_lead_time_units"] = z * recs["seasonal_naive_residual_sd"].clip(lower=0) * math.sqrt(lead)
recs["safety_stock_protection_period_units"] = z * recs["seasonal_naive_residual_sd"].clip(lower=0) * math.sqrt(lead+review)
recs["recommended_reorder_point_units"] = np.ceil(recs["forecast_lead_time_demand_units"] + recs["safety_stock_lead_time_units"])
recs["recommended_order_up_to_units"] = np.ceil(recs["forecast_protection_period_demand_units"] + recs["safety_stock_protection_period_units"])
recs["planning_priority_score"] = recs[[f"forecast_wk_{i}" for i in range(1,14)]].sum(axis=1) + recs["safety_stock_protection_period_units"]

if inv_file is not None:
    try:
        inv = pd.read_csv(inv_file)
        required = {"store", "item", "on_hand_units"}
        if not required.issubset(inv.columns):
            st.error("Inventory CSV must contain: store, item, on_hand_units. Optional: on_order_units, backorders_units.")
        else:
            for c in ["on_order_units", "backorders_units"]:
                if c not in inv.columns: inv[c] = 0
            inv = inv[["store","item","on_hand_units","on_order_units","backorders_units"]]
            for c in ["store","item","on_hand_units","on_order_units","backorders_units"]: inv[c] = pd.to_numeric(inv[c], errors="coerce")
            recs = recs.merge(inv, on=["store","item"], how="left", validate="one_to_one")
            recs["inventory_position_units"] = recs["on_hand_units"] + recs["on_order_units"].fillna(0) - recs["backorders_units"].fillna(0)
            recs["suggested_order_units"] = np.ceil(np.maximum(0, recs["recommended_order_up_to_units"] - recs["inventory_position_units"]))
            recs["replenishment_status"] = np.where(recs["inventory_position_units"].isna(), "UNKNOWN - missing stock", np.where(recs["inventory_position_units"] <= recs["recommended_reorder_point_units"], "REORDER NOW", np.where(recs["inventory_position_units"] <= 1.2*recs["recommended_reorder_point_units"], "WATCH", "OK")))
    except Exception as e:
        st.error(f"Could not read inventory file: {e}")

fc_total = fc.groupby("week_start", as_index=False).forecast_units.sum()
c1,c2,c3,c4 = st.columns(4)
c1.metric("Store-item series", f"{recs.shape[0]:,}")
c2.metric("Forecast horizon", "13 weeks")
c3.metric("13-week forecast units", f"{fc.forecast_units.sum():,.0f}")
c4.metric("Default service target", sl_label)

st.subheader("Portfolio forecast")
fig = px.line(fc_total, x="week_start", y="forecast_units", markers=True, labels={"week_start":"Week starting","forecast_units":"Forecast units"}, title="Total weekly demand forecast (all store-item series)")
st.plotly_chart(fig, width="stretch")

if "replenishment_status" in recs.columns:
    st.subheader("Live replenishment review")
    counts = recs.replenishment_status.value_counts().reset_index(); counts.columns=["status","series"]
    c1,c2 = st.columns([1,2])
    c1.dataframe(counts, hide_index=True, width="stretch")
    c2.metric("Series flagged REORDER NOW", int((recs.replenishment_status=="REORDER NOW").sum()))
    st.caption("Alerts are calculated from the uploaded inventory snapshot and the selected assumptions; validate input completeness and freshness.")
else:
    st.warning("No inventory snapshot uploaded. Live reorder alerts are unknown; the table below shows planning thresholds, not confirmed stockout/reorder status.")

st.subheader("Explore a store-item series")
col1,col2 = st.columns(2)
stores = sorted(int(x) for x in hist.store.unique())
store = col1.selectbox("Store", stores, index=1 if 2 in stores else 0)
items = sorted(int(x) for x in hist.item.unique())
item = col2.selectbox("Item / SKU", items, index=14 if 15 in items else 0)
hs=hist[(hist.store==store)&(hist.item==item)].sort_values("week_start").tail(52)
fs=fc[(fc.store==store)&(fc.item==item)].sort_values("week_start")
fig2=go.Figure()
fig2.add_trace(go.Scatter(x=hs.week_start,y=hs.actual_units,mode="lines",name="Historical weekly sales"))
fig2.add_trace(go.Scatter(x=fs.week_start,y=fs.forecast_units,mode="lines+markers",name="Seasonal-naive forecast",line=dict(dash="dash")))
fig2.update_layout(title=f"Store {store} · Item {item}: last 52 actual weeks and 13-week forecast",xaxis_title="Week",yaxis_title="Units")
st.plotly_chart(fig2,width="stretch")
row = recs[(recs.store==store)&(recs.item==item)].iloc[0]
a,b,c,d=st.columns(4)
a.metric("Reorder point", f"{row.recommended_reorder_point_units:,.0f} units")
b.metric("Order-up-to level", f"{row.recommended_order_up_to_units:,.0f} units")
c.metric("Safety stock", f"{row.safety_stock_lead_time_units:,.0f} units")
d.metric("13-week forecast", f"{row.forecast_next_13w_units:,.0f} units")

st.subheader("SKU planning table")
show_cols=["store","item","abc_class","planning_priority_band","forecast_next_13w_units","seasonal_naive_residual_sd","safety_stock_lead_time_units","recommended_reorder_point_units","recommended_order_up_to_units"]
if "inventory_position_units" in recs.columns:
    show_cols += ["inventory_position_units","suggested_order_units","replenishment_status"]
view=recs.sort_values("planning_priority_score",ascending=False)[show_cols].head(100)
st.dataframe(view, hide_index=True, width="stretch")
st.download_button("Download calculated recommendations CSV", data=recs.to_csv(index=False).encode("utf-8"), file_name="stocksense_dashboard_recommendations.csv", mime="text/csv")
st.caption("Historical demand is observed sales, not necessarily unconstrained demand. Forecast horizon starts 1 January 2018 because the supplied dataset ends in 2017.")
