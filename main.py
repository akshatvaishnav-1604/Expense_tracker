"""
main.py
-------
Interactive Command Line Interface (CLI) for the Object-Oriented Expense Tracker.
Provides a beginner-friendly, menu-driven interface to:
  1. Add new transactions (with auto-suggested category)
  2. View all transactions in a clean tabular format
  3. Filter transactions by date range, category, or type
  4. View summary statistics and category breakdowns (with visual bar graphs)
  5. Export transactions to CSV
  6. Import transactions from CSV
  7. Delete a transaction
  8. Populate sample data for fast demonstration
  9. Exit the application
"""

import os
import sys
from datetime import datetime
from typing import List
from models import Transaction
from tracker import ExpenseTracker

# Ensure UTF-8 output encoding for cross-platform terminal compatibility (especially Windows)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ANSI color codes for enhanced terminal UI
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def print_banner() -> None:
    """Prints a styled welcome banner."""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 68)
    print("      [+] PERSONAL EXPENSE TRACKER & FINANCIAL ANALYTICS [+]      ")
    print("          (Object-Oriented Python + SQLite3 Database)           ")
    print("=" * 68 + f"{Colors.RESET}")


def display_menu() -> None:
    """Prints the main interactive menu options."""
    print(f"\n{Colors.BOLD}--- MAIN MENU ---{Colors.RESET}")
    print(f"{Colors.GREEN}1.{Colors.RESET} Add Transaction")
    print(f"{Colors.GREEN}2.{Colors.RESET} View All Transactions")
    print(f"{Colors.GREEN}3.{Colors.RESET} Filter Transactions (Date Range, Category, Type)")
    print(f"{Colors.GREEN}4.{Colors.RESET} View Summary Report & Category Breakdown")
    print(f"{Colors.GREEN}5.{Colors.RESET} Export Transactions to CSV")
    print(f"{Colors.GREEN}6.{Colors.RESET} Import Transactions from CSV")
    print(f"{Colors.GREEN}7.{Colors.RESET} Delete a Transaction")
    print(f"{Colors.GREEN}8.{Colors.RESET} Populate Sample Data (Quick Demo)")
    print(f"{Colors.RED}9.{Colors.RESET} Exit")


def format_transactions_table(transactions: List[Transaction]) -> None:
    """
    Renders a list of Transaction objects in a clean, aligned ASCII table.
    """
    if not transactions:
        print(f"\n{Colors.YELLOW}No transactions found.{Colors.RESET}")
        return

    header = f"{'ID':<5} | {'Date':<11} | {'Type':<8} | {'Category':<16} | {'Amount ($)':>12} | {'Description'}"
    divider = "-" * 80

    print(f"\n{Colors.BOLD}{header}{Colors.RESET}")
    print(divider)

    total_expense = 0.0
    total_income = 0.0

    for tx in transactions:
        type_color = Colors.GREEN if tx.trans_type == "Income" else Colors.RED
        formatted_type = f"{type_color}{tx.trans_type:<8}{Colors.RESET}"
        amount_str = f"{tx.amount:>12.2f}"

        print(
            f"{tx.id:<5} | {tx.date:<11} | {formatted_type} | {tx.category:<16} | {amount_str} | {tx.description}"
        )

        if tx.trans_type == "Income":
            total_income += tx.amount
        else:
            total_expense += tx.amount

    print(divider)
    print(
        f"{Colors.BOLD}Total Income: {Colors.GREEN}${total_income:.2f}{Colors.RESET} | "
        f"{Colors.BOLD}Total Expenses: {Colors.RED}${total_expense:.2f}{Colors.RESET} | "
        f"{Colors.BOLD}Net: {Colors.CYAN}${total_income - total_expense:.2f}{Colors.RESET} "
        f"(Count: {len(transactions)})"
    )


def prompt_add_transaction(tracker: ExpenseTracker) -> None:
    """Interactively guides the user to create and add a new transaction."""
    print(f"\n{Colors.BOLD}--- Add New Transaction ---{Colors.RESET}")

    # 1. Transaction Type
    print("Transaction Type:")
    print("  1. Expense (Default)")
    print("  2. Income")
    type_choice = input("Enter choice [1/2] (press Enter for Expense): ").strip()
    trans_type = "Income" if type_choice == "2" else "Expense"

    # 2. Date
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_input = input(f"Date (YYYY-MM-DD) [Default: {today_str}]: ").strip()
    date_val = date_input if date_input else today_str

    try:
        datetime.strptime(date_val, "%Y-%m-%d")
    except ValueError:
        print(f"{Colors.RED}Error: Invalid date format. Please use YYYY-MM-DD.{Colors.RESET}")
        return

    # 3. Description
    description = input("Description / Note (e.g. 'Uber to office', 'Monthly Salary'): ").strip()

    # 4. Automated Category Suggestion
    suggested_category = tracker.suggest_category(description)
    if suggested_category:
        print(f"{Colors.CYAN}💡 Smart Suggestion detected category: '{suggested_category}'{Colors.RESET}")
        cat_input = input(f"Category [Press Enter to accept '{suggested_category}' or type custom]: ").strip()
        category = cat_input if cat_input else suggested_category
    else:
        category = input("Category (e.g. Groceries, Transport, Utilities, Food & Dining): ").strip()
        if not category:
            category = "Miscellaneous"

    # 5. Amount
    amount_str = input("Amount ($): ").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            print(f"{Colors.RED}Error: Amount must be greater than 0.{Colors.RESET}")
            return
    except ValueError:
        print(f"{Colors.RED}Error: Please enter a valid numerical amount.{Colors.RESET}")
        return

    # Create Transaction Object & Persist to DB
    try:
        new_tx = Transaction(
            date=date_val,
            category=category,
            amount=amount,
            description=description,
            trans_type=trans_type,
        )
        tx_id = tracker.add_transaction(new_tx)
        print(f"\n{Colors.GREEN}✔ Successfully saved transaction #{tx_id}: {new_tx}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error adding transaction: {e}{Colors.RESET}")


