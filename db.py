import os
import sqlite3
from datetime import date

import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "budget.db")

DEFAULT_CATEGORIES = {
    "personal": [
        ("Salary", "income", "#22c55e"),
        ("Freelance", "income", "#84cc16"),
        ("Groceries", "expense", "#f97316"),
        ("Rent", "expense", "#ef4444"),
        ("Utilities", "expense", "#eab308"),
        ("Dining Out", "expense", "#f59e0b"),
        ("Transportation", "expense", "#3b82f6"),
        ("Entertainment", "expense", "#a855f7"),
        ("Health", "expense", "#ec4899"),
        ("Other", "expense", "#6b7280"),
    ],
    "business": [
        ("Client Revenue", "income", "#22c55e"),
        ("Consulting", "income", "#84cc16"),
        ("Software", "expense", "#6366f1"),
        ("Marketing", "expense", "#f97316"),
        ("Office Supplies", "expense", "#eab308"),
        ("Travel", "expense", "#3b82f6"),
        ("Contractors", "expense", "#a855f7"),
        ("Payroll", "expense", "#ef4444"),
        ("Taxes", "expense", "#64748b"),
        ("Other", "expense", "#6b7280"),
    ],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('personal', 'business'))
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    color TEXT NOT NULL DEFAULT '#6366f1',
    UNIQUE (account_id, name)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    notes TEXT DEFAULT ''
);
"""


@st.cache_resource
def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    _seed_if_empty(conn)
    return conn


def _seed_if_empty(conn):
    count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    if count > 0:
        return

    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (name, type) VALUES ('Personal', 'personal')")
    personal_id = cur.lastrowid
    cur.execute("INSERT INTO accounts (name, type) VALUES ('Business', 'business')")
    business_id = cur.lastrowid

    for name, type_, color in DEFAULT_CATEGORIES["personal"]:
        cur.execute(
            "INSERT INTO categories (account_id, name, type, color) VALUES (?, ?, ?, ?)",
            (personal_id, name, type_, color),
        )
    for name, type_, color in DEFAULT_CATEGORIES["business"]:
        cur.execute(
            "INSERT INTO categories (account_id, name, type, color) VALUES (?, ?, ?, ?)",
            (business_id, name, type_, color),
        )
    conn.commit()


# --- Accounts -------------------------------------------------------------

def list_accounts(conn):
    return conn.execute("SELECT * FROM accounts ORDER BY id").fetchall()


# --- Categories ------------------------------------------------------------

def list_categories(conn, account_id, type_=None):
    if type_:
        return conn.execute(
            "SELECT * FROM categories WHERE account_id = ? AND type = ? ORDER BY name",
            (account_id, type_),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM categories WHERE account_id = ? ORDER BY type, name",
        (account_id,),
    ).fetchall()


def create_category(conn, account_id, name, type_, color):
    conn.execute(
        "INSERT INTO categories (account_id, name, type, color) VALUES (?, ?, ?, ?)",
        (account_id, name, type_, color),
    )
    conn.commit()


def update_category(conn, category_id, name, type_, color):
    conn.execute(
        "UPDATE categories SET name = ?, type = ?, color = ? WHERE id = ?",
        (name, type_, color, category_id),
    )
    conn.commit()


def delete_category(conn, category_id):
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()


# --- Transactions ------------------------------------------------------------

def list_transactions(conn, account_id, start=None, end=None, category_id=None,
                       type_=None, search=None, sort="date", order="desc"):
    sortable = {"date", "description", "amount", "type"}
    sort = sort if sort in sortable else "date"
    order = "ASC" if str(order).lower() == "asc" else "DESC"

    conditions = ["t.account_id = ?"]
    params = [account_id]

    if start:
        conditions.append("t.date >= ?")
        params.append(start)
    if end:
        conditions.append("t.date <= ?")
        params.append(end)
    if category_id:
        conditions.append("t.category_id = ?")
        params.append(category_id)
    if type_:
        conditions.append("t.type = ?")
        params.append(type_)
    if search:
        conditions.append("LOWER(t.description) LIKE ?")
        params.append(f"%{search.lower()}%")

    query = f"""
        SELECT t.*, c.name AS category_name, c.color AS category_color
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE {' AND '.join(conditions)}
        ORDER BY t.{sort} {order}, t.id {order}
    """
    return conn.execute(query, params).fetchall()


def create_transaction(conn, account_id, category_id, date, description, amount, type_, notes=""):
    conn.execute(
        """INSERT INTO transactions (account_id, category_id, date, description, amount, type, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (account_id, category_id, date, description, abs(amount), type_, notes),
    )
    conn.commit()


def update_transaction(conn, tx_id, category_id, date, description, amount, type_, notes):
    conn.execute(
        """UPDATE transactions SET category_id = ?, date = ?, description = ?,
           amount = ?, type = ?, notes = ? WHERE id = ?""",
        (category_id, date, description, abs(amount), type_, notes, tx_id),
    )
    conn.commit()


def delete_transaction(conn, tx_id):
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()


# --- Dashboard ---------------------------------------------------------------

def current_month():
    return date.today().strftime("%Y-%m")


def shift_month(month, delta):
    year, mo = map(int, month.split("-"))
    zero_based = mo - 1 + delta
    year += zero_based // 12
    mo = zero_based % 12 + 1
    return f"{year:04d}-{mo:02d}"


def totals_for_month(conn, account_id, month):
    row = conn.execute(
        """SELECT
             COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
             COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
           FROM transactions
           WHERE account_id = ? AND substr(date, 1, 7) = ?""",
        (account_id, month),
    ).fetchone()
    income, expenses = row["income"], row["expenses"]
    return {"income": income, "expenses": expenses, "net": income - expenses}


def spending_by_category(conn, account_id, month, type_="expense"):
    return conn.execute(
        """SELECT c.id AS category_id, c.name, c.color, COALESCE(SUM(t.amount), 0) AS total
           FROM categories c
           LEFT JOIN transactions t ON t.category_id = c.id AND t.account_id = c.account_id
             AND substr(t.date, 1, 7) = ? AND t.type = ?
           WHERE c.account_id = ? AND c.type = ?
           GROUP BY c.id
           HAVING total > 0
           ORDER BY total DESC""",
        (month, type_, account_id, type_),
    ).fetchall()


def monthly_trend(conn, account_id, months=12):
    now_month = current_month()
    month_list = [shift_month(now_month, -i) for i in range(months - 1, -1, -1)]
    return [{"month": m, **totals_for_month(conn, account_id, m)} for m in month_list]
