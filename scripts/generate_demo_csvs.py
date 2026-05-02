"""
Generate larger demo CSVs (~50 patients, ~50 doctors, care-team links, ~120 orders).
Run from repo root:  python scripts/generate_demo_csvs.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

N_PATIENTS = 50
N_DOCTORS = 50
N_PRODUCTS = 40
N_ORDERS = 120

SPECIALTIES = [
    "Cardiology",
    "Pediatrics",
    "General Medicine",
    "Orthopedics",
    "Dermatology",
    "ENT",
    "Ophthalmology",
    "Gynecology",
    "Psychiatry",
    "Neurology",
]
CITIES = [
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
]

FIRST = (
    "Aarav,Aditya,Arjun,Dev,Ishaan,Kabir,Karan,Rohan,Vivaan,Yash,"
    "Ananya,Diya,Kavya,Meera,Neha,Priya,Riya,Sara,Tanvi,Vidya"
).split(",")
LAST = (
    "Sharma,Verma,Patel,Singh,Gupta,Reddy,Iyer,Kapoor,Menon,Joshi,"
    "Nair,Desai,Khan,Mehta,Agarwal,Bose,Chawla,Das,Kulkarni,Rao"
).split(",")


def slug(s: str) -> str:
    return s.lower().replace(".", "").replace(" ", ".")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    doctor_id_start = 201
    patient_id_start = 1
    product_id_start = 301
    order_id_start = 5001
    payment_id_start = 9001

    doctors_rows = []
    for i in range(N_DOCTORS):
        did = doctor_id_start + i
        fn = FIRST[i % len(FIRST)]
        ln = LAST[(i * 3) % len(LAST)]
        name = f"Dr. {fn} {ln}"
        sp = SPECIALTIES[i % len(SPECIALTIES)]
        city = CITIES[i % len(CITIES)]
        email = f"{slug(fn)}.{slug(ln)}{did}@clinic.demo"
        doctors_rows.append(
            {"doctor_id": did, "name": name, "specialty": sp, "email": email, "city": city}
        )

    patients_rows = []
    for i in range(N_PATIENTS):
        pid = patient_id_start + i
        fn = FIRST[(i + 5) % len(FIRST)]
        ln = LAST[(i + 7) % len(LAST)]
        name = f"{fn} {ln}"
        city = CITIES[(i + 2) % len(CITIES)]
        email = f"patient{pid}@demo.clinic"
        patients_rows.append(
            {"patient_id": pid, "name": name, "email": email, "city": city}
        )

    legacy = [
        ("Amit Sharma", "amit@example.com", "Delhi"),
        ("Riya Singh", "riya@example.com", "Mumbai"),
        ("Arjun Verma", "arjun@example.com", "Bangalore"),
        ("Neha Gupta", "neha@example.com", "Pune"),
        ("Karan Mehta", "karan@example.com", "Gurgaon"),
    ]
    for i, (nm, em, ct) in enumerate(legacy):
        patients_rows[i]["name"] = nm
        patients_rows[i]["email"] = em
        patients_rows[i]["city"] = ct

    # Care team: primary + optional consulting (different doctor)
    pd_rows = []
    for row in patients_rows:
        pid = int(row["patient_id"])
        primary_doc = doctor_id_start + ((pid - 1) % N_DOCTORS)
        pd_rows.append(
            {"patient_id": pid, "doctor_id": primary_doc, "relationship": "primary"}
        )
        if pid % 2 == 0:
            consult = doctor_id_start + ((pid + 19) % N_DOCTORS)
            if consult != primary_doc:
                pd_rows.append(
                    {"patient_id": pid, "doctor_id": consult, "relationship": "consulting"}
                )

    products_rows = []
    categories = ["Tablet", "Syrup", "Injection", "Ointment", "Capsule"]
    for j in range(N_PRODUCTS):
        pid = product_id_start + j
        products_rows.append(
            {
                "product_id": pid,
                "name": f"MediCare Product {pid}",
                "category": categories[j % 5],
                "unit_price": round(25 + (j * 13) % 800 + j * 0.5, 2),
                "requires_prescription": "yes" if j % 3 else "no",
            }
        )

    orders_rows = []
    statuses = ["delivered", "pending", "shipped", "cancelled"]
    for k in range(N_ORDERS):
        oid = order_id_start + k
        pat_id = patient_id_start + (k % N_PATIENTS)
        # Mix: often primary, sometimes another attending from care team or rotating doc
        primary_doc = doctor_id_start + ((pat_id - 1) % N_DOCTORS)
        alt_doc = doctor_id_start + ((pat_id + k + 3) % N_DOCTORS)
        doc_id = primary_doc if (k % 4) != 0 else alt_doc
        prd = product_id_start + (k % N_PRODUCTS)
        qty = 1 + (k % 4)
        amt = round(float(30 + (k * 17) % 900) * qty, 2)
        orders_rows.append(
            {
                "order_id": oid,
                "patient_id": pat_id,
                "doctor_id": doc_id,
                "product_id": prd,
                "quantity": qty,
                "amount": amt,
                "status": statuses[k % 4],
            }
        )

    payments_rows = []
    methods = ["UPI", "card", "cash", "netbanking"]
    pstats = ["completed", "completed", "pending", "failed"]
    for k in range(N_ORDERS):
        payments_rows.append(
            {
                "payment_id": payment_id_start + k,
                "order_id": order_id_start + k,
                "payment_method": methods[k % 4],
                "payment_status": pstats[k % 4],
            }
        )

    def write(name: str, rows: list, fieldnames: list[str]) -> None:
        path = DATA / name
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {path} ({len(rows)} rows)")

    write("doctors.csv", doctors_rows, ["doctor_id", "name", "specialty", "email", "city"])
    write("patients.csv", patients_rows, ["patient_id", "name", "email", "city"])
    write(
        "patient_doctors.csv",
        pd_rows,
        ["patient_id", "doctor_id", "relationship"],
    )
    write(
        "products.csv",
        products_rows,
        ["product_id", "name", "category", "unit_price", "requires_prescription"],
    )
    write(
        "orders.csv",
        orders_rows,
        ["order_id", "patient_id", "doctor_id", "product_id", "quantity", "amount", "status"],
    )
    write(
        "payments.csv",
        payments_rows,
        ["payment_id", "order_id", "payment_method", "payment_status"],
    )


if __name__ == "__main__":
    main()
