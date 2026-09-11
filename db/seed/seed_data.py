"""Idempotent demo-corpus seed script. Run via `make seed`
(docker compose run --rm api python -m db.seed.seed_data).

Builds the synthetic archive engineered to reproduce the Section 15 QA scenario end to
end: a hero past matter (M-001) whose advisory memo relies on a case-law authority with
a genuine negative-treatment record, four decoy matters that exercise the retrieval
funnel's discrimination and "no confident match" behavior, and one matter (M-006)
granted only to a second user - a concrete, clickable proof that AccessGrant isolation
holds even against a textually/vector-similar matter belonging to the same
counterparty.
"""
import asyncio
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select

from app.db import OwnerSessionLocal
from app.models.access_grant import AccessGrant
from app.models.authority import Authority
from app.models.document import Document
from app.models.fingerprint import IssueFingerprint
from app.models.matter import Matter
from app.models.matter_authority import MatterAuthority
from app.models.querylog import QueryLog
from app.models.reliability import ReliabilityAssessment
from app.models.user import User
from app.reliability.mock_provider import MockCaseLawProvider
from app.security import hash_password
from app.services.ingestion import build_matter_fingerprint, ingest_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "matters"

CONTINENTAL = "Continental Constructions Co. Ltd v. State Trading Corporation of India, AIR 1997 Del 217"
ONGC_SAW_PIPES = "ONGC v. Saw Pipes Ltd, (2003) 5 SCC 705"

USERS = [
    {"email": "lawyer1@secondbrain.test", "password": "lawyer123", "display_name": "Meera Nair", "role": "lawyer"},
    {"email": "lawyer2@secondbrain.test", "password": "lawyer123", "display_name": "Arjun Rao", "role": "lawyer"},
    {"email": "admin@secondbrain.test", "password": "admin123", "display_name": "Firm Admin", "role": "admin"},
]

MATTERS = [
    {
        "key": "m001_kesar_anand",
        "title": "Kesar Industries - Termination of Supply Agreement with Anand Component Works",
        "client_name": "Kesar Industries Pvt. Ltd.",
        "practice_area": "commercial_contracts",
        "jurisdiction": "India - Maharashtra",
        "matter_type": "supply agreement termination",
        "status": "closed",
        "opened_date": date(2021, 9, 15),
        "documents": [
            ("Manufacturing Supply Agreement", "contract", "tier1_confidential", "supply_agreement.md"),
            ("Advisory Memo - Termination Strategy", "memo", "tier1_confidential", "advisory_memo.md"),
            ("Correspondence - Anand Damages Threat", "email", "tier1_confidential", "correspondence.md"),
        ],
        "access": ["lawyer1@secondbrain.test"],
        "authorities": [
            {
                "citation": CONTINENTAL,
                "relied_upon_for": "Confirming that awaiting full expiry of the cure period before treating the "
                                    "breach as terminable was procedurally correct, since the counterparty's damages "
                                    "assertion came only after the cure period had already run.",
                "doc_file": "advisory_memo.md", "page": 3, "paragraph": 3,
            }
        ],
    },
    {
        "key": "m002_rao_textiles",
        "title": "Rao Textiles - Termination of Senior Plant Manager",
        "client_name": "Rao Textiles Pvt. Ltd.",
        "practice_area": "employment",
        "jurisdiction": "India - Karnataka",
        "matter_type": "employee termination",
        "status": "closed",
        "opened_date": date(2022, 1, 10),
        "documents": [
            ("Advisory Memo - Wrongful Termination Exposure", "memo", "tier1_confidential", "advisory_memo.md"),
        ],
        "access": ["lawyer1@secondbrain.test"],
        "authorities": [],
    },
    {
        "key": "m003_bansal_foods",
        "title": "Bansal Foods - Termination of Distribution Agreement",
        "client_name": "Bansal Foods Pvt. Ltd.",
        "practice_area": "commercial_contracts",
        "jurisdiction": "India - Karnataka",
        "matter_type": "distribution agreement termination",
        "status": "closed",
        "opened_date": date(2020, 5, 1),
        "documents": [
            ("Advisory Memo - Termination for Cause", "memo", "tier1_confidential", "advisory_memo.md"),
        ],
        "access": ["lawyer1@secondbrain.test"],
        "authorities": [],
    },
    {
        "key": "m004_deccan_infra",
        "title": "Deccan Infra - EPC Final Payment Arbitration",
        "client_name": "Deccan Infra Projects Ltd.",
        "practice_area": "arbitration",
        "jurisdiction": "India - Telangana",
        "matter_type": "EPC arbitration",
        "status": "open",
        "opened_date": date(2022, 4, 1),
        "documents": [
            ("Advisory Memo - Arbitration Strategy", "memo", "tier1_confidential", "advisory_memo.md"),
        ],
        "access": ["lawyer1@secondbrain.test"],
        "authorities": [
            {
                "citation": ONGC_SAW_PIPES,
                "relied_upon_for": "Setting the (high) bar for a future Section 34 public-policy challenge, should "
                                    "the tribunal rule against Deccan.",
                "doc_file": "advisory_memo.md", "page": 2, "paragraph": 6,
            }
        ],
    },
    {
        "key": "m005_meridian_pharma",
        "title": "Meridian Pharma - API Supply Agreement Price Renegotiation",
        "client_name": "Meridian Pharma Ltd.",
        "practice_area": "commercial_contracts",
        "jurisdiction": "India - Gujarat",
        "matter_type": "supply agreement price review",
        "status": "open",
        "opened_date": date(2023, 2, 1),
        "documents": [
            ("Advisory Memo - Price Review Mechanism", "memo", "tier1_confidential", "advisory_memo.md"),
        ],
        "access": ["lawyer1@secondbrain.test"],
        "authorities": [],
    },
    {
        "key": "m006_anand_component_works",
        "title": "Anand Component Works - Termination of Supply Agreement with Ashoka Forge Works",
        "client_name": "Anand Component Works Pvt. Ltd.",
        "practice_area": "commercial_contracts",
        "jurisdiction": "India - Maharashtra",
        "matter_type": "supply agreement termination",
        "status": "closed",
        "opened_date": date(2022, 5, 6),
        "documents": [
            ("Advisory Memo - Termination Strategy (Ashoka Forge Works)", "memo", "tier1_confidential", "advisory_memo.md"),
        ],
        "access": ["lawyer2@secondbrain.test"],
        "authorities": [
            {
                "citation": CONTINENTAL,
                "relied_upon_for": "Basis for advising that Anand may terminate once the cure period has run, "
                                    "since no damages claim has been asserted by the counterparty at all.",
                "doc_file": "advisory_memo.md", "page": 2, "paragraph": 4,
            }
        ],
    },
]


