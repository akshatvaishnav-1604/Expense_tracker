"""
models.py
---------
Defines the data models for the Expense Tracker.
Demonstrates Object-Oriented Programming (OOP) concepts such as:
  - Class definition & Encapsulation
  - Constructor (__init__) and object initialization
  - Data validation methods
  - String representation (__str__, __repr__)
  - Factory/serialization methods (to_dict, from_row)
"""

from datetime import datetime


class Transaction:
    """
    Represents an individual financial transaction (Income or Expense).
    
    Attributes:
        id (int | None): Unique identifier assigned by the database (None if not yet saved).
        date (str): Date of transaction in YYYY-MM-DD format.
        trans_type (str): 'Income' or 'Expense'.
        category (str): Category (e.g., 'Groceries', 'Salary', 'Transport').
        amount (float): Monetary value of the transaction.
        description (str): Short description/note for the transaction.
    """

    VALID_TYPES = ("Expense", "Income")

    def __init__(
        self,
        date: str,
        category: str,
        amount: float,
        description: str = "",
        trans_type: str = "Expense",
        trans_id: int | None = None,
    ):
        """
        Initializes a new Transaction instance.
        """
        self.id = trans_id
        self.date = date
        self.trans_type = trans_type.strip().capitalize()
        self.category = category.strip()
        self.amount = float(amount)
        self.description = description.strip()

        # Validate attributes upon creation
        self.validate()

    def validate(self) -> None:
        """
        Validates the transaction's fields to maintain data integrity.
        Raises ValueError if any field is invalid.
        """
        # Validate Transaction Type
        if self.trans_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid transaction type '{self.trans_type}'. Must be one of {self.VALID_TYPES}."
            )

        # Validate Amount (must be positive)
        if self.amount <= 0:
            raise ValueError("Amount must be a positive number greater than 0.")

        # Validate Date format (YYYY-MM-DD)
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid date format '{self.date}'. Please use YYYY-MM-DD format (e.g., 2026-03-15)."
            )

        # Validate Category
        if not self.category:
            raise ValueError("Category cannot be empty.")

    def to_dict(self) -> dict:
        """
        Converts the Transaction object into a dictionary.
        Useful for JSON or CSV serialization.
        """
        return {
            "id": self.id,
            "date": self.date,
            "trans_type": self.trans_type,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Transaction":
        """
        Factory method: Creates a Transaction object from a SQLite database row tuple.
        Expected tuple format: (id, date, trans_type, category, amount, description)
        """
        return cls(
            trans_id=row[0],
            date=row[1],
            trans_type=row[2],
            category=row[3],
            amount=row[4],
            description=row[5] if len(row) > 5 else "",
        )

    def __str__(self) -> str:
        """
        Returns a user-friendly string representation of the transaction.
        """
        id_str = f"#{self.id}" if self.id else "#New"
        return f"[{id_str}] {self.date} | {self.trans_type.upper():<7} | {self.category:<15} | ${self.amount:>8.2f} | {self.description}"

    def __repr__(self) -> str:
        """
        Returns an unambiguous string representation for debugging.
        """
        return (
            f"Transaction(id={self.id}, date='{self.date}', trans_type='{self.trans_type}', "
            f"category='{self.category}', amount={self.amount}, description='{self.description}')"
        )
