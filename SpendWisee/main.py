
import mysql.connector
import db_config
from datetime import date
from decimal import Decimal, InvalidOperation
import csv


# DATABASE CONNECTION
def connect_db():
    try:
        return mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database
        )
    except mysql.connector.Error as e:
        print("Database connection failed:", e)
        return None


# ADD EXPENSE
def add_expense():
    name = input("Enter expense name: ").strip()
    category = input("Enter category: ").strip()

    try:
        amount = Decimal(input("Enter amount: "))
        expense_date = input("Enter date (YYYY-MM-DD): ")

        if not name or not category or amount <= 0:
            print("Invalid input!")
            return

        date.fromisoformat(expense_date)

    except (ValueError, InvalidOperation):
        print("Please enter valid details.")
        return

    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            sql = """INSERT INTO expenses
                     (expense_name, amount, category, expense_date)
                     VALUES (%s, %s, %s, %s)"""

            cursor.execute(sql, (name, amount, category, expense_date))
            db.commit()
            print("Expense added successfully!")

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# VIEW ALL EXPENSES
def view_expenses():
    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM expenses ORDER BY expense_date DESC")
            records = cursor.fetchall()

            if not records:
                print("No expenses found.")
            else:
                print("\nID | Name | Amount | Category | Date")
                print("-" * 60)

                for row in records:
                    print(row)

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# SEARCH EXPENSE
def search_expense():
    keyword = input("Enter expense name or category: ").strip()

    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            sql = """SELECT * FROM expenses
                     WHERE expense_name LIKE %s OR category LIKE %s"""

            cursor.execute(sql, (f"%{keyword}%", f"%{keyword}%"))
            records = cursor.fetchall()

            if records:
                for row in records:
                    print(row)
            else:
                print("No matching expenses found.")

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# UPDATE EXPENSE
def update_expense():
    try:
        expense_id = int(input("Enter expense ID to update: "))
        name = input("Enter new expense name: ").strip()
        amount = Decimal(input("Enter new amount: "))
        category = input("Enter new category: ").strip()
        expense_date = input("Enter new date (YYYY-MM-DD): ")

        if not name or not category or amount <= 0:
            print("Invalid input!")
            return

        date.fromisoformat(expense_date)

    except (ValueError, InvalidOperation):
        print("Invalid details entered.")
        return

    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            sql = """UPDATE expenses
                     SET expense_name=%s, amount=%s,
                         category=%s, expense_date=%s
                     WHERE expense_id=%s"""

            cursor.execute(
                sql, (name, amount, category, expense_date, expense_id)
            )
            db.commit()

            if cursor.rowcount:
                print("Expense updated successfully!")
            else:
                print("Expense ID not found.")

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# DELETE EXPENSE
def delete_expense():
    try:
        expense_id = int(input("Enter expense ID to delete: "))
    except ValueError:
        print("Enter a valid ID.")
        return

    confirm = input("Are you sure? (y/n): ").lower()

    if confirm != "y":
        print("Deletion cancelled.")
        return

    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            cursor.execute(
                "DELETE FROM expenses WHERE expense_id=%s",
                (expense_id,)
            )
            db.commit()

            if cursor.rowcount:
                print("Expense deleted successfully!")
            else:
                print("Expense ID not found.")

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# TOTAL EXPENSE SUMMARY
def total_summary():
    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT SUM(amount), COUNT(*) FROM expenses"
            )
            total, count = cursor.fetchone()

            print("\nTotal Expenses:", total or 0)
            print("Total Transactions:", count)

            cursor.execute(
                "SELECT category, SUM(amount) FROM expenses GROUP BY category"
            )

            print("\nCategory-wise Summary:")
            for category, amount in cursor.fetchall():
                print(category, ":", amount)

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# MONTHLY EXPENSE SUMMARY
def monthly_summary():
    month = input("Enter month (YYYY-MM): ")

    try:
        date.fromisoformat(month + "-01")
    except ValueError:
        print("Enter month in YYYY-MM format.")
        return

    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            cursor.execute(
                """SELECT SUM(amount) FROM expenses
                   WHERE DATE_FORMAT(expense_date, '%Y-%m')=%s""",
                (month,)
            )

            total = cursor.fetchone()[0]
            print("Total expenses for", month, ":", total or 0)

        except mysql.connector.Error as e:
            print("Error:", e)

        finally:
            cursor.close()
            db.close()


# EXPORT EXPENSES TO CSV
def export_csv():
    db = connect_db()
    if db:
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM expenses")
            records = cursor.fetchall()

            with open("expenses.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "ID", "Expense Name", "Amount", "Category", "Date"
                ])
                writer.writerows(records)

            print("Expenses exported to expenses.csv")

        except (mysql.connector.Error, OSError) as e:
            print("Export failed:", e)

        finally:
            cursor.close()
            db.close()


# MAIN MENU
def main():
    while True:
        print("\n========== SPENDWISE ==========")
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Search Expense")
        print("4. Update Expense")
        print("5. Delete Expense")
        print("6. Total Expense Summary")
        print("7. Monthly Expense Summary")
        print("8. Export Expenses to CSV")
        print("9. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            search_expense()
        elif choice == "4":
            update_expense()
        elif choice == "5":
            delete_expense()
        elif choice == "6":
            total_summary()
        elif choice == "7":
            monthly_summary()
        elif choice == "8":
            export_csv()
        elif choice == "9":
            print("Thank you for using SpendWise!")
            break
        else:
            print("Invalid choice. Please try again.")


main()
