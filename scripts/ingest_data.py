import json
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.embeddings import get_embeddings

load_dotenv()

DATA_DIR = ROOT / "data"

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST_NAME"),
    "port": os.getenv("PORT", "5432"),
}

BATCH_SIZE = 50

emb = get_embeddings()

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()


def setup_structured_tables():
    """Drop & recreate tables: patients, doctors, patient_doctors, products, orders, payments."""
    print("Setting up structured tables (patients, doctors, patient_doctors, products, orders, payments)...")
    cur.execute(
        """
        DROP TABLE IF EXISTS payments CASCADE;
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS patient_doctors CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS doctors CASCADE;
        DROP TABLE IF EXISTS patients CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        """
    )
    cur.execute(
        """
        CREATE TABLE patients (
            patient_id INT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT,
            CONSTRAINT patients_email_unique UNIQUE (email)
        );
        CREATE TABLE doctors (
            doctor_id INT PRIMARY KEY,
            name TEXT NOT NULL,
            specialty TEXT,
            email TEXT,
            city TEXT
        );
        CREATE TABLE patient_doctors (
            patient_id INT NOT NULL REFERENCES patients(patient_id),
            doctor_id INT NOT NULL REFERENCES doctors(doctor_id),
            relationship TEXT NOT NULL,
            PRIMARY KEY (patient_id, doctor_id, relationship)
        );
        CREATE TABLE products (
            product_id INT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            unit_price NUMERIC,
            requires_prescription TEXT
        );
        CREATE TABLE orders (
            order_id INT PRIMARY KEY,
            patient_id INT NOT NULL REFERENCES patients(patient_id),
            doctor_id INT NOT NULL REFERENCES doctors(doctor_id),
            product_id INT NOT NULL REFERENCES products(product_id),
            quantity INT DEFAULT 1,
            amount NUMERIC,
            status TEXT
        );
        CREATE TABLE payments (
            payment_id INT PRIMARY KEY,
            order_id INT NOT NULL REFERENCES orders(order_id),
            payment_method TEXT,
            payment_status TEXT
        );
        """
    )
    conn.commit()

    patients_df = pd.read_csv(DATA_DIR / "patients.csv")
    doctors_df = pd.read_csv(DATA_DIR / "doctors.csv")
    patient_doctors_df = pd.read_csv(DATA_DIR / "patient_doctors.csv")
    products_df = pd.read_csv(DATA_DIR / "products.csv")
    orders_df = pd.read_csv(DATA_DIR / "orders.csv")
    payments_df = pd.read_csv(DATA_DIR / "payments.csv")

    for _, row in patients_df.iterrows():
        cur.execute(
            "INSERT INTO patients (patient_id, name, email, city) VALUES (%s, %s, %s, %s)",
            (int(row["patient_id"]), row["name"], row["email"], row["city"]),
        )
    for _, row in doctors_df.iterrows():
        cur.execute(
            "INSERT INTO doctors (doctor_id, name, specialty, email, city) VALUES (%s, %s, %s, %s, %s)",
            (int(row["doctor_id"]), row["name"], row["specialty"], row["email"], row["city"]),
        )
    for _, row in patient_doctors_df.iterrows():
        cur.execute(
            """
            INSERT INTO patient_doctors (patient_id, doctor_id, relationship)
            VALUES (%s, %s, %s)
            """,
            (int(row["patient_id"]), int(row["doctor_id"]), str(row["relationship"])),
        )
    for _, row in products_df.iterrows():
        cur.execute(
            "INSERT INTO products (product_id, name, category, unit_price, requires_prescription) VALUES (%s, %s, %s, %s, %s)",
            (
                int(row["product_id"]),
                row["name"],
                row["category"],
                float(row["unit_price"]),
                str(row["requires_prescription"]),
            ),
        )
    for _, row in orders_df.iterrows():
        cur.execute(
            """
            INSERT INTO orders (order_id, patient_id, doctor_id, product_id, quantity, amount, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                int(row["order_id"]),
                int(row["patient_id"]),
                int(row["doctor_id"]),
                int(row["product_id"]),
                int(row["quantity"]),
                float(row["amount"]),
                row["status"],
            ),
        )
    for _, row in payments_df.iterrows():
        cur.execute(
            "INSERT INTO payments (payment_id, order_id, payment_method, payment_status) VALUES (%s, %s, %s, %s)",
            (
                int(row["payment_id"]),
                int(row["order_id"]),
                row["payment_method"],
                row["payment_status"],
            ),
        )
    conn.commit()
    print("Structured tables loaded from CSV.")


def setup_database():
    print("Setting up vector table...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        content TEXT,
        embedding VECTOR(1536),
        metadata JSONB
    );
    """
    )
    conn.commit()
    print("Vector table ready")