def wipe_existing_data(db):
    print("[seed] wiping existing demo data...")
    for model in [ReliabilityAssessment, QueryLog, MatterAuthority, Document, IssueFingerprint, AccessGrant, Matter, Authority, User]:
        db.execute(delete(model))
    db.commit()


def seed_users(db) -> dict[str, User]:
    print("[seed] creating users...")
    users = {}
    for u in USERS:
        user = User(email=u["email"], hashed_password=hash_password(u["password"]), display_name=u["display_name"], role=u["role"])
        db.add(user)
        db.flush()
        users[u["email"]] = user
    db.commit()
    return users


def seed_authorities(db) -> dict[str, Authority]:
    print("[seed] creating authorities from CaseLawProvider fixtures...")
    provider = MockCaseLawProvider()
    authorities = {}
    for citation in provider.all_citations():
        status = provider.get_citation_status(citation)
        judgments = provider.get_citing_judgments(citation)
        authority = Authority(
            citation=citation,
            court=status.treatment_history[0].court if status.treatment_history else "Unknown",
            year=int(citation.split()[-1]) if citation.split()[-1].isdigit() else 2000,
            status=status.status,
            treatment_history=[j.model_dump(mode="json") for j in judgments],
            monitoring_status="checked_flagged" if judgments else "checked_clear",
        )
        # Extract court/year properly from the fixture record itself rather than guessing from the citation string.
        record = provider._by_citation[citation]  # noqa: SLF001 - seed script is allowed to reach into mock internals
        authority.court = record["court"]
        authority.year = record["year"]
        db.add(authority)
        db.flush()
        authorities[citation] = authority
    db.commit()
    return authorities


async def seed_matter(db, config: dict, users: dict[str, User], authorities: dict[str, Authority]):
    print(f"[seed] creating matter: {config['title']}")
    matter = Matter(
        title=config["title"], client_name=config["client_name"], practice_area=config["practice_area"],
        jurisdiction=config["jurisdiction"], matter_type=config["matter_type"], status=config["status"],
        opened_date=config["opened_date"],
    )
    db.add(matter)
    db.flush()

    for email in config["access"]:
        db.add(AccessGrant(matter_id=matter.id, user_id=users[email].id, grant_level="write", granted_by=users[email].id))
    db.flush()

    doc_dir = FIXTURES_DIR / config["key"]
    docs_by_file: dict[str, Document] = {}
    for title, doc_type, tier, filename in config["documents"]:
        raw_text = (doc_dir / filename).read_text(encoding="utf-8")
        doc = await ingest_document(db, str(matter.id), title, doc_type, tier, raw_text)
        docs_by_file[filename] = doc
    db.flush()

    for auth_cfg in config["authorities"]:
        cited_doc = docs_by_file[auth_cfg["doc_file"]]
        db.add(MatterAuthority(
            matter_id=matter.id, authority_id=authorities[auth_cfg["citation"]].id,
            cited_in_document_id=cited_doc.id, cited_at_page=auth_cfg["page"],
            cited_at_paragraph=auth_cfg["paragraph"], relied_upon_for=auth_cfg["relied_upon_for"],
        ))
    db.flush()

    combined_text = "\n\n".join(d.extracted_text for d in docs_by_file.values())
    _, degraded = await build_matter_fingerprint(db, str(matter.id), combined_text)
    if degraded:
        print(f"  [seed] WARNING: fingerprint/embedding degraded for '{config['title']}' - "
              f"is GEMINI_API_KEY configured?")
    db.commit()


async def main():
    db = OwnerSessionLocal()
    try:
        wipe_existing_data(db)
        users = seed_users(db)
        authorities = seed_authorities(db)
        for config in MATTERS:
            await seed_matter(db, config, users, authorities)

        print("\n[seed] done.")
        print(f"[seed] {len(users)} users, {len(authorities)} authorities, {len(MATTERS)} matters seeded.")
        print("[seed] demo logins: lawyer1@secondbrain.test / lawyer123, lawyer2@secondbrain.test / lawyer123, "
              "admin@secondbrain.test / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
