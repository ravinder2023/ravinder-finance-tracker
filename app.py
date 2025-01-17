import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Initialize session state
if "data" not in st.session_state:
    st.session_state["data"] = pd.DataFrame(columns=["Date", "Category", "Amount", "Type"])

# App title
st.title("Personal Finance Tracker")
st.sidebar.title("Navigation")

# Sidebar menu
menu = st.sidebar.radio("Go to", ["Home", "Add Transaction", "View Transactions", "Analytics", "Export Data"])

# Home
if menu == "Home":
    st.header("Welcome to Personal Finance Tracker")
    st.markdown(
        """
        This app helps you manage your income and expenses effectively.  
        **Features**:  
        - Add, Edit, and Delete Transactions  
        - Visualize spending categories  
        - Export data as CSV or PDF  
        """
    )

# Add Transaction
elif menu == "Add Transaction":
    st.header("Add a New Transaction")
    with st.form("transaction_form", clear_on_submit=True):
        date = st.date_input("Date")
        category = st.text_input("Category")
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        transaction_type = st.selectbox("Type", ["Income", "Expense"])
        submit = st.form_submit_button("Add Transaction")

        if submit:
            new_data = pd.DataFrame(
                {
                    "Date": [date],
                    "Category": [category],
                    "Amount": [amount],
                    "Type": [transaction_type],
                }
            )
            st.session_state["data"] = pd.concat([st.session_state["data"], new_data], ignore_index=True)
            st.success("Transaction added successfully!")

# View Transactions
elif menu == "View Transactions":
    st.header("All Transactions")
    if st.session_state["data"].empty:
        st.warning("No transactions available. Add a new transaction!")
    else:
        st.dataframe(st.session_state["data"])
        st.markdown("### Edit or Delete Transactions")
        index = st.number_input("Enter the row index to delete", min_value=0, max_value=len(st.session_state["data"]) - 1, step=1)
        delete = st.button("Delete Transaction")
        if delete:
            st.session_state["data"] = st.session_state["data"].drop(index).reset_index(drop=True)
            st.success("Transaction deleted successfully!")

# Analytics
elif menu == "Analytics":
    st.header("Analytics")
    if st.session_state["data"].empty:
        st.warning("No data available for analytics!")
    else:
        st.markdown("### Summary")
        income = st.session_state["data"][st.session_state["data"]["Type"] == "Income"]["Amount"].sum()
        expense = st.session_state["data"][st.session_state["data"]["Type"] == "Expense"]["Amount"].sum()
        st.write(f"**Total Income**: ₹{income:.2f}")
        st.write(f"**Total Expense**: ₹{expense:.2f}")
        st.write(f"**Net Savings**: ₹{(income - expense):.2f}")

        st.markdown("### Expense by Category")
        expense_data = st.session_state["data"][st.session_state["data"]["Type"] == "Expense"]
        if not expense_data.empty:
            category_expense = expense_data.groupby("Category")["Amount"].sum()
            fig, ax = plt.subplots()
            category_expense.plot.pie(ax=ax, autopct="%1.1f%%", startangle=90)
            ax.set_ylabel("")
            st.pyplot(fig)
        else:
            st.warning("No expense data available for pie chart!")

# Export Data
elif menu == "Export Data":
    st.header("Export Transactions")
    if st.session_state["data"].empty:
        st.warning("No data available to export!")
    else:
        file_format = st.radio("Select file format", ["CSV", "PDF"])
        if file_format == "CSV":
            csv_file = "transactions.csv"
            st.session_state["data"].to_csv(csv_file, index=False)
            with open(csv_file, "rb") as file:
                st.download_button("Download CSV", file, file_name="transactions.csv", mime="text/csv")
        elif file_format == "PDF":
            st.info("PDF export functionality is under development.")
