# Budget Tracker (Python / Streamlit)


## Stack

- **Streamlit** — UI and app framework (multipage: `Home.py` for Transactions, `pages/1_Categories.py` for Categories)
- **SQLite** (via Python's built-in `sqlite3`) — storage, file lives at `data/budget.db` (gitignored, created automatically on first run)
- **pandas** — data wrangling for the dashboard charts
- **Plotly** — charts (pie, line), rendered via `st.plotly_chart`

## Current scope (v1)

- Personal / Business account switcher (sidebar)
- Category management (create/edit/delete, scoped per account)
- Manual transaction entry, with inline edit/delete and filtering (date range, category, type, search, sort)
- Dashboard: income/expense/net summary vs. last month, spending-by-category pie chart, 12-month income/expense trend line
