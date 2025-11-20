import pandas as pd

from app.core.config import Config
from app.core.databases import DatabaseHelper


class SysMenuRepository:
    def __init__(self):
        self.config = Config()
        self.db_helper = DatabaseHelper()

    def fetch_menus(self, role_id: int) -> pd.DataFrame:
        query = f"""
            SELECT
                srm.role_id,
                srm.menu_id,
                sm.menu_code,
                sm.menu_title 
            FROM
                sys_role_menu AS srm
                INNER JOIN sys_role AS sr ON srm.role_id = sr.role_id
                INNER JOIN sys_menu AS sm ON srm.menu_id = sm.menu_id 
            WHERE
                sr.role_id = %s
        """
        params = (role_id,)
        return self.db_helper.fetch_data(query, params)


def get_sys_menu_repository() -> SysMenuRepository:
    return SysMenuRepository()
