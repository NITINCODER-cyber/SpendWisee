
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from decimal import Decimal, InvalidOperation
import mysql.connector
import db_config
import csv


# =====================================================
# 1. DATABASE CONNECTION
# =====================================================

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            connection_timeout=5
        )
        return connection

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Database Connection Error",
            f"Could not connect to MySQL:\n{error}"
        )
        return None


def close_database(connection, cursor):
    if cursor:
        try:
            cursor.close()
        except mysql.connector.Error:
            pass

    if connection:
        try:
            if connection.is_connected():
                connection.close()
        except mysql.connector.Error:
            pass


# =====================================================
# 2. MAIN WINDOW
# =====================================================

root = tk.Tk()

root.title("SpendWise - Expense Tracker")
root.geometry("1100x720")
root.minsize(950, 620)
root.configure(bg="#F4F6F9")

BG_COLOR = "#F4F6F9"
SIDEBAR_COLOR = "#172554"
PRIMARY_COLOR = "#2563EB"
WHITE = "#FFFFFF"
TEXT_COLOR = "#1E293B"
MUTED_COLOR = "#64748B"

expenses = []
editing_expense_id = None


# =====================================================
# 3. TKINTER VARIABLES
# =====================================================

expense_name_var = tk.StringVar()
amount_var = tk.StringVar()
category_var = tk.StringVar()
date_var = tk.StringVar(value=str(date.today()))

search_var = tk.StringVar()


# =====================================================
# 4. MAIN LAYOUT
# =====================================================

sidebar = tk.Frame(
    root,
    bg=SIDEBAR_COLOR,
    width=220
)

sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

main_area = tk.Frame(
    root,
    bg=BG_COLOR
)

main_area.pack(
    side="right",
    fill="both",
    expand=True
)

dashboard_page = tk.Frame(main_area, bg=BG_COLOR)
add_page = tk.Frame(main_area, bg=BG_COLOR)
view_page = tk.Frame(main_area, bg=BG_COLOR)
about_page = tk.Frame(main_area, bg=BG_COLOR)


# =====================================================
# 5. HELPER FUNCTIONS
# =====================================================

def create_title(parent, text):
    tk.Label(
        parent,
        text=text,
        font=("Arial", 23, "bold"),
        bg=BG_COLOR,
        fg=TEXT_COLOR
    ).pack(anchor="w", pady=(0, 20))


def create_card(parent, title, value):
    card = tk.Frame(
        parent,
        bg=WHITE,
        highlightbackground="#E2E8F0",
        highlightthickness=1
    )

    tk.Label(
        card,
        text=title,
        font=("Arial", 11),
        bg=WHITE,
        fg=MUTED_COLOR
    ).pack(anchor="w", padx=18, pady=(15, 5))

    value_label = tk.Label(
        card,
        text=value,
        font=("Arial", 21, "bold"),
        bg=WHITE,
        fg=TEXT_COLOR
    )

    value_label.pack(anchor="w", padx=18, pady=(0, 15))

    return card, value_label


def create_table(parent, columns, headings, widths, height=8):
    table = ttk.Treeview(
        parent,
        columns=columns,
        show="headings",
        height=height
    )

    for column, heading, width in zip(
        columns, headings, widths
    ):
        table.heading(column, text=heading)
        table.column(
            column,
            width=width,
            anchor="center"
        )

    table.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    return table


def clear_table(table):
    for item in table.get_children():
        table.delete(item)


# =====================================================
# 6. LOAD EXPENSES FROM MYSQL
# =====================================================

def load_expenses():
    global expenses

    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return

        cursor = connection.cursor()

        cursor.execute("""
            SELECT expense_id,
                   expense_name,
                   amount,
                   category,
                   expense_date
            FROM expenses
            ORDER BY expense_date DESC, expense_id DESC
        """)

        records = cursor.fetchall()

        expenses = []

        for record in records:
            expenses.append({
                "id": record[0],
                "name": record[1],
                "amount": float(record[2]),
                "category": record[3] or "Other",
                "date": str(record[4])
            })

        update_dashboard()
        refresh_expense_table()

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Unable to load expenses:\n{error}"
        )

    finally:
        close_database(connection, cursor)


