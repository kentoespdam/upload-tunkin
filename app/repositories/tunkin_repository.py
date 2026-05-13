from typing import Optional

from fastapi import UploadFile

from app.core.config import Config
from app.core.databases import DatabaseHelper
from app.models.request_model import TunkinRequest

TEMPLATE_COLUMN = [
    "NO",
    "PERIODE",
    "NIPAM",
    "JUMLAH PENERIMAAN"
]


def get_tunkin_repository() -> "TunkinRepository":
    """Factory function to create TunkinRepository instance."""
    return TunkinRepository()


class TunkinRepository:
    def __init__(self, config=Config(), db_helper: DatabaseHelper = DatabaseHelper()):
        self.config = config
        self.file: Optional[UploadFile] = None
        self._allowed_extension = {'xlsx', 'xls'}
        self._max_file_size = 50 * 1024 * 1024  # 50MB
        self.db_helper = db_helper

    def fetch_page_data(self, periode: str, req: TunkinRequest,):
        query = f"""
            SELECT
                kpi.id AS id,
                kpi.periode AS periode, 
                kpi.nipam AS nipam, 
                ep.emp_name AS nama, 
                po.pos_name AS jabatan, 
                org.org_name AS organisasi, 
                sef.text AS status_pegawai,
                kpi.tunkin AS tunkin,
                kpi.pph21_ter AS pph21_ter
            FROM {self.config.kpi_table_name} kpi
            INNER JOIN employee AS em ON kpi.nipam = em.emp_code
            INNER JOIN emp_profile AS ep ON em.emp_profile_id = ep.emp_profile_id
            INNER JOIN position AS po ON em.emp_pos_id = po.pos_id
            INNER JOIN organization AS org ON po.pos_org_id = org.org_id
            INNER JOIN sys_reference AS sef ON sef.`code` = 'emp_flag' 
                AND em.emp_flag = sef.`value` 
            WHERE kpi.periode = %s
        """
        params = (periode,)
        if req.nipam:
            query += " AND nipam = %s"
            params += (req.nipam,)

        query +="ORDER BY org.org_level , po.pos_level"
        return self.db_helper.fetch_page(query, params, req.page, req.size)
