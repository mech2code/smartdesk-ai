"""Download strova-ai/hr-policies-qa-dataset from HuggingFace and convert to KB markdown files."""
import os
import json
import re
from pathlib import Path

HR_DIR = Path(__file__).parent / "hr"
HR_DIR.mkdir(exist_ok=True)


def download_via_datasets_lib():
    from datasets import load_dataset
    ds = load_dataset("strova-ai/hr-policies-qa-dataset", split="train")
    return [{"question": row["question"], "answer": row["answer"]} for row in ds]


def download_via_http():
    """Fallback: fetch parquet via HuggingFace HTTP API."""
    import urllib.request
    import io

    url = "https://huggingface.co/datasets/strova-ai/hr-policies-qa-dataset/resolve/main/data/train-00000-of-00001.parquet"
    print(f"Fetching {url}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = resp.read()

    import pyarrow.parquet as pq
    table = pq.read_table(io.BytesIO(data))
    df = table.to_pydict()
    questions = df.get("question", df.get("Question", []))
    answers = df.get("answer", df.get("Answer", []))
    return [{"question": q, "answer": a} for q, a in zip(questions, answers)]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "_", text)
    return text[:60]


def group_by_topic(rows):
    """Group Q&A pairs into rough topic clusters for separate markdown files."""
    topics = {
        "leave_policy": ["leave", "pto", "vacation", "sick", "time off", "absence", "holiday", "maternity", "paternity", "bereavement"],
        "benefits": ["benefit", "health", "dental", "vision", "insurance", "medical", "401k", "retirement", "pension", "wellness"],
        "payroll": ["payroll", "salary", "pay", "compensation", "bonus", "raise", "overtime", "wage", "reimburs"],
        "onboarding": ["onboard", "new hire", "orientation", "first day", "start", "joining"],
        "remote_work": ["remote", "work from home", "wfh", "hybrid", "telework", "home office"],
        "performance": ["performance", "review", "appraisal", "evaluation", "goal", "feedback", "promotion"],
        "code_of_conduct": ["conduct", "harassment", "discrimination", "policy", "ethics", "complaint", "grievance", "disciplin"],
    }
    grouped = {t: [] for t in topics}
    grouped["general"] = []

    for row in rows:
        q = row["question"].lower()
        matched = False
        for topic, keywords in topics.items():
            if any(kw in q for kw in keywords):
                grouped[topic].append(row)
                matched = True
                break
        if not matched:
            grouped["general"].append(row)

    return grouped


def write_markdown(topic: str, rows: list):
    if not rows:
        return
    title = topic.replace("_", " ").title()
    lines = [f"# HR Policy — {title}\n"]
    for row in rows:
        lines.append(f"## {row['question']}\n")
        lines.append(f"{row['answer']}\n")
    content = "\n".join(lines)
    path = HR_DIR / f"{topic}.md"
    path.write_text(content, encoding="utf-8")
    print(f"  Wrote {path} ({len(rows)} Q&A pairs)")


def main():
    print("Downloading HR dataset...")
    rows = []
    try:
        rows = download_via_datasets_lib()
        print(f"  Loaded {len(rows)} rows via datasets library")
    except Exception as e:
        print(f"  datasets library failed ({e}), trying HTTP...")
        try:
            rows = download_via_http()
            print(f"  Loaded {len(rows)} rows via HTTP")
        except Exception as e2:
            print(f"  HTTP also failed: {e2}")
            print("  Writing fallback HR docs...")
            write_fallback_docs()
            return

    grouped = group_by_topic(rows)
    for topic, topic_rows in grouped.items():
        write_markdown(topic, topic_rows)

    print(f"\nDone. HR KB files written to {HR_DIR}/")


