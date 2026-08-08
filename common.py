import streamlit as st

from db import get_connection, list_accounts

ACCOUNT_STATE_KEY = "selected_account_id"


def render_account_switcher():
    """Renders the Personal/Business switcher in the sidebar and returns the selected account row.

    Selection is kept in st.session_state so it persists as the user moves between pages.
    """
    conn = get_connection()
    accounts = list_accounts(conn)

    if not accounts:
        st.sidebar.warning("No accounts found.")
        st.stop()

    account_by_id = {a["id"]: a for a in accounts}

    if ACCOUNT_STATE_KEY not in st.session_state or st.session_state[ACCOUNT_STATE_KEY] not in account_by_id:
        st.session_state[ACCOUNT_STATE_KEY] = accounts[0]["id"]

    st.sidebar.title("Budget Tracker")
    labels = [a["name"] for a in accounts]
    ids = [a["id"] for a in accounts]
    current_index = ids.index(st.session_state[ACCOUNT_STATE_KEY])

    selected_label = st.sidebar.radio("Account", labels, index=current_index, key="account_radio")
    selected_id = ids[labels.index(selected_label)]
    st.session_state[ACCOUNT_STATE_KEY] = selected_id

    return account_by_id[selected_id]
