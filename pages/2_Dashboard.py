import pandas as pd
import plotly.express as px
import streamlit as st

from common import render_account_switcher
from db import get_connection, current_month, shift_month, totals_for_month, spending_by_category, monthly_trend

st.set_page_config(page_title="Dashboard - Budget Tracker", layout="wide")

conn = get_connection()
account = render_account_switcher()
account_id = account["id"]

st.title(f"{account['name']} — Dashboard")

# Last 24 months, oldest to newest, defaulting to the current month.
month_options = [shift_month(current_month(), -i) for i in range(23, -1, -1)]
selected_month = st.selectbox("Month", month_options, index=len(month_options) - 1)


def pct_change(current, previous):
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return (current - previous) / previous * 100


this_month = totals_for_month(conn, account_id, selected_month)
last_month = totals_for_month(conn, account_id, shift_month(selected_month, -1))

col1, col2, col3 = st.columns(3)
col1.metric(
    "Total Income", f"${this_month['income']:.2f}",
    f"{pct_change(this_month['income'], last_month['income']):+.0f}% vs last month",
)
col2.metric(
    "Total Expenses", f"${this_month['expenses']:.2f}",
    f"{pct_change(this_month['expenses'], last_month['expenses']):+.0f}% vs last month",
    delta_color="inverse",
)
col3.metric(
    "Net", f"${this_month['net']:.2f}",
    f"{pct_change(this_month['net'], last_month['net']):+.0f}% vs last month",
)

st.divider()

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Spending by Category")
    category_rows = spending_by_category(conn, account_id, selected_month, "expense")
    if category_rows:
        df = pd.DataFrame([dict(r) for r in category_rows])
        color_map = dict(zip(df["name"], df["color"]))
        fig = px.pie(df, values="total", names="name", color="name", color_discrete_map=color_map, hole=0.4)
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data for this month yet.")

with chart_col2:
    st.subheader("Monthly Trend (last 12 months)")
    trend_rows = monthly_trend(conn, account_id, 12)
    df_trend = pd.DataFrame(trend_rows)
    fig2 = px.line(
        df_trend, x="month", y=["income", "expenses"], markers=True,
        color_discrete_map={"income": "#22c55e", "expenses": "#ef4444"},
        labels={"value": "Amount ($)", "month": "Month", "variable": ""},
    )
    st.plotly_chart(fig2, use_container_width=True)