def write_fallback_docs():
    """Write hand-crafted fallback HR docs if dataset download fails."""
    docs = {
        "leave_policy": """# Leave Policy

## How many vacation days do employees get?
Full-time employees receive 15 days of paid vacation per year for the first 3 years, 20 days from year 4 onwards. Part-time employees receive leave on a pro-rated basis.

## How do I request time off?
Submit your leave request through the HR portal at hr-portal.internal/leave. Requests must be submitted at least 2 weeks in advance for vacations of 3+ days. Your manager will approve or deny within 3 business days.

## What is the sick leave policy?
Employees receive 10 days of paid sick leave per year. Sick leave does not roll over. A doctor's note is required for absences of 3+ consecutive days.

## What is the bereavement leave policy?
Employees receive up to 5 paid days for immediate family (spouse, child, parent, sibling) and 3 days for extended family (grandparent, in-law, aunt/uncle).

## Does unused vacation roll over?
Up to 5 unused vacation days may roll over to the next calendar year. Any remaining balance is forfeited on January 31st.

## What is maternity/paternity leave?
Primary caregivers receive 16 weeks of paid parental leave. Secondary caregivers receive 4 weeks of paid parental leave. Leave must begin within 12 months of the child's birth or adoption.

## What are the company holidays?
The company observes 11 federal holidays plus 2 floating holidays that employees can use at their discretion.
""",
        "benefits": """# Employee Benefits

## What health insurance plans are available?
The company offers three health plans: Basic HMO, Standard PPO, and Premium PPO. Open enrollment occurs annually in November. New hires may enroll within 30 days of their start date.

## Who pays for health insurance?
The company covers 80% of the premium for employee-only coverage and 60% for family coverage. The employee pays the remaining portion via pre-tax payroll deduction.

## Is dental insurance included?
Yes. All full-time employees receive dental insurance covering preventive care (100%), basic procedures (80%), and major procedures (50%) after meeting the annual deductible.

## Is vision insurance offered?
Yes. Vision coverage includes one annual eye exam and up to $150 toward frames or contact lenses per year.

## Does the company offer a 401(k)?
Yes. The company matches 100% of employee contributions up to 4% of salary. Matching contributions vest over a 3-year schedule (33%/year).

## What is the Employee Assistance Program (EAP)?
The EAP provides free, confidential counseling (up to 8 sessions/year), financial planning assistance, and legal consultation. Contact the EAP at 1-800-EAP-HELP or eap.company.com.

## Are there wellness benefits?
Employees receive a $600 annual wellness stipend for gym memberships, fitness equipment, or wellness apps. Submit receipts to hr@company.com for reimbursement.
""",
        "payroll": """# Payroll Information

## When is payday?
Employees are paid bi-weekly (every other Friday). The payroll schedule is published on the HR portal at the start of each year.

## How do I set up direct deposit?
Log in to hr-portal.internal/payroll and navigate to Direct Deposit. Enter your bank routing and account numbers. Changes take effect within 2 pay cycles.

## How do I access my pay stubs?
Pay stubs are available in the HR portal under Payroll → Pay History. You will also receive an email notification when each stub is ready.

## How do I report a payroll error?
Contact payroll@company.com within 5 business days of the pay date. Include your employee ID, the pay period in question, and the discrepancy details.

## What are pre-tax deductions?
Pre-tax deductions include health/dental/vision premiums, 401(k) contributions, FSA contributions, and commuter benefits. These reduce your taxable income.

## How is overtime calculated?
Non-exempt employees receive 1.5x their hourly rate for hours worked beyond 40 in a week. Overtime must be pre-approved by your manager.

## When do I receive my W-2?
W-2 forms are available electronically in the HR portal by January 31st. A paper copy is also mailed to your address on file.
""",
        "remote_work": """# Remote Work Policy

## Who is eligible to work remotely?
All employees in roles that do not require a physical presence may work remotely. Eligibility is determined by your manager and HR based on job function.

## What is the hybrid work schedule?
The standard hybrid model is 3 days in-office and 2 days remote per week. Teams may agree on specific in-office days with manager approval.

## Do I need to notify someone when working remotely?
Yes. Update your calendar and status in Teams/Slack to reflect your work location. Notify your manager of any changes to your expected schedule.

## What equipment does the company provide for remote work?
The company provides a laptop, monitor (upon request), and headset for remote work. Employees may request additional peripherals through the IT portal.

## Is there a home office stipend?
New remote employees receive a one-time $500 home office setup stipend. Submit receipts within 60 days of your start date to expenses@company.com.

## What are the expectations for availability while remote?
Remote employees must be available during core hours (10 AM–3 PM local time), respond to messages within 2 hours, and attend all scheduled meetings via video.

## Can I work from a different city or country temporarily?
Short-term remote work from a different location (up to 30 days) requires manager approval. International remote work also requires HR and Legal sign-off due to tax implications.
""",
        "code_of_conduct": """# Code of Conduct

## What is the company's harassment policy?
The company has a zero-tolerance policy for harassment of any kind, including sexual harassment, bullying, and discrimination based on race, gender, age, religion, disability, or any protected characteristic.

## How do I report harassment or misconduct?
Report incidents to your HR Business Partner, your manager (if not the offending party), or anonymously via the ethics hotline at 1-888-ETHICS-1 or ethics.company.com. All reports are confidential.

## What happens after I report misconduct?
HR will acknowledge your report within 24 hours and begin a formal investigation within 3 business days. You will be updated on the outcome. Retaliation against anyone who reports in good faith is strictly prohibited.

## What is the conflict of interest policy?
Employees must disclose any outside business interests, financial relationships, or personal relationships that could influence their work decisions. Disclosures go to your manager and HR.

## What is the company's social media policy?
Employees may use social media freely but must not share confidential company information, speak on behalf of the company without authorization, or post content that could damage the company's reputation.

## What is the expense policy?
Business expenses must be pre-approved by your manager, submitted within 30 days of incurrence, and accompanied by receipts. Refer to the full expense policy at hr-portal.internal/expenses.
""",
    }

    for filename, content in docs.items():
        path = HR_DIR / f"{filename}.md"
        path.write_text(content, encoding="utf-8")
        print(f"  Wrote fallback {path}")


if __name__ == "__main__":
    main()
