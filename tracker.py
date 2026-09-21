"""
tracker.py
----------
Defines the ExpenseTracker class which serves as the Database Manager and Business Logic layer.
Demonstrates:
  - SQLite database connectivity using python's built-in sqlite3
  - Secure parameterized SQL queries to prevent SQL injection
  - Table creation and Schema Definition
  - CRUD (Create, Read, Update, Delete) operations
  - SQL Aggregations (SUM, COUNT, GROUP BY, COALESCE)
  - Keyword-based smart categorization
  - CSV file Export and Import using Python's standard csv module
"""

import csv
import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Tuple, Dict, Any, Generator
from models import Transaction


class ExpenseTracker:
    """
    Manages SQLite database storage and financial business logic.
    """

    # Keyword mapping dictionary for automatic categorization
    KEYWORD_CATEGORY_MAP: Dict[str, List[str]] = {
        "Transport": ["uber", "ola", "lyft", "taxi", "cab", "bus", "train", "metro", "flight", "fuel", "petrol", "diesel", "gas"],
        "Food & Dining": ["restaurant", "cafe", "coffee", "starbucks", "mcdonald", "burger", "pizza", "dinner", "lunch", "breakfast", "swiggy", "zomato", "doordash"],
        "Groceries": ["supermarket", "grocery", "groceries", "walmart", "target", "costco", "whole foods", "vegetables", "fruits", "milk", "bread"],
        "Entertainment": ["netflix", "spotify", "hulu", "movie", "cinema", "theatre", "concert", "game", "steam", "playstation", "disney"],
        "Shopping": ["amazon", "flipkart", "ebay", "clothes", "shoes", "mall", "zara", "h&m", "electronics"],
        "Utilities": ["electricity", "water", "internet", "wifi", "broadband", "phone", "recharge", "power bill"],
        "Housing": ["rent", "mortgage", "maintenance", "property tax", "landlord"],
        "Healthcare": ["pharmacy", "medicine", "doctor", "hospital", "clinic", "dental", "meds"],
        "Salary": ["salary", "paycheck", "payroll", "stipend", "wages", "bonus"],
        "Investments": ["dividend", "stocks", "mutual fund", "interest", "crypto", "capital gain"],
    }

    def __init__(self, db_path: str = "expenses.db"):
        """
        Initializes the database connection and creates the table if it does not exist.
        
        Args:
            db_path (str): File path to the SQLite database file (or ':memory:' for tests).
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager to establish, auto-commit, and safely close SQLite database connections.
        Ensures resources are freed and file locks are released on all platforms.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self) -> None:
        """
        Creates the 'transactions' table in SQLite if it does not already exist.
        Uses SQL DDL (Data Definition Language).
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            trans_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        );
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()

    # ==========================================
    # 1. CRUD Operations (Create, Read, Delete)
    # ==========================================

    def add_transaction(self, transaction: Transaction) -> int:
        """
        Inserts a new transaction into the database.
        
        Args:
            transaction (Transaction): The Transaction object to insert.
            
        Returns:
            int: The auto-generated database ID of the newly inserted record.
        """
        sql = """
        INSERT INTO transactions (date, trans_type, category, amount, description)
        VALUES (?, ?, ?, ?, ?);
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Execute with parameterized inputs to prevent SQL Injection
            cursor.execute(
                sql,
                (
                    transaction.date,
                    transaction.trans_type,
                    transaction.category,
                    transaction.amount,
                    transaction.description,
                ),
            )
            conn.commit()
            transaction.id = cursor.lastrowid
            return transaction.id

    def get_all_transactions(self) -> List[Transaction]:
        """
        Retrieves all transactions sorted chronologically (newest first).
        
        Returns:
            List[Transaction]: List of Transaction objects.
        """
        sql = "SELECT id, date, trans_type, category, amount, description FROM transactions ORDER BY date DESC, id DESC;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Transaction.from_row(row) for row in rows]

    def get_transaction_by_id(self, trans_id: int) -> Optional[Transaction]:
        """
        Retrieves a single transaction by its primary key ID.
        
        Args:
            trans_id (int): Transaction ID.
            
        Returns:
            Optional[Transaction]: Transaction object if found, None otherwise.
        """
        sql = "SELECT id, date, trans_type, category, amount, description FROM transactions WHERE id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (trans_id,))
            row = cursor.fetchone()
            return Transaction.from_row(row) if row else None

    def delete_transaction(self, trans_id: int) -> bool:
        """
        Deletes a transaction from the database by its ID.
        
        Args:
            trans_id (int): The ID of the transaction to delete.
            
        Returns:
            bool: True if a record was deleted, False if ID was not found.
        """
        sql = "DELETE FROM transactions WHERE id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (trans_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================
    # 2. Custom SQL Query Filtering
    # ==========================================

    def get_filtered_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        trans_type: Optional[str] = None,
    ) -> List[Transaction]:
        """
        Filters transactions dynamically based on user-provided criteria using SQL WHERE clauses.
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format (inclusive).
            end_date (str, optional): End date in YYYY-MM-DD format (inclusive).
            category (str, optional): Category name (case-insensitive substring or match).
            trans_type (str, optional): 'Expense' or 'Income'.
            
        Returns:
            List[Transaction]: List of matching Transaction objects.
        """
        query_parts = ["SELECT id, date, trans_type, category, amount, description FROM transactions WHERE 1=1"]
        params: List[Any] = []

        if start_date:
            query_parts.append("AND date >= ?")
            params.append(start_date)

        if end_date:
            query_parts.append("AND date <= ?")
            params.append(end_date)

        if category:
            query_parts.append("AND LOWER(category) LIKE LOWER(?)")
            params.append(f"%{category.strip()}%")

        if trans_type:
            query_parts.append("AND LOWER(trans_type) = LOWER(?)")
            params.append(trans_type.strip())

        query_parts.append("ORDER BY date DESC, id DESC;")
        final_sql = " ".join(query_parts)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(final_sql, tuple(params))
            rows = cursor.fetchall()
            return [Transaction.from_row(row) for row in rows]

    # ==========================================
    # 3. Analytics & Summary Reports
    # ==========================================

    def get_summary(self) -> Dict[str, float]:
        """
        Calculates high-level financial summary using SQL aggregate functions (SUM, COUNT).
        
        Returns:
            dict: Contains 'total_income', 'total_expense', 'net_balance', and 'count'.
        """
        sql = """
        SELECT
            COALESCE(SUM(CASE WHEN trans_type = 'Income' THEN amount ELSE 0 END), 0) AS total_income,
            COALESCE(SUM(CASE WHEN trans_type = 'Expense' THEN amount ELSE 0 END), 0) AS total_expense,
            COUNT(*) AS total_count
        FROM transactions;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            total_income = row[0] if row else 0.0
            total_expense = row[1] if row else 0.0
            total_count = row[2] if row else 0

            return {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_balance": total_income - total_expense,
                "count": total_count,
            }

    def get_category_summary(self, trans_type: str = "Expense") -> List[Dict[str, Any]]:
        """
        Groups spending or income by category using SQL GROUP BY and SUM.
        
        Args:
            trans_type (str): 'Expense' or 'Income' (defaults to 'Expense').
            
        Returns:
            List[Dict]: List of dictionaries with category name, total amount, count, and percentage.
        """
        sql = """
        SELECT
            category,
            SUM(amount) AS total_amount,
            COUNT(*) AS trans_count
        FROM transactions
        WHERE LOWER(trans_type) = LOWER(?)
        GROUP BY category
        ORDER BY total_amount DESC;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (trans_type.strip(),))
            rows = cursor.fetchall()

            # Calculate overall total to compute percentage
            grand_total = sum(row[1] for row in rows) if rows else 0.0

            results = []
            for category, total_amount, count in rows:
                percentage = (total_amount / grand_total * 100.0) if grand_total > 0 else 0.0
                results.append({
                    "category": category,
                    "total_amount": total_amount,
                    "count": count,
                    "percentage": percentage,
                })
            return results

    # ==========================================
    # 4. Automated Keyword-based Categorization
    # ==========================================

    def suggest_category(self, description: str) -> Optional[str]:
        """
        Analyzes a description string and suggests an appropriate category
        based on predefined keyword rules.
        
        Args:
            description (str): Description or memo of the transaction.
            
        Returns:
            Optional[str]: Suggested category name if a keyword match is found, else None.
        """
        if not description:
            return None

        desc_lower = description.lower()
        for category, keywords in self.KEYWORD_CATEGORY_MAP.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category
        return None

    # ==========================================
    # 5. Flat File Handling (CSV Export / Import)
    # ==========================================

    def export_to_csv(self, filepath: str) -> int:
        """
        Exports all transactions to a CSV flat file using Python's standard csv module.
        
        Args:
            filepath (str): Destination path for the CSV file.
            
        Returns:
            int: Number of records exported.
        """
        transactions = self.get_all_transactions()
        headers = ["id", "date", "trans_type", "category", "amount", "description"]

        with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for tx in transactions:
                writer.writerow(tx.to_dict())

        return len(transactions)

    def import_from_csv(self, filepath: str) -> Tuple[int, int]:
        """
        Imports transactions from a CSV file into the SQLite database.
        Validates each row before insertion.
        
        Args:
            filepath (str): Source path of the CSV file.
            
        Returns:
            Tuple[int, int]: (successful_imports_count, error_count)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found.")

        success_count = 0
        error_count = 0

        with open(filepath, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Parse and validate row data
                    date = row.get("date", "").strip()
                    category = row.get("category", "").strip()
                    amount = float(row.get("amount", 0))
                    trans_type = row.get("trans_type", "Expense").strip()
                    description = row.get("description", "").strip()

                    # If category is missing, attempt auto-suggestion
                    if not category and description:
                        category = self.suggest_category(description) or "Miscellaneous"

                    transaction = Transaction(
                        date=date,
                        category=category,
                        amount=amount,
                        description=description,
                        trans_type=trans_type,
                    )
                    self.add_transaction(transaction)
                    success_count += 1
                except (ValueError, KeyError):
                    error_count += 1

        return success_count, error_count
