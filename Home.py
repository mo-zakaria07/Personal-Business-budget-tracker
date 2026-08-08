from datetime import date

import streamlit as st

from common import render_account_switcher
from db import (
    get_connection,
    list_categories,
    list_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
)

st.set_page_config(page_title="Budget Tracker", layout="wide")

conn = get_connection()
account = render_account_switcher()
account_id = account["id"]

st.title(f"{account['name']} — Transactions")

# --- Add transaction ---------------------------------------------------------

st.subheader("Add Transaction")
new_type = st.radio("Type", ["expense", "income"], horizontal=True, key="new_tx_type")

with st.form("add_transaction_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    tx_date = col1.date_input("Date", value=date.today())
    description = col2.text_input("Description")
    amount = col3.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")

    categories = list_categories(conn, account_id, type_=new_type)
    category_options = {"Uncategorized": None}
    for c in categories:
        category_options[c["name"]] = c["id"]
    category_label = st.selectbox("Category", list(category_options.keys()))
    notes = st.text_input("Notes")

    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            create_transaction(
                conn, account_id, category_options[category_label],
                tx_date.isoformat(), description, amount, new_type, notes,
            )
            st.success("Transaction added.")
            st.rerun()

st.divider()

# --- Filters -----------------------------------------------------------------

st.subheader("Transactions")
f1, f2, f3, f4, f5 = st.columns(5)
start = f1.date_input("From", value=None, key="filter_start")
end = f2.date_input("To", value=None, key="filter_end")

all_categories = list_categories(conn, account_id)
category_filter_options = {"All": None}
for c in all_categories:
    category_filter_options[c["name"]] = c["id"]
category_filter_label = f3.selectbox("Category", list(category_filter_options.keys()))

type_filter = f4.selectbox("Type", ["All", "income", "expense"])
search = f5.text_input("Search description")

sort_col, order_col = st.columns(2)
sort_by = sort_col.selectbox("Sort by", ["date", "description", "amount", "type"])
order = order_col.selectbox("Order", ["desc", "asc"])

transactions = list_transactions(
    conn,
    account_id,
    start=start.isoformat() if start else None,
    end=end.isoformat() if end else None,
    category_id=category_filter_options[category_filter_label],
    type_=None if type_filter == "All" else type_filter,
    search=search or None,
    sort=sort_by,
    order=order,
)

st.caption(f"{len(transactions)} transaction(s)")

if "editing_tx_id" not in st.session_state:
    st.session_state.editing_tx_id = None

if not transactions:
    st.info("No transactions found.")

for tx in transactions:
    if st.session_state.editing_tx_id == tx["id"]:
        with st.container(border=True):
            ec1, ec2, ec3 = st.columns(3)
            e_date = ec1.date_input("Date", value=date.fromisoformat(tx["date"]), key=f"edit_date_{tx['id']}")
            e_description = ec2.text_input("Description", value=tx["description"], key=f"edit_desc_{tx['id']}")
            e_amount = ec3.number_input(
                "Amount", min_value=0.0, step=0.01, format="%.2f", value=float(tx["amount"]),
                key=f"edit_amount_{tx['id']}",
            )

            ec4, ec5, ec6 = st.columns(3)
            e_type = ec4.selectbox(
                "Type", ["expense", "income"], index=0 if tx["type"] == "expense" else 1,
                key=f"edit_type_{tx['id']}",
            )
            e_categories = list_categories(conn, account_id, type_=e_type)
            e_category_options = {"Uncategorized": None}
            for c in e_categories:
                e_category_options[c["name"]] = c["id"]
            current_label = next(
                (name for name, cid in e_category_options.items() if cid == tx["category_id"]), "Uncategorized"
            )
            e_category_label = ec5.selectbox(
                "Category", list(e_category_options.keys()),
                index=list(e_category_options.keys()).index(current_label),
                key=f"edit_cat_{tx['id']}",
            )
            e_notes = ec6.text_input("Notes", value=tx["notes"] or "", key=f"edit_notes_{tx['id']}")

            save_col, cancel_col = st.columns(2)
            if save_col.button("Save", key=f"save_{tx['id']}"):
                update_transaction(
                    conn, tx["id"], e_category_options[e_category_label],
                    e_date.isoformat(), e_description, e_amount, e_type, e_notes,
                )
                st.session_state.editing_tx_id = None
                st.rerun()
            if cancel_col.button("Cancel", key=f"cancel_{tx['id']}"):
                st.session_state.editing_tx_id = None
                st.rerun()
    else:
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 1.5, 1, 2, 1.2])
            c1.write(tx["date"])
            c2.write(tx["description"] or "—")
            if tx["category_name"]:
                c3.markdown(
                    f"<span style='color:{tx['category_color']}'>&#9679;</span> {tx['category_name']}",
                    unsafe_allow_html=True,
                )
            else:
                c3.write("Uncategorized")
            amount_color = "red" if tx["type"] == "expense" else "green"
            sign = "-" if tx["type"] == "expense" else "+"
            c4.markdown(f":{amount_color}[{sign}${tx['amount']:.2f}]")
            c5.write(tx["notes"] or "")
            b1, b2 = c6.columns(2)
            if b1.button("Edit", key=f"edit_{tx['id']}"):
                st.session_state.editing_tx_id = tx["id"]
                st.rerun()
            if b2.button("Delete", key=f"delete_{tx['id']}"):
                delete_transaction(conn, tx["id"])
                st.rerun()
