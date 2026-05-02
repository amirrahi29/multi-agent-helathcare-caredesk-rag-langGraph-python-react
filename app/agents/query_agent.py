from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import re

# Load env
load_dotenv()

# LLM init
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

_CONFIRM_RE = re.compile(
    r"^(yes|yeah|yep|yup|ok(ay)?|sure|haa?n?|theek|thik|go ahead|continue|proceed)\s*[\.\!\?]*$",
    re.I,
)

# First-person / care-desk "your doctor" → must use session patient + orders join, not RAG-only.
_MY_DOCTOR_RE = re.compile(
    r"\b(my|me|mine|main|mera|meri|mere|apna|apne|apni)\b.{0,60}\b(doctor|dr\.?|physician|doc|डॉ)\b|"
    r"\b(doctor|dr\.?|physician|doc|डॉ)\b.{0,60}\b(my|me|mine|main|mera|meri|mere|apna|apne|apni)\b|"
    r"\bwho\s+is\s+my\s+doctor\b|\bwhich\s+doctor\s+(do\s+i\s+have|for\s+me)\b|"
    r"मेरा\s+डॉ|मेरे\s+डॉ|अपना\s+डॉ|डॉ\s+कौन|doctor\s+kaun|"
    r"\baapka\s+doctor\b|\bआपका\s+डॉ\b|"
    # Implicit "my" doctor on signed-in patient portal (no मेरा needed)
    r"डॉक्टर\s+का\s+नाम|डॉ\s+का\s+नाम|doctor\s+ka\s+naam|डॉक्टर\s+कौन|कौन\s+सा\s+डॉक्टर",
    re.I,
)

# Medicines tied to this patient’s care (orders) — not document RAG.
_MY_MEDICINES_RE = re.compile(
    r"(मेडिसिन|दवा|दवाएं|medicine|medication|prescri|सजेस्ट|suggest|कौन\s+कौन\s+सी).{0,80}"
    r"(डॉ|doctor|dr\.?|इस\s+डॉ|this\s+doctor)|"
    r"(इस\s+डॉ|डॉ ने|doctor).{0,80}(मेडिसिन|दवा|medicine|suggest|सजेस्ट)|"
    r"\bmy\s+medicines\b|\bmeri\s+davaa?\b|\bmujhe\s+kis\s+davaa",
    re.I,
)

# Contact details for providers — structured when we already discussed doctors.
_CONTACT_DETAIL_RE = re.compile(
    r"ईमेल|इ-मेल|email|e-?mail|संपर्क|contact|फोन|phone|कॉल|call|कनेक्ट|connect|reach",
    re.I,
)
_THEIR_PRONOUN_RE = re.compile(r"इनका|उनका|इन्हें|उन्हें|unke|inka|unka|their|them|these\s+doctors", re.I)


def _history_blob(history: list | None, max_messages: int = 8) -> str:
    if not history:
        return ""
    tail = history[-max_messages:]
    parts = []
    for m in tail:
        c = (m.get("content") or "").strip()
        if c:
            parts.append(c)
    return "\n".join(parts)


def _history_mentions_doctor(history: list | None) -> bool:
    blob = _history_blob(history).lower()
    return (
        "doctor" in blob
        or "dr." in blob
        or "physician" in blob
        or "डॉ" in blob
        or "डॉक्टर" in blob
    )


# -----------------------------
# Helper: Extract JSON safely
# -----------------------------
def extract_json(text: str) -> str:
    """
    Extract JSON object from LLM response safely
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return "{}"


def _format_history_tail(history: list | None, max_messages: int = 8) -> str:
    if not history:
        return "(no prior messages)"
    tail = history[-max_messages:]
    lines = []
    for m in tail:
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(no prior messages)"


# -----------------------------
# Query Agent
# -----------------------------
def query_agent(state: dict) -> dict:
    query = (state.get("query") or "").strip()
    history = state.get("history") or []

    if not query:
        return {
            "intent": "unknown",
            "type": "rag"
        }

    if _CONFIRM_RE.match(query.strip()):
        return {
            "intent": "confirmation",
            "type": "rag"
        }

    pid = state.get("patient_id")

    if pid is not None and _MY_DOCTOR_RE.search(query):
        return {
            "intent": "my_session_doctors",
            "type": "structured"
        }

    if pid is not None and _MY_MEDICINES_RE.search(query):
        return {
            "intent": "my_session_medicines",
            "type": "structured"
        }

    # Doctor contact (email/phone) — structured; avoids RAG returning unrelated patient rows.
    if pid is not None and _CONTACT_DETAIL_RE.search(query):
        patient_own_email_only = bool(
            re.search(r"\b(mera|meri|mere|मेरा|मेरी|मेरे)\s+(ईमेल|email)\b", query, re.I)
        ) and not re.search(r"डॉक्टर|डॉ\.?|doctor|dr\.?", query, re.I)
        doctor_in_query = bool(
            re.search(
                r"(डॉक्टर|डॉ\.?|doctor|dr\.?).{0,80}(ईमेल|email|संपर्क|contact|फोन|phone)|"
                r"(ईमेल|email|संपर्क|contact|फोन|phone).{0,50}(डॉक्टर|डॉ\.?|doctor|dr\.?)",
                query,
                re.I,
            )
        ) or bool(
            re.search(r"डॉक्टर|डॉ\.?|doctor|dr\.?", query, re.I)
            and re.search(r"कनेक्ट|connect|reach", query, re.I)
        )
        followup_contact = bool(
            _history_mentions_doctor(history) and len(query) <= 96 and not patient_own_email_only
        )
        if not patient_own_email_only and (
            _THEIR_PRONOUN_RE.search(query)
            or doctor_in_query
            or followup_contact
        ):
            return {
                "intent": "my_session_doctors",
                "type": "structured"
            }

    if re.search(r"\(order\s+\d+\)", query, re.I) and re.search(
        r"किस\s*यूजर|whose\s*(order|user)?|which\s*user|यह\s+किस|किसका",
        query,
        re.I,
    ):
        return {
            "intent": "order_owner",
            "type": "structured"
        }

    transcript = _format_history_tail(history)

    session_hint = ""
    if state.get("patient_id") is not None:
        session_hint = (
            f"\nSession: user is logged in as patient_id={state['patient_id']}, "
            f"name={state.get('patient_name') or 'unknown'}."
        )

    prompt = f"""
