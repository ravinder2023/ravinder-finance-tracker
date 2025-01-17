import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from fpdf import FPDF
import hashlib

# Database setup
DB_FILE = "data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            amount REAL,
            type TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Username already exists!")
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user

def add_transaction(user_id, date, category, amount, transaction_type):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, date, category, amount, type)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, date, category, amount, transaction_type))
    conn.commit()
    conn.close()

def get_user_transactions(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data, columns=["ID", "User ID", "Date", "Category", "Amount", "Type"])

def delete_transaction(transaction_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()

def export_to_pdf(data, filename="transactions.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Transaction Report", ln=True, align="C")
    
    pdf.ln(10)
    for index, row in data.iterrows():
        pdf.cell(200, 10, txt=f"Date: {row['Date']}, Category: {row['Category']}, Amount: ₹{row['Amount']:.2f}, Type: {row['Type']}", ln=True)
    pdf.output(filename)
    return filename

# Initialize the database
init_db()

# App title
st.title("Personal Finance Tracker with Authentication")

# Authentication
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

if st.session_state["user_id"] is None:
    auth_menu = st.sidebar.radio("Authentication", ["Login", "Register"])
    if auth_menu == "Register":
        st.header("Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Register"):
            if password != confirm_password:
                st.error("Passwords do not match!")
            else:
                register_user(username, password)
                st.success("Registration successful! Please log in.")

    elif auth_menu == "Login":
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state["user_id"] = user[0]
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password!")
else:
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state["user_id"] = None
        st.success("Logged out successfully!")
        st.experimental_rerun()

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
                add_transaction(st.session_state["user_id"], date, category, amount, transaction_type)
                st.success("Transaction added successfully!")

    # View Transactions
    elif menu == "View Transactions":
        st.header("All Transactions")
        data = get_user_transactions(st.session_state["user_id"])
        if data.empty:
            st.warning("No transactions available. Add a new transaction!")
        else:
            st.dataframe(data)
            transaction_id = st.number_input("Enter the transaction ID to delete", min_value=1, step=1)
            delete = st.button("Delete Transaction")
            if delete:
                delete_transaction(transaction_id)
                st.success("Transaction deleted successfully!")
                st.experimental_rerun()

    # Analytics
    elif menu == "Analytics":
        st.header("Analytics")
        data = get_user_transactions(st.session_state["user_id"])
        if data.empty:
            st.warning("No data available for analytics!")
        else:
            income = data[data["Type"] == "Income"]["Amount"].sum()
            expense = data[data["Type"] == "Expense"]["Amount"].sum()
            st.write(f"**Total Income**: ₹{income:.2f}")
            st.write(f"**Total Expense**: ₹{expense:.2f}")
            st.write(f"**Net Savings**: ₹{(income - expense):.2f}")

            expense_data = data[data["Type"] == "Expense"]
            if not expense_data.empty:
                category_expense = expense_data.groupby("Category")["Amount"].sum()
                fig, ax = plt.subplots()
                category_expense.plot.pie(ax=ax, autopct="%1.1f%%", startangle=90)
                ax.set_ylabel("")
                st.pyplot(fig)

    # Export Data
    elif menu == "Export Data":
        st.header("Export Transactions")
        data = get_user_transactions(st.session_state["user_id"])
        if data.empty:
            st.warning("No data available to export!")
        else:
            file_format = st.radio("Select file format", ["CSV", "PDF"])
            if file_format == "CSV":
                csv_file = "transactions.csv"
                data.to_csv(csv_file, index=False)
                with open(csv_file, "rb") as file:
                    st.download_button("Download CSV", file, file_name="transactions.csv", mime="text/csv")
            elif file_format == "PDF":
                pdf_file = export_to_pdf(data)
                with open(pdf_file, "rb") as file:
                    st.download_button("Download PDF", file, file_name="transactions.pdf", mime="application/pdf")