# =====================================================
# 7. UPDATE DASHBOARD
# =====================================================

def update_dashboard():
    total = sum(
        item["amount"] for item in expenses
    )

    transaction_count = len(expenses)

    current_month = date.today().strftime("%Y-%m")

    monthly_total = sum(
        item["amount"]
        for item in expenses
        if item["date"].startswith(current_month)
    )

    total_amount_label.config(
        text=f"₹{total:,.2f}"
    )

    monthly_amount_label.config(
        text=f"₹{monthly_total:,.2f}"
    )

    total_count_label.config(
        text=str(transaction_count)
    )

    update_category_chart()
    update_recent_table()


# =====================================================
# 8. CATEGORY-WISE EXPENSE CHART
# =====================================================

def update_category_chart():
    category_canvas.delete("all")

    category_totals = {}

    for item in expenses:
        category = item["category"] or "Other"

        category_totals[category] = (
            category_totals.get(category, 0)
            + item["amount"]
        )

    if not category_totals:
        category_canvas.configure(height=100)

        category_canvas.create_text(
            250,
            45,
            text="No expense data available yet.",
            fill=MUTED_COLOR,
            font=("Arial", 12)
        )

        return

    sorted_categories = sorted(
        category_totals.items(),
        key=lambda item: item[1],
        reverse=True
    )

    max_amount = max(
        amount for category, amount in sorted_categories
    )

    chart_height = max(
        100,
        len(sorted_categories) * 42 + 20
    )

    category_canvas.configure(height=chart_height)

    bar_width = 300
    start_y = 15
    gap = 42

    for index, (category, amount) in enumerate(
        sorted_categories
    ):
        y = start_y + index * gap

        category_canvas.create_text(
            10,
            y + 10,
            text=category,
            anchor="w",
            font=("Arial", 10),
            fill=TEXT_COLOR
        )

        category_canvas.create_rectangle(
            120,
            y,
            120 + bar_width,
            y + 20,
            fill="#E2E8F0",
            outline=""
        )

        current_width = (
            amount / max_amount
        ) * bar_width

        category_canvas.create_rectangle(
            120,
            y,
            120 + current_width,
            y + 20,
            fill=PRIMARY_COLOR,
            outline=""
        )

        category_canvas.create_text(
            435,
            y + 10,
            text=f"₹{amount:,.2f}",
            anchor="w",
            font=("Arial", 9, "bold"),
            fill=TEXT_COLOR
        )


# =====================================================
# 9. RECENT TRANSACTIONS
# =====================================================

def update_recent_table():
    clear_table(recent_table)

    for item in expenses[:5]:
        recent_table.insert(
            "",
            "end",
            values=(
                item["name"],
                f"₹{item['amount']:,.2f}",
                item["category"],
                item["date"]
            )
        )


# =====================================================
# 10. REFRESH EXPENSE TABLE
# =====================================================

def refresh_expense_table(filtered_expenses=None):
    clear_table(expense_table)

    if filtered_expenses is None:
        filtered_expenses = expenses

    for item in filtered_expenses:
        expense_table.insert(
            "",
            "end",
            values=(
                item["id"],
                item["name"],
                f"₹{item['amount']:,.2f}",
                item["category"],
                item["date"]
            )
        )


# =====================================================
# 11. SEARCH EXPENSES
# =====================================================

def search_expenses(*args):
    search_text = search_var.get().strip().lower()

    if not search_text:
        refresh_expense_table()
        return

    filtered_expenses = []

    for item in expenses:
        if (
            search_text in item["name"].lower()
            or search_text in str(item["category"]).lower()
            or search_text in item["date"].lower()
        ):
            filtered_expenses.append(item)

    refresh_expense_table(filtered_expenses)


# =====================================================
# 12. VALIDATE EXPENSE FORM
# =====================================================

