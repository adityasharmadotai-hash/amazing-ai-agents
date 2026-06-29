"""Create a sample SQLite database for the AI Database Analyst.

Generates a small, realistic e-commerce schema (customers, employees, products,
orders, order_items, users) with seeded data so that the example questions in
the README work out of the box.

Usage:
    python scripts/create_sample_db.py
    python scripts/create_sample_db.py --path sample_data/northwind.db
"""

from __future__ import annotations

import argparse
import os
import random
import sqlite3
from datetime import date, datetime, timedelta

RANDOM_SEED = 42

CATEGORIES = ["Beverages", "Condiments", "Confections", "Dairy", "Grains", "Produce", "Seafood"]
COUNTRIES = ["USA", "UK", "Germany", "France", "Canada", "Australia", "India", "Brazil"]
FIRST_NAMES = ["Alice", "Bob", "Carla", "David", "Elena", "Frank", "Grace", "Hugo", "Iris", "Jack",
               "Kara", "Liam", "Mona", "Nate", "Olivia", "Pedro", "Quinn", "Rosa", "Sam", "Tara"]
LAST_NAMES = ["Smith", "Johnson", "Lee", "Brown", "Garcia", "Müller", "Dubois", "Rossi",
              "Patel", "Chen", "Kim", "Nguyen", "Silva", "Khan", "Ivanov"]


def _schema(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS users;

        CREATE TABLE customers (
            customer_id   INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL,
            country       TEXT NOT NULL,
            created_at    TEXT NOT NULL
        );

        CREATE TABLE employees (
            employee_id   INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL,
            title         TEXT NOT NULL,
            hire_date     TEXT NOT NULL,
            region        TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id    INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            category      TEXT NOT NULL,
            unit_price    REAL NOT NULL,
            unit_cost     REAL NOT NULL,
            in_stock      INTEGER NOT NULL
        );

        CREATE TABLE orders (
            order_id      INTEGER PRIMARY KEY,
            customer_id   INTEGER NOT NULL,
            employee_id   INTEGER NOT NULL,
            order_date    TEXT NOT NULL,
            status        TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id      INTEGER NOT NULL,
            product_id    INTEGER NOT NULL,
            quantity      INTEGER NOT NULL,
            unit_price    REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT NOT NULL,
            email         TEXT NOT NULL,
            last_login    TEXT,
            is_active     INTEGER NOT NULL
        );

        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_order_items_order ON order_items(order_id);
        """
    )


def _seed(cur: sqlite3.Cursor) -> None:
    rng = random.Random(RANDOM_SEED)
    today = date.today()

    # Customers
    customers = []
    for cid in range(1, 61):
        fn = rng.choice(FIRST_NAMES)
        ln = rng.choice(LAST_NAMES)
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{cid}@example.com"
        created = today - timedelta(days=rng.randint(30, 900))
        customers.append((cid, name, email, rng.choice(COUNTRIES), created.isoformat()))
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

    # Employees
    titles = ["Sales Rep", "Senior Sales Rep", "Account Manager", "Sales Manager"]
    regions = ["North", "South", "East", "West"]
    employees = []
    for eid in range(1, 11):
        fn = rng.choice(FIRST_NAMES)
        ln = rng.choice(LAST_NAMES)
        hire = today - timedelta(days=rng.randint(200, 2500))
        employees.append(
            (eid, f"{fn} {ln}", f"{fn.lower()}.{ln.lower()}@company.com",
             rng.choice(titles), hire.isoformat(), rng.choice(regions))
        )
    cur.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", employees)

    # Products
    products = []
    for pid in range(1, 41):
        price = round(rng.uniform(5, 120), 2)
        cost = round(price * rng.uniform(0.4, 0.8), 2)
        products.append(
            (pid, f"Product {pid:02d}", rng.choice(CATEGORIES), price, cost, rng.randint(0, 500))
        )
    cur.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)

    # Orders + items (including some for "today" so "today's sales" returns rows)
    statuses = ["completed", "completed", "completed", "shipped", "pending", "cancelled"]
    orders = []
    items = []
    item_id = 1
    for oid in range(1, 401):
        cust = rng.randint(1, 60)
        emp = rng.randint(1, 10)
        if oid <= 8:
            order_date = today  # guarantee some "today" sales
        else:
            order_date = today - timedelta(days=rng.randint(0, 365))
        status = rng.choice(statuses)
        orders.append((oid, cust, emp, order_date.isoformat(), status))
        for _ in range(rng.randint(1, 5)):
            pid = rng.randint(1, 40)
            qty = rng.randint(1, 10)
            unit_price = round(rng.uniform(5, 120), 2)
            items.append((item_id, oid, pid, qty, unit_price))
            item_id += 1
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
    cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)

    # Users (with some inactive / stale logins and intentional duplicate emails)
    users = []
    for uid in range(1, 81):
        fn = rng.choice(FIRST_NAMES)
        username = f"{fn.lower()}{uid}"
        email = f"{fn.lower()}@mail.com"  # duplicates by design -> "find duplicate users"
        if rng.random() < 0.2:
            last_login = None
        else:
            last_login = (datetime.now() - timedelta(days=rng.randint(0, 200))).isoformat()
        is_active = 0 if rng.random() < 0.25 else 1
        users.append((uid, username, email, last_login, is_active))
    cur.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users)


def create_sample_db(path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        _schema(cur)
        _seed(cur)
        conn.commit()
    finally:
        conn.close()
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the sample SQLite database.")
    parser.add_argument("--path", default="sample_data/northwind.db", help="Output DB path.")
    args = parser.parse_args()
    out = create_sample_db(args.path)
    size = os.path.getsize(out)
    print(f"[OK] Sample database created at {out} ({size/1024:.1f} KB)")
    print("     Tables: customers, employees, products, orders, order_items, users")


if __name__ == "__main__":
    main()
