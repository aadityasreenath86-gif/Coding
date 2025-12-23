import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ------------------ Page Config ------------------
st.set_page_config(page_title="Expense Tracker", layout="centered")
st.title("💸 Expense Tracker (Indian Rupees ₹)")

# ------------------ Constants ------------------
CATEGORIES = [
    "Housing",
    "Utilities",
    "Food",
    "Transportation",
    "Insurance",
    "Healthcare",
    "Debt Payments",
    "Savings & Investments",
    "Personal Care",
    "Entertainment",
    "Clothing",
    "Miscellaneous"
]

EXCEL_FILE = "expenses.xlsx"
SHEET_NAME = "Expenses"

COLUMNS = ["Date", "Category", "Amount (INR)", "Type", "Note"]

# ------------------ Initialize Excel ------------------
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=COLUMNS)
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        df_init.to_excel(writer, index=False, sheet_name=SHEET_NAME)

# ------------------ Helper Functions ------------------
def load_data():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, index=False, sheet_name=SHEET_NAME)

# ------------------ Tabs ------------------
tab1, tab2 = st.tabs(["➕ Add / Remove Expense", "📊 Summary & Manage"])

# ================== TAB 1 ==================
with tab1:
    st.header("Add a new entry")

    col1, col2 = st.columns([2, 1])

    with col1:
        category = st.selectbox("Select Category", CATEGORIES)
        amount = st.number_input(
            "Amount (INR)", min_value=0.0, step=1.0, format="%.2f"
        )
        txn_type = st.radio("Type", ["Expense", "Income/Savings"])
        note = st.text_input("Optional Note")

    with col2:
        st.write("")
        st.write("")
        add_btn = st.button("Add Entry 💾", use_container_width=True)
        remove_btn = st.button("Remove Last Entry 🗑️", use_container_width=True)

    # -------- Add Entry --------
    if add_btn:
        if amount <= 0:
            st.error("Amount must be greater than ₹0")
        else:
            df = load_data()
            new_entry = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Category": category,
                "Amount (INR)": amount,
                "Type": txn_type,
                "Note": note
            }

            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)

            st.success(
                f"Added {txn_type.lower()} in '{category}': ₹{amount:,.2f}"
            )

    # -------- Remove Last Entry --------
    if remove_btn:
        df = load_data()
        if not df.empty:
            removed = df.iloc[-1]
            df = df.iloc[:-1]
            save_data(df)

            st.warning(
                f"Removed last entry: {removed['Category']} "
                f"₹{removed['Amount (INR)']:,.2f}"
            )
        else:
            st.info("No entries to remove.")

    # -------- Recent Entries --------
    st.subheader("Recent Entries")
    recent_df = load_data().tail(10)
    st.dataframe(
        recent_df if not recent_df.empty
        else pd.DataFrame(columns=COLUMNS)
    )

# ================== TAB 2 ==================
with tab2:
    st.header("Expense Summary & Management")

    data = load_data()

    if data.empty:
        st.info("No entries yet. Start adding your expenses or savings!")
    else:
        # -------- Date Processing --------
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data["Month"] = data["Date"].dt.to_period("M").astype(str)

        # -------- Month Selection --------
        selected_month = st.selectbox(
            "Select Month",
            sorted(data["Month"].dropna().unique(), reverse=True)
        )

        monthly_data = data[data["Month"] == selected_month]

        # -------- Filter Type --------
        show = st.radio(
            "Show Summary for",
            ["Expenses Only", "Savings Only", "All"]
        )

        if show == "Expenses Only":
            filtered = monthly_data[monthly_data["Type"] == "Expense"]
        elif show == "Savings Only":
            filtered = monthly_data[monthly_data["Type"] != "Expense"]
        else:
            filtered = monthly_data

        # -------- Summary --------
        st.subheader("Total by Category")

        if not filtered.empty:
            grouped = (
                filtered.groupby("Category")["Amount (INR)"]
                .sum()
                .sort_values(ascending=False)
            )

            st.bar_chart(grouped)
            st.dataframe(
                grouped.reset_index().rename(
                    columns={"Amount (INR)": "Total (INR)"}
                )
            )
        else:
            st.write("No entries for selected filter.")

        # -------- Manage Entries --------
        st.subheader("Manage Entries")

        selected_rows = st.multiselect(
            "Select rows to delete",
            options=list(filtered.index),
            format_func=lambda x: (
                f"{filtered.loc[x, 'Category']} "
                f"₹{filtered.loc[x, 'Amount (INR)']:,.2f} "
                f"({filtered.loc[x, 'Type']})"
            )
        )

        if st.button("Delete Selected Rows", disabled=not selected_rows):
            df_all = data.drop(index=selected_rows)
            df_all = df_all.reset_index(drop=True)
            save_data(df_all)
            st.success(f"Deleted {len(selected_rows)} entries.")
