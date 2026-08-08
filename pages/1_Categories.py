import sqlite3

import streamlit as st

from common import render_account_switcher
from db import get_connection, list_categories, create_category, update_category, delete_category

st.set_page_config(page_title="Categories - Budget Tracker", layout="wide")

conn = get_connection()
account = render_account_switcher()
account_id = account["id"]

st.title(f"{account['name']} — Categories")

# --- Add category ------------------------------------------------------------

st.subheader("Add Category")
with st.form("add_category_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Name")
    type_ = c2.selectbox("Type", ["expense", "income"])
    color = c3.color_picker("Color", value="#6366f1")

    if st.form_submit_button("Add Category"):
        if not name.strip():
            st.error("Name is required.")
        else:
            try:
                create_category(conn, account_id, name.strip(), type_, color)
                st.success(f"Added category '{name}'.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("A category with this name already exists for this account.")

st.divider()

if "editing_category_id" not in st.session_state:
    st.session_state.editing_category_id = None


def render_category_section(title, categories):
    st.subheader(title)
    if not categories:
        st.caption("No categories yet.")
        return

    for cat in categories:
        if st.session_state.editing_category_id == cat["id"]:
            with st.container(border=True):
                ec1, ec2, ec3 = st.columns(3)
                e_name = ec1.text_input("Name", value=cat["name"], key=f"edit_cat_name_{cat['id']}")
                e_type = ec2.selectbox(
                    "Type", ["expense", "income"], index=0 if cat["type"] == "expense" else 1,
                    key=f"edit_cat_type_{cat['id']}",
                )
                e_color = ec3.color_picker("Color", value=cat["color"], key=f"edit_cat_color_{cat['id']}")

                save_col, cancel_col = st.columns(2)
                if save_col.button("Save", key=f"save_cat_{cat['id']}"):
                    try:
                        update_category(conn, cat["id"], e_name.strip(), e_type, e_color)
                        st.session_state.editing_category_id = None
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("A category with this name already exists for this account.")
                if cancel_col.button("Cancel", key=f"cancel_cat_{cat['id']}"):
                    st.session_state.editing_category_id = None
                    st.rerun()
        else:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(
                    f"<span style='color:{cat['color']}'>&#9679;</span> {cat['name']}",
                    unsafe_allow_html=True,
                )
                if c2.button("Edit", key=f"edit_cat_{cat['id']}"):
                    st.session_state.editing_category_id = cat["id"]
                    st.rerun()
                if c3.button("Delete", key=f"delete_cat_{cat['id']}"):
                    delete_category(conn, cat["id"])
                    st.rerun()


expense_categories = list_categories(conn, account_id, type_="expense")
income_categories = list_categories(conn, account_id, type_="income")

render_category_section("Expense Categories", expense_categories)
render_category_section("Income Categories", income_categories)
