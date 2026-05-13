from typing import Annotated

from fastapi import Depends

from app.core.config import SqidsHelper
from app.core.databases import DatabaseHelper


class OrganizationRepository:
    """Read-only repository for the organization table."""

    def __init__(self, db: DatabaseHelper):
        self.db = db

    def list_all(self) -> list[dict]:
        query = """
            SELECT org_id, org_name
            FROM organization
            ORDER BY org_level
        """
        rows = self.db.fetch_tuple_data(query)
        return rows or []


def get_organization_repository() -> OrganizationRepository:
    return OrganizationRepository(DatabaseHelper())


def list_organizations(
    repo: Annotated[OrganizationRepository, Depends(get_organization_repository)],
) -> list[dict]:
    """Inline dependency: fetch organizations and encode IDs."""
    sqids = SqidsHelper()
    orgs = repo.list_all()
    return [
        {"id": sqids.encode(row["org_id"]), "name": row["org_name"]}
        for row in orgs
    ]