def validate_expense_form():
    name = expense_name_var.get().strip()
    amount_text = amount_var.get().strip()
    category = category_var.get().strip()
    expense_date = date_var.get().strip()

    if not name or not amount_text or not category or not expense_date:
        messagebox.showwarning(
            "Missing Information",
            "Please fill in all fields."
        )
        return None

    if len(name) > 100:
        messagebox.showwarning(
            "Invalid Name",
            "Expense name cannot exceed 100 characters."
        )
        return None

    try:
        amount = Decimal(amount_text)

        if not amount.is_finite() or amount <= 0:
            raise InvalidOperation

        if amount > Decimal("99999999.99"):
            messagebox.showwarning(
                "Invalid Amount",
                "Amount is too large."
            )
            return None

        if amount.as_tuple().exponent < -2:
            messagebox.showwarning(
                "Invalid Amount",
                "Amount can have a maximum of 2 decimal places."
            )
            return None

        date.fromisoformat(expense_date)

    except (InvalidOperation, ValueError):
        messagebox.showwarning(
            "Invalid Input",
            "Enter a valid positive amount and date in YYYY-MM-DD format."
        )
        return None

    return name, amount, category, expense_date


# =====================================================
# 13. CLEAR FORM
# =====================================================

def clear_form():
    global editing_expense_id

    editing_expense_id = None

    expense_name_var.set("")
    amount_var.set("")
    category_var.set("")
    date_var.set(str(date.today()))

    form_submit_button.config(
        text="Add Expense"
    )


# =====================================================
# 14. OPEN ADD EXPENSE PAGE
# =====================================================

def open_add_page():
    clear_form()
    show_page(add_page)


# =====================================================
# 15. ADD EXPENSE
# =====================================================

def add_expense():
    form_data = validate_expense_form()

    if form_data is None:
        return

    name, amount, category, expense_date = form_data

    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO expenses
            (expense_name, amount, category, expense_date)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            amount,
            category,
            expense_date
        ))

        connection.commit()

        messagebox.showinfo(
            "Success",
            "Expense added successfully!"
        )

        clear_form()
        load_expenses()
        show_page(dashboard_page)

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Unable to add expense:\n{error}"
        )

    finally:
        close_database(connection, cursor)


# =====================================================
# 16. EDIT EXPENSE
# =====================================================

def edit_expense():
    global editing_expense_id

    selected_item = expense_table.selection()

    if not selected_item:
        messagebox.showwarning(
            "No Selection",
            "Please select an expense to edit."
        )
        return

    values = expense_table.item(
        selected_item[0],
        "values"
    )

    expense_id = int(values[0])

    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return

        cursor = connection.cursor()

        cursor.execute("""
            SELECT expense_id,
                   expense_name,
                   amount,
                   category,
                   expense_date
            FROM expenses
            WHERE expense_id = %s
        """, (expense_id,))

        record = cursor.fetchone()

        if record is None:
            messagebox.showerror(
                "Not Found",
                "This expense no longer exists."
            )
            load_expenses()
            return

        editing_expense_id = record[0]

        expense_name_var.set(record[1])
        amount_var.set(str(record[2]))
        category_var.set(record[3])
        date_var.set(str(record[4]))

        form_submit_button.config(
            text="Update Expense"
        )

        show_page(add_page)

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Unable to edit expense:\n{error}"
        )

    finally:
        close_database(connection, cursor)


# =====================================================
# 17. UPDATE EXPENSE
# =====================================================

