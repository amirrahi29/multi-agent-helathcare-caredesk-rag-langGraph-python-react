import os
import re

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST_NAME"),
    "port": os.getenv("PORT", "5432"),
}


def extract_id(query: str):
    numbers = re.findall(r"\d+", query or "")
    return numbers[0] if numbers else None


def _sql_order_detail(cur, order_id: str) -> str | None:
    cur.execute(
        """
        SELECT o.order_id, o.status, o.amount, o.quantity,
               p.name AS product, u.name AS patient, d.name AS doctor
        FROM orders o
        JOIN products p ON p.product_id = o.product_id
        JOIN patients u ON u.patient_id = o.patient_id
        JOIN doctors d ON d.doctor_id = o.doctor_id
        WHERE o.order_id = %s
        """,
        (int(order_id),),
    )
    row = cur.fetchone()
    if not row:
        return None
    oid, status, amount, qty, product, patient, doctor = row
    return (
        f"Order {oid}: patient {patient}, doctor {doctor}, medicine {product} "
        f"(qty {qty}), status {status}, amount {amount}."
    )


def _rag_fallback_order(cur, order_id: str) -> str | None:
    cur.execute(
        "SELECT content FROM documents WHERE content ILIKE %s LIMIT 1",
        (f"%Order {order_id}%",),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _sql_payment_detail(cur, payment_id: str) -> str | None:
    cur.execute(
        """
        SELECT p.payment_id, p.payment_method, p.payment_status, p.order_id,
               o.status AS order_status
        FROM payments p
        JOIN orders o ON o.order_id = p.order_id
        WHERE p.payment_id = %s
        """,
        (int(payment_id),),
    )
    row = cur.fetchone()
    if not row:
        return None
    pid, method, pay_status, oid, ord_status = row
    return (
        f"Payment {pid} for order {oid}: method {method}, payment status {pay_status}; "
        f"order status {ord_status}."
    )


def tool_agent(state: dict) -> dict:
    query = state.get("query")
    intent = state.get("intent")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    result = None

    try:
        if intent == "order_status":
            order_id = extract_id(query)
            if not order_id:
                result = "Order id not found in message"
            else:
                result = _sql_order_detail(cur, order_id)
                if result is None:
                    result = _rag_fallback_order(cur, order_id)
                if result is None:
                    result = "Order not found"

        elif intent == "order_owner":
            order_id = extract_id(query)
            if not order_id:
                result = "Order id not found in message"
            else:
                cur.execute(
                    """
                    SELECT u.name
                    FROM orders o
                    JOIN patients u ON u.patient_id = o.patient_id
                    WHERE o.order_id = %s
                    """,
                    (int(order_id),),
                )
                row = cur.fetchone()
                if row:
                    result = row[0]
                else:
                    result = _rag_fallback_order(cur, order_id)
                if result is None:
                    result = "Order not found"

        elif intent == "payment_status":
            payment_id = extract_id(query)
            if not payment_id:
                result = "Payment id not found in message"
            else:
                result = _sql_payment_detail(cur, payment_id)
                if result is None:
                    cur.execute(
                        "SELECT content FROM documents WHERE content ILIKE %s LIMIT 1",
                        (f"%Payment {payment_id}%",),
                    )
                    row = cur.fetchone()
                    result = row[0] if row else "Payment not found"

        elif intent in ("count_patients", "count_users"):
            cur.execute("SELECT COUNT(*) FROM patients")
            row = cur.fetchone()
            result = row[0] if row is not None else 0

        elif intent in ("list_patients", "list_users"):
            cur.execute(
                "SELECT patient_id, name, email FROM patients ORDER BY name"
            )
            rows = cur.fetchall()
            result = (
                [f"{r[1]} — {r[2]} (patient id {r[0]})" for r in rows]
                if rows
                else []
            )

        elif intent == "my_session_doctors":
            sid = state.get("patient_id")
            if sid is None:
                result = "No signed-in patient in this session."
            else:
                cur.execute(
                    """
                    WITH link_labels AS (
                        SELECT DISTINCT doctor_id, relationship AS lbl
                        FROM patient_doctors
                        WHERE patient_id = %s
                        UNION
                        SELECT DISTINCT o.doctor_id, 'order_attending'::text
                        FROM orders o
                        WHERE o.patient_id = %s
                    ),
                    agg AS (
                        SELECT doctor_id, string_agg(lbl, ', ' ORDER BY lbl) AS how
                        FROM link_labels
                        GROUP BY doctor_id
                    )
                    SELECT d.doctor_id, d.name, d.specialty, d.email, d.city, agg.how
                    FROM agg
                    JOIN doctors d ON d.doctor_id = agg.doctor_id
                    ORDER BY d.name
                    """,
                    (int(sid), int(sid)),
                )
                rows = cur.fetchall()
                if not rows:
                    result = (
                        "No doctors linked for this patient in care-team assignments or orders."
                    )
                else:
                    result = [
                        f"{r[1]} (doctor id {r[0]}): {r[2]}, {r[3]}, {r[4]} "
                        f"[links: {r[5]}]"
                        for r in rows
                    ]

        elif intent == "my_session_medicines":
            sid = state.get("patient_id")
            if sid is None:
                result = "No signed-in patient in this session."
            else:
                cur.execute(
                    """
                    SELECT o.order_id, p.name, p.product_id, d.name, d.doctor_id,
                           o.status, o.quantity, o.amount
                    FROM orders o
                    JOIN products p ON p.product_id = o.product_id
                    JOIN doctors d ON d.doctor_id = o.doctor_id
                    WHERE o.patient_id = %s
                    ORDER BY o.order_id DESC
                    LIMIT 50
                    """,
                    (int(sid),),
                )
                rows = cur.fetchall()
                if not rows:
                    result = "No orders or prescribed items on record for this patient."
                else:
                    result = [
                        f"Order {r[0]}: {r[1]} (product id {r[2]}) — Dr. {r[3]} (id {r[4]}), "
                        f"status {r[5]}, qty {r[6]}, amount {r[7]}"
                        for r in rows
                    ]

        elif intent == "count_doctors":
            cur.execute("SELECT COUNT(*) FROM doctors")
            row = cur.fetchone()
            result = row[0] if row is not None else 0

        elif intent == "list_doctors":
            cur.execute(
                "SELECT doctor_id, name, specialty, city FROM doctors ORDER BY name"
            )
            rows = cur.fetchall()
            result = (
                [f"{r[1]} — {r[2]}, {r[3]} (doctor id {r[0]})" for r in rows]
                if rows
                else []
            )

        elif intent == "doctor_detail":
            doc_id = extract_id(query)
            if not doc_id:
                result = "Doctor id not found in message"
            else:
                cur.execute(
                    """
                    SELECT doctor_id, name, specialty, email, city
                    FROM doctors WHERE doctor_id = %s
                    """,
                    (int(doc_id),),
                )
                row = cur.fetchone()
                if row:
                    result = (
                        f"Doctor {row[1]} (id {row[0]}): specialty {row[2]}, "
                        f"{row[3]}, {row[4]}."
                    )
                else:
                    result = "Doctor not found"

        elif intent == "count_products":
            cur.execute("SELECT COUNT(*) FROM products")
            row = cur.fetchone()
            result = row[0] if row is not None else 0

        elif intent == "list_products":
            cur.execute(
                "SELECT product_id, name, category, unit_price, requires_prescription "
                "FROM products ORDER BY name"
            )
            rows = cur.fetchall()
            result = [
                f"{r[1]} ({r[2]}) — ₹{r[3]}, rx: {r[4]} (id {r[0]})"
                for r in rows
            ] if rows else []

        elif intent == "product_detail":
            pid = extract_id(query)
            if not pid:
                result = "Product id not found in message"
            else:
                cur.execute(
                    """
                    SELECT product_id, name, category, unit_price, requires_prescription
                    FROM products WHERE product_id = %s
                    """,
                    (int(pid),),
                )
                row = cur.fetchone()
                if row:
                    result = (
                        f"Product {row[1]} (id {row[0]}): {row[2]}, "
                        f"unit price {row[3]}, prescription required: {row[4]}."
                    )
                else:
                    result = "Product not found"

        elif intent == "count_orders":
            cur.execute("SELECT COUNT(*) FROM orders")
            row = cur.fetchone()
            result = row[0] if row is not None else 0

        elif intent == "list_orders":
            cur.execute(
                """
                SELECT o.order_id, o.status, o.amount, p.name
                FROM orders o
                JOIN products p ON p.product_id = o.product_id
                ORDER BY o.order_id
                """
            )
            rows = cur.fetchall()
            result = [f"Order {r[0]}: {r[3]} — {r[1]}, ₹{r[2]}" for r in rows] if rows else []

        else:
            result = "Unsupported structured query"

    except Exception as e:
        conn.rollback()
        result = f"Error: {str(e)}"

    finally:
        cur.close()
        conn.close()

    return {"tool_data": result}
