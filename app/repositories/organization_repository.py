from app.core.config import Config
from app.core.databases import DatabaseHelper


class OrganizationRepository:
    def __init__(self):
        self.config=Config()
        self.db_helper=DatabaseHelper()

    async def fetch_all(self):
        query="""
            SELECT
                org_id,
                org_name
            FROM organization
            WHERE org_status = %s
            """
        params=('Enabled',)

        result=self.db_helper.fetch_data(query, params)
        if result.empty:
            raise Exception("Organization not found")
        result["org_id"]=result["org_id"].apply(self.db_helper.sqids.encode).astype(str)
        return result
        