def update_expense():
    global editing_expense_id

    form_data = validate_expense_form()

    if form_data is None:
        return

    name, amount, category, expense_date = form_data

    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE expenses
            SET expense_name = %s,
                amount = %s,
                category = %s,
                expense_date = %s
            WHERE expense_id = %s
        """, (
            name,
            amount,
            category,
            expense_date,
            editing_expense_id
        ))

        connection.commit()

        messagebox.showinfo(
            "Success",
            "Expense updated successfully!"
        )

        clear_form()
        load_expenses()
        show_page(view_page)

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Unable to update expense:\n{error}"
        )

    finally:
        close_database(connection, cursor)


# =====================================================
# 18. SAVE EXPENSE
# =====================================================

def save_expense():
    if editing_expense_id is None:
        add_expense()
    else:
        update_expense()


# =====================================================
# 19. DELETE EXPENSE
# =====================================================

def delete_expense():
    selected_item = expense_table.selection()

    if not selected_item:
        messagebox.showwarning(
            "No Selection",
            "Please select an expense to delete."
        )
        return

    values = expense_table.item(
        selected_item[0],
        "values"
    )

    expense_id = int(values[0])

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this expense?"
    )

    if not confirm:
        return

    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return

        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM expenses WHERE expense_id = %s",
            (expense_id,)
        )

        connection.commit()

        messagebox.showinfo(
            "Success",
            "Expense deleted successfully!"
        )

        load_expenses()

    except mysql.connector.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Unable to delete expense:\n{error}"
        )

    finally:
        close_database(connection, cursor)


# =====================================================
# 20. EXPORT EXPENSES TO CSV
# =====================================================

def export_expenses():
    if not expenses:
        messagebox.showwarning(
            "No Data",
            "There are no expenses to export."
        )
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Save Expenses"
    )

    if not file_path:
        return

    try:
        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Expense ID",
                "Expense Name",
                "Amount",
                "Category",
                "Date"
            ])

            for item in expenses:
                writer.writerow([
                    item["id"],
                    item["name"],
                    item["amount"],
                    item["category"],
                    item["date"]
                ])

        messagebox.showinfo(
            "Export Successful",
            "Expenses exported successfully!"
        )

    except (OSError, csv.Error) as error:
        messagebox.showerror(
            "Export Error",
            f"Unable to export expenses:\n{error}"
        )


# =====================================================
# 21. PAGE NAVIGATION
# =====================================================

def show_page(page):
    pages = [
        dashboard_page,
        add_page,
        view_page,
        about_page
    ]

    for current_page in pages:
        current_page.pack_forget()

    page.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=25
    )

    if page == view_page:
        search_var.set("")
        refresh_expense_table()


# =====================================================
# 22. SIDEBAR
# =====================================================

tk.Label(
    sidebar,
    text="SpendWise",
    font=("Arial", 23, "bold"),
    bg=SIDEBAR_COLOR,
    fg=WHITE
).pack(pady=(35, 45))


def create_nav_button(text, command):
    tk.Button(
        sidebar,
        text=text,
        command=command,
        font=("Arial", 12),
        bg=SIDEBAR_COLOR,
        fg=WHITE,
        activebackground="#1E40AF",
        activeforeground=WHITE,
        bd=0,
        relief="flat",
        anchor="w",
        padx=25,
        pady=15,
        cursor="hand2"
    ).pack(fill="x", padx=10, pady=3)


create_nav_button(
    "Dashboard",
    lambda: show_page(dashboard_page)
)

create_nav_button(
    "Add Expense",
    open_add_page
)

create_nav_button(
    "View Expenses",
    lambda: show_page(view_page)
)

create_nav_button(
    "About",
    lambda: show_page(about_page)
)


tk.Label(
    sidebar,
    text="Personal Expense Tracker",
    font=("Arial", 9),
    bg=SIDEBAR_COLOR,
    fg="#CBD5E1"
).pack(side="bottom", pady=20)


# =====================================================
# 23. DASHBOARD PAGE
# =====================================================

create_title(
    dashboard_page,
    "Dashboard"
)

summary_frame = tk.Frame(
    dashboard_page,
    bg=BG_COLOR
)

summary_frame.pack(
    fill="x",
    pady=(0, 20)
)

total_card, total_amount_label = create_card(
    summary_frame,
    "Total Expenses",
    "₹0.00"
)

monthly_card, monthly_amount_label = create_card(
    summary_frame,
    "This Month",
    "₹0.00"
)

count_card, total_count_label = create_card(
    summary_frame,
    "Total Transactions",
    "0"
)

for card in (
    total_card,
    monthly_card,
    count_card
):
    card.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 12)
    )


# Category chart

chart_frame = tk.Frame(
    dashboard_page,
    bg=WHITE,
    highlightbackground="#E2E8F0",
    highlightthickness=1
)

chart_frame.pack(
    fill="x",
    pady=(0, 20)
)

tk.Label(
    chart_frame,
    text="Category-wise Expenses",
    font=("Arial", 15, "bold"),
    bg=WHITE,
    fg=TEXT_COLOR
).pack(
    anchor="w",
    padx=18,
    pady=15
)

category_canvas = tk.Canvas(
    chart_frame,
    height=100,
    bg=WHITE,
    highlightthickness=0
)

category_canvas.pack(
    fill="x",
    padx=15,
    pady=(0, 15)
)


# Recent transactions

recent_frame = tk.Frame(
    dashboard_page,
    bg=WHITE,
    highlightbackground="#E2E8F0",
    highlightthickness=1
)

recent_frame.pack(
    fill="both",
    expand=True
)

tk.Label(
    recent_frame,
    text="Recent Transactions",
    font=("Arial", 15, "bold"),
    bg=WHITE,
    fg=TEXT_COLOR
).pack(
    anchor="w",
    padx=18,
    pady=10
)

recent_table = create_table(
    recent_frame,
    ("name", "amount", "category", "date"),
    ("Expense Name", "Amount", "Category", "Date"),
    (220, 130, 150, 150),
    height=5
)


# =====================================================
# 24. ADD / EDIT EXPENSE PAGE
# =====================================================

create_title(
    add_page,
    "Add / Edit Expense"
)

form_frame = tk.Frame(
    add_page,
    bg=WHITE,
    padx=30,
    pady=25,
    highlightbackground="#E2E8F0",
    highlightthickness=1
)

form_frame.pack(
    fill="x",
    padx=30,
    pady=10
)


def create_form_field(
    parent,
    label_text,
    variable,
    widget_type="entry"
):
    tk.Label(
        parent,
        text=label_text,
        font=("Arial", 11, "bold"),
        bg=WHITE,
        fg=TEXT_COLOR
    ).pack(
        anchor="w",
        pady=(12, 5)
    )

    if widget_type == "category":
        widget = ttk.Combobox(
            parent,
            textvariable=variable,
            values=[
                "Food",
                "Travel",
                "Shopping",
                "Education",
                "Entertainment",
                "Bills",
                "Other"
            ],
            state="readonly",
            font=("Arial", 11)
        )

    else:
        widget = tk.Entry(
            parent,
            textvariable=variable,
            font=("Arial", 11),
            bd=1,
            relief="solid"
        )

    widget.pack(
        fill="x",
        ipady=8
    )

    return widget


create_form_field(
    form_frame,
    "Expense Name",
    expense_name_var
)

create_form_field(
    form_frame,
    "Amount (₹)",
    amount_var
)

create_form_field(
    form_frame,
    "Category",
    category_var,
    "category"
)

create_form_field(
    form_frame,
    "Date (YYYY-MM-DD)",
    date_var
)


form_submit_button = tk.Button(
    form_frame,
    text="Add Expense",
    command=save_expense,
    font=("Arial", 12, "bold"),
    bg=PRIMARY_COLOR,
    fg=WHITE,
    activebackground="#1D4ED8",
    activeforeground=WHITE,
    bd=0,
    padx=20,
    pady=12,
    cursor="hand2"
)

form_submit_button.pack(
    fill="x",
    pady=(25, 10)
)


tk.Button(
    form_frame,
    text="Clear Form",
    command=clear_form,
    font=("Arial", 11),
    bg="#E2E8F0",
    fg=TEXT_COLOR,
    bd=0,
    pady=10,
    cursor="hand2"
).pack(fill="x")


# =====================================================
# 25. VIEW EXPENSES PAGE
# =====================================================

create_title(
    view_page,
    "All Expenses"
)

search_frame = tk.Frame(
    view_page,
    bg=BG_COLOR
)

search_frame.pack(
    fill="x",
    pady=(0, 10)
)

tk.Label(
    search_frame,
    text="Search:",
    font=("Arial", 11, "bold"),
    bg=BG_COLOR,
    fg=TEXT_COLOR
).pack(
    side="left",
    padx=(0, 10)
)

search_entry = tk.Entry(
    search_frame,
    textvariable=search_var,
    font=("Arial", 11),
    bd=1,
    relief="solid"
)

search_entry.pack(
    side="left",
    fill="x",
    expand=True,
    ipady=8
)


table_frame = tk.Frame(
    view_page,
    bg=WHITE,
    highlightbackground="#E2E8F0",
    highlightthickness=1
)

table_frame.pack(
    fill="both",
    expand=True
)

expense_table = create_table(
    table_frame,
    ("id", "name", "amount", "category", "date"),
    ("ID", "Expense Name", "Amount", "Category", "Date"),
    (60, 230, 130, 150, 150)
)


# Search updates the table as the user types.

search_var.trace_add(
    "write",
    search_expenses
)


# =====================================================
# 26. VIEW PAGE ACTION BUTTONS
# =====================================================

action_frame = tk.Frame(
    view_page,
    bg=BG_COLOR
)

action_frame.pack(
    fill="x",
    pady=15
)


def create_action_button(
    parent,
    text,
    command,
    color
):
    tk.Button(
        parent,
        text=text,
        command=command,
        font=("Arial", 11, "bold"),
        bg=color,
        fg=WHITE,
        activeforeground=WHITE,
        bd=0,
        padx=20,
        pady=11,
        cursor="hand2"
    ).pack(
        side="left",
        padx=(0, 10)
    )


create_action_button(
    action_frame,
    "Edit Selected",
    edit_expense,
    "#D97706"
)

create_action_button(
    action_frame,
    "Delete Selected",
    delete_expense,
    "#DC2626"
)

create_action_button(
    action_frame,
    "Refresh",
    load_expenses,
    PRIMARY_COLOR
)

create_action_button(
    action_frame,
    "Export CSV",
    export_expenses,
    "#16A34A"
)


# =====================================================
# 27. ABOUT PAGE
# =====================================================

create_title(
    about_page,
    "About SpendWise"
)

about_frame = tk.Frame(
    about_page,
    bg=WHITE,
    padx=30,
    pady=30
)

about_frame.pack(
    fill="x",
    padx=20,
    pady=10
)

tk.Label(
    about_frame,
    text="SpendWise",
    font=("Arial", 25, "bold"),
    bg=WHITE,
    fg=PRIMARY_COLOR
).pack(
    anchor="w",
    pady=(0, 15)
)

about_text = (
    "SpendWise is a personal expense tracking application "
    "developed using Python and MySQL.\n\n"

    "The application helps users manage their daily expenses "
    "and understand their spending habits.\n\n"

    "Features:\n"
    "• Add new expenses\n"
    "• View all transactions\n"
    "• Edit existing expenses\n"
    "• Delete expenses\n"
    "• Search transactions\n"
    "• Category-wise expense analysis\n"
    "• Monthly expense summary\n"
    "• Export expenses to CSV\n\n"

    "Technologies Used:\n"
    "• Python\n"
    "• Tkinter\n"
    "• MySQL\n"
    "• MySQL Connector\n"
    "• CSV module"
)

tk.Label(
    about_frame,
    text=about_text,
    font=("Arial", 12),
    bg=WHITE,
    fg=TEXT_COLOR,
    justify="left",
    anchor="w"
).pack(anchor="w")


# =====================================================
# 28. TABLE STYLING
# =====================================================

style = ttk.Style()

style.theme_use("clam")

style.configure(
    "Treeview",
    font=("Arial", 10),
    rowheight=30,
    background=WHITE,
    fieldbackground=WHITE
)

style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold"),
    background="#E2E8F0",
    foreground=TEXT_COLOR
)

style.map(
    "Treeview",
    background=[
        ("selected", "#BFDBFE")
    ],
    foreground=[
        ("selected", TEXT_COLOR)
    ]
)


# =====================================================
# 29. START APPLICATION
# =====================================================

show_page(dashboard_page)

load_expenses()

root.mainloop()