def prompt_filter_transactions(tracker: ExpenseTracker) -> None:
    """Interactively filters transactions by various criteria."""
    print(f"\n{Colors.BOLD}--- Filter Transactions ---{Colors.RESET}")
    print("Leave any filter empty to skip it.")

    start_date = input("Start Date (YYYY-MM-DD) or Enter for all: ").strip() or None
    end_date = input("End Date (YYYY-MM-DD) or Enter for all: ").strip() or None
    category = input("Category keyword or Enter for all: ").strip() or None
    
    print("Type Filter: 1. All | 2. Expense Only | 3. Income Only")
    t_choice = input("Enter choice [1/2/3] (default 1): ").strip()
    trans_type = None
    if t_choice == "2":
        trans_type = "Expense"
    elif t_choice == "3":
        trans_type = "Income"

    results = tracker.get_filtered_transactions(
        start_date=start_date,
        end_date=end_date,
        category=category,
        trans_type=trans_type,
    )
    format_transactions_table(results)


def display_summary_report(tracker: ExpenseTracker) -> None:
    """Renders high-level summary metrics and category breakdown with visual bars."""
    print(f"\n{Colors.BOLD}================ FINANCIAL SUMMARY REPORT ================{Colors.RESET}")

    summary = tracker.get_summary()
    total_income = summary["total_income"]
    total_expense = summary["total_expense"]
    net_balance = summary["net_balance"]
    count = summary["count"]

    savings_rate = (net_balance / total_income * 100.0) if total_income > 0 else 0.0

    print(f"Total Transactions: {Colors.BOLD}{count}{Colors.RESET}")
    print(f"Total Income:       {Colors.GREEN}${total_income:>10.2f}{Colors.RESET}")
    print(f"Total Expenses:     {Colors.RED}${total_expense:>10.2f}{Colors.RESET}")
    
    balance_color = Colors.GREEN if net_balance >= 0 else Colors.RED
    print(f"Net Balance:        {balance_color}${net_balance:>10.2f}{Colors.RESET}")
    if total_income > 0:
        print(f"Savings Rate:       {balance_color}{savings_rate:>9.1f}%{Colors.RESET}")

    print(f"\n{Colors.BOLD}--- Expense Breakdown by Category (SQL GROUP BY) ---{Colors.RESET}")
    cat_summary = tracker.get_category_summary(trans_type="Expense")

    if not cat_summary:
        print(f"{Colors.YELLOW}No expense records found to generate category report.{Colors.RESET}")
    else:
        print(f"{'Category':<18} | {'Total ($)':>10} | {'Count':>5} | {'Percentage':>10} | Distribution")
        print("-" * 75)
        for item in cat_summary:
            cat = item["category"]
            total = item["total_amount"]
            c = item["count"]
            pct = item["percentage"]
            # Visual ASCII bar graph (each block is 4%)
            bar = "█" * int(pct / 4)
            print(f"{cat:<18} | ${total:>9.2f} | {c:>5} | {pct:>9.1f}% | {Colors.CYAN}{bar}{Colors.RESET}")

    print(f"{Colors.BOLD}=========================================================={Colors.RESET}")


def prompt_export_csv(tracker: ExpenseTracker) -> None:
    """Exports transactions to a CSV file."""
    print(f"\n{Colors.BOLD}--- Export to CSV ---{Colors.RESET}")
    default_filename = "exported_expenses.csv"
    filename = input(f"Enter target filename [Default: {default_filename}]: ").strip()
    if not filename:
        filename = default_filename

    if not filename.endswith(".csv"):
        filename += ".csv"

    try:
        count = tracker.export_to_csv(filename)
        print(f"{Colors.GREEN}✔ Successfully exported {count} transactions to '{filename}'.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error exporting to CSV: {e}{Colors.RESET}")