def clear_documents():
    cur.execute("TRUNCATE TABLE documents RESTART IDENTITY CASCADE;")
    conn.commit()
    print("Cleared documents for re-embedding")


def create_index():
    print("Creating vector index...")
    cur.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
    """
    )
    conn.commit()
    print("Index created")


def patient_to_text(row):
    return (
        f"Patient {row['name']} (patient id {row['patient_id']}) has email {row['email']} "
        f"and lives in {row['city']}."
    )


def doctor_to_text(row):
    return (
        f"Doctor {row['name']} (doctor id {row['doctor_id']}), specialty {row['specialty']}, "
        f"email {row['email']}, city {row['city']}."
    )


def product_to_text(row):
    return (
        f"Product / medicine {row['name']} (product id {row['product_id']}) is a {row['category']}, "
        f"unit price {row['unit_price']}, prescription required: {row['requires_prescription']}."
    )


def order_to_text(row):
    return (
        f"Order {row['order_id']} for patient {row['patient_name']} (patient id {row['patient_id']}) "
        f"with doctor {row['doctor_name']} (doctor id {row['doctor_id']}), "
        f"medicine {row['product_name']} (product id {row['product_id']}), quantity {row['quantity']}, "
        f"status {row['status']}, amount {row['amount']}."
    )


def patient_doctor_to_text(row):
    return (
        f"Patient id {row['patient_id']} ({row['relationship']} care) is linked to "
        f"{row['doctor_name']} (doctor id {row['doctor_id']}), specialty {row['specialty']}."
    )


def payment_to_text(row):
    return (
        f"Payment {row['payment_id']} for order {row['order_id']} via {row['payment_method']}, "
        f"status {row['payment_status']}."
    )


def load_all_data():
    patients_df = pd.read_csv(DATA_DIR / "patients.csv")
    doctors_df = pd.read_csv(DATA_DIR / "doctors.csv")
    patient_doctors_df = pd.read_csv(DATA_DIR / "patient_doctors.csv")
    products_df = pd.read_csv(DATA_DIR / "products.csv")
    orders_df = pd.read_csv(DATA_DIR / "orders.csv")
    payments_df = pd.read_csv(DATA_DIR / "payments.csv")

    merged_orders = orders_df.merge(
        patients_df.rename(columns={"name": "patient_name"}),
        on="patient_id",
    ).merge(doctors_df.rename(columns={"name": "doctor_name"}), on="doctor_id").merge(
        products_df.rename(columns={"name": "product_name"}),
        on="product_id",
    )
    pd_merged = patient_doctors_df.merge(
        doctors_df.rename(columns={"name": "doctor_name"}),
        on="doctor_id",
    )

    texts = []
    for _, row in patients_df.iterrows():
        texts.append(patient_to_text(row))
    for _, row in doctors_df.iterrows():
        texts.append(doctor_to_text(row))
    for _, row in pd_merged.iterrows():
        texts.append(patient_doctor_to_text(row))
    for _, row in products_df.iterrows():
        texts.append(product_to_text(row))
    for _, row in merged_orders.iterrows():
        texts.append(order_to_text(row))
    for _, row in payments_df.iterrows():
        texts.append(payment_to_text(row))

    return texts


def insert_batch(texts, vectors):
    for text, vector in zip(texts, vectors):
        cur.execute(
            "INSERT INTO documents (content, embedding, metadata) VALUES (%s, %s, %s)",
            (text, vector, json.dumps({})),
        )
    conn.commit()


def run_ingestion():
    setup_structured_tables()
    setup_database()
    clear_documents()

    all_texts = load_all_data()
    print(f"Total RAG text records: {len(all_texts)}")

    for i in range(0, len(all_texts), BATCH_SIZE):
        batch = all_texts[i : i + BATCH_SIZE]
        print(f"Embedding batch {i // BATCH_SIZE + 1}")
        vectors = emb.embed_documents(batch)
        insert_batch(batch, vectors)

    create_index()
    print("Data ingestion completed successfully!")


if __name__ == "__main__":
    try:
        os.chdir(ROOT)
        run_ingestion()
    except Exception as e:
        print("Error:", e)
        raise
    finally:
        cur.close()
        conn.close()
