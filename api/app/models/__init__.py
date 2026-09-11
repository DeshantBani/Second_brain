"""Importing this package registers every model on Base.metadata, which is what
db_bootstrap.py's create_all() call relies on. Keep every new model imported here."""
from app.models.user import User
from app.models.matter import Matter
from app.models.access_grant import AccessGrant
from app.models.document import Document
from app.models.fingerprint import IssueFingerprint
from app.models.authority import Authority
from app.models.matter_authority import MatterAuthority
from app.models.reliability import ReliabilityAssessment
from app.models.querylog import QueryLog
from app.models.agent_call_log import AgentCallLog

__all__ = [
    "User",
    "Matter",
    "AccessGrant",
    "Document",
    "IssueFingerprint",
    "Authority",
    "MatterAuthority",
    "ReliabilityAssessment",
    "QueryLog",
    "AgentCallLog",
]