def prompt_import_csv(tracker: ExpenseTracker) -> None:
    """Imports transactions from a CSV file."""
    print(f"\n{Colors.BOLD}--- Import from CSV ---{Colors.RESET}")
    default_filename = "sample_data.csv"
    filename = input(f"Enter source CSV filename [Default: {default_filename}]: ").strip()
    if not filename:
        filename = default_filename

    try:
        success, errors = tracker.import_from_csv(filename)
        print(f"{Colors.GREEN}✔ Successfully imported {success} transactions from '{filename}'.{Colors.RESET}")
        if errors > 0:
            print(f"{Colors.YELLOW}⚠ Skipped {errors} invalid rows.{Colors.RESET}")
    except FileNotFoundError:
        print(f"{Colors.RED}Error: File '{filename}' was not found.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error importing CSV: {e}{Colors.RESET}")


def prompt_delete_transaction(tracker: ExpenseTracker) -> None:
    """Prompts for an ID and deletes the corresponding transaction."""
    print(f"\n{Colors.BOLD}--- Delete Transaction ---{Colors.RESET}")
    id_input = input("Enter the ID of the transaction to delete: ").strip()

    try:
        trans_id = int(id_input)
    except ValueError:
        print(f"{Colors.RED}Error: ID must be an integer.{Colors.RESET}")
        return

    # Check if transaction exists
    tx = tracker.get_transaction_by_id(trans_id)
    if not tx:
        print(f"{Colors.RED}No transaction found with ID #{trans_id}.{Colors.RESET}")
        return

    print(f"Found: {tx}")
    confirm = input("Are you sure you want to delete this record? (y/N): ").strip().lower()
    if confirm == "y":
        deleted = tracker.delete_transaction(trans_id)
        if deleted:
            print(f"{Colors.GREEN}✔ Transaction #{trans_id} deleted successfully.{Colors.RESET}")
        else:
            print(f"{Colors.RED}Failed to delete transaction #{trans_id}.{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}Deletion cancelled.{Colors.RESET}")


def seed_sample_data(tracker: ExpenseTracker) -> None:
    """Seeds the database with realistic sample transactions for instant demonstration."""
    sample_records = [
        ("2026-03-01", "Salary", 4500.00, "Monthly Software Engineer Salary", "Income"),
        ("2026-03-02", "Housing", 1200.00, "Apartment Monthly Rent", "Expense"),
        ("2026-03-03", "Groceries", 145.50, "Walmart weekly grocery shopping", "Expense"),
        ("2026-03-04", "Transport", 32.75, "Uber ride to client meeting", "Expense"),
        ("2026-03-05", "Food & Dining", 48.00, "Dinner with friends at Italian Cafe", "Expense"),
        ("2026-03-06", "Utilities", 85.20, "Broadband Internet and Electricity bill", "Expense"),
        ("2026-03-07", "Entertainment", 15.99, "Netflix Monthly Subscription", "Expense"),
        ("2026-03-08", "Shopping", 110.00, "Amazon purchase: Ergonomic mouse & keyboard", "Expense"),
        ("2026-03-09", "Investments", 250.00, "Quarterly Stock Dividend", "Income"),
        ("2026-03-10", "Healthcare", 45.00, "Pharmacy prescription medicines", "Expense"),
    ]

    added = 0
    for date_val, category, amount, description, trans_type in sample_records:
        tx = Transaction(
            date=date_val,
            category=category,
            amount=amount,
            description=description,
            trans_type=trans_type,
        )
        tracker.add_transaction(tx)
        added += 1

    print(f"\n{Colors.GREEN}✔ Successfully loaded {added} sample transactions into the database!{Colors.RESET}")


def main() -> None:
    """Main CLI execution loop."""
    print_banner()
    tracker = ExpenseTracker("expenses.db")

    while True:
        try:
            display_menu()
            choice = input(f"\n{Colors.BOLD}Select an option (1-9): {Colors.RESET}").strip()

            if choice == "1":
                prompt_add_transaction(tracker)
            elif choice == "2":
                transactions = tracker.get_all_transactions()
                format_transactions_table(transactions)
            elif choice == "3":
                prompt_filter_transactions(tracker)
            elif choice == "4":
                display_summary_report(tracker)
            elif choice == "5":
                prompt_export_csv(tracker)
            elif choice == "6":
                prompt_import_csv(tracker)
            elif choice == "7":
                prompt_delete_transaction(tracker)
            elif choice == "8":
                seed_sample_data(tracker)
            elif choice == "9":
                print(f"\n{Colors.CYAN}Thank you for using Personal Expense Tracker. Goodbye! 👋{Colors.RESET}\n")
                sys.exit(0)
            else:
                print(f"{Colors.RED}Invalid selection. Please enter a number between 1 and 9.{Colors.RESET}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Operation cancelled by user. Returning to menu...{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}An unexpected error occurred: {e}{Colors.RESET}")


if __name__ == "__main__":
    main()