You are an intent classifier for a healthcare / pharmacy assistant (patients, doctors, medicines/products, orders, payments).

Use the recent conversation for context when the latest message is short, ambiguous, or a follow-up.
{session_hint}

Return ONLY valid JSON. No explanation. No markdown.

Schema:
{{
  "intent": "...",
  "type": "structured" or "rag"
}}

Intents (structured = exact DB lookup; rag = semantic search on documents):
- Order status (order id present) → order_status, structured
- Who owns order / which patient placed order X → order_owner, structured
- Payment status (payment id present) → payment_status, structured
- Count patients → count_patients, structured
- List all patients → list_patients, structured
- The logged-in patient asks who is THEIR doctor (my/mera/apna doctor, डॉक्टर का नाम क्या है on a patient portal, aapka doctor to the patient, who is my doctor) → my_session_doctors, structured (requires session patient_id)
- Logged-in patient asks which medicines this doctor suggested / prescribed for them (includes इस डॉक्टर ने मुझे … मेडिसिन) → my_session_medicines, structured
- Short follow-up asking for doctor email / contact / phone after doctor was discussed → my_session_doctors, structured (not rag)
- Count doctors → count_doctors, structured
- List all doctors → list_doctors, structured
- One doctor by id (e.g. doctor 201, Dr id 201) → doctor_detail, structured
- Count products / medicines / SKUs → count_products, structured
- List products / medicines / catalog → list_products, structured
- One product by id (product 301, medicine id 302) → product_detail, structured
- Count orders → count_orders, structured
- List all orders → list_orders, structured
- Single patient profile / where does X live / email of patient (no structured list) → patient_info, rag
- Doctor by name only (no id) or medicine description without id → rag or unknown, type rag
- Product general / "what is paracetamol used for" → rag
- Short affirmation (yes, ok, haan, theek, proceed) → confirmation, rag
- Otherwise unsure → type rag

Rules:
- If the message contains an explicit numeric id and matches order / payment / doctor / product / order list pattern, prefer structured.
- "How many" + entity → matching count_* intent.
- First-person doctor questions for the signed-in patient → my_session_doctors, structured (never rag for that).
- Medicines from this patient’s orders / attending doctors → my_session_medicines, structured.

Examples:
Mera doctor kaun hai?
{{"intent": "my_session_doctors", "type": "structured"}}

Who is my doctor?
{{"intent": "my_session_doctors", "type": "structured"}}

Aapka doctor kaun hai?
{{"intent": "my_session_doctors", "type": "structured"}}

डॉक्टर का नाम क्या है
{{"intent": "my_session_doctors", "type": "structured"}}

इस डॉक्टर ने मुझे कौन सी दवाएं दीं
{{"intent": "my_session_medicines", "type": "structured"}}

Order 101 ka status?
{{"intent": "order_status", "type": "structured"}}

Order 101 kis patient ka hai?
{{"intent": "order_owner", "type": "structured"}}

यह किस यूजर का ऑर्डर था (order 101)
{{"intent": "order_owner", "type": "structured"}}

Payment 5001 ka status?
{{"intent": "payment_status", "type": "structured"}}

Kitne patients hain?
{{"intent": "count_patients", "type": "structured"}}

List all patients
{{"intent": "list_patients", "type": "structured"}}

How many doctors?
{{"intent": "count_doctors", "type": "structured"}}

List doctors
{{"intent": "list_doctors", "type": "structured"}}

Doctor 201 ki details
{{"intent": "doctor_detail", "type": "structured"}}

Kitne medicines / products hain?
{{"intent": "count_products", "type": "structured"}}

All products list
{{"intent": "list_products", "type": "structured"}}

Product 301 ka price
{{"intent": "product_detail", "type": "structured"}}

Total orders?
{{"intent": "count_orders", "type": "structured"}}

List all orders
{{"intent": "list_orders", "type": "structured"}}

Amit kaha rehta hai?
{{"intent": "patient_info", "type": "rag"}}

Haan theek hai
{{"intent": "confirmation", "type": "rag"}}

Recent conversation:
{transcript}

Latest user message:
{query}
"""

    result = llm.invoke(prompt)

    try:
        json_str = extract_json(result.content)
        parsed = json.loads(json_str)
    except Exception:
        parsed = {
            "intent": "unknown",
            "type": "rag"
        }

    return {
        "intent": parsed.get("intent", "unknown"),
        "type": parsed.get("type", "rag")
    }
