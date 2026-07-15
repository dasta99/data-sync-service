"""Denormalize booth_voter — joins all dimensions once."""

import logging
from typing import List

from shared.interfaces import Database
from transform.base import TransformHelper

logger = logging.getLogger("transform.sir.denormalize")

TABLE = "dim_booth_voter"

DEPENDS_ON: List[str] = [
    "booth_voter",
    "booth",
    "assembly",
    "parliament",
    "state",
    "mytdp_cluster",
    "mytdp_unit",
    "dp_booth",
    "dp_constituency",
]


class DenormalizeBoothVoter(TransformHelper):

    def run(self, db: Database, from_date: str, to_date: str, report_date: str, publication_date_id: int) -> int:
        """Build dim_booth_voter — single pass join of booth_voter + all dimensions."""
        
        # Clear existing data for date range
        cur = db.cursor()
        try:
            cur.execute(f"DELETE FROM {TABLE} WHERE DATE(updated_at) BETWEEN %s AND %s", (from_date, to_date))
            db.commit()
        finally:
            cur.close()

        sql = """
            SELECT
                bv.id,
                bv.booth_id,
                bv.voter_id,
                bv.assembly_id,
                bv.parliament_id,
                bv.serial_no,
                bv.kss_id,
                bv.sir_verified,
                bv.sir_status,
                bv.sir_verified_by,
                bv.sir_mobile_number,
                bv.sir_caste_id,
                bv.sir_political_party_id,
                bv.file_path,
                bv.form_submitted_to_blo,
                bv.blo_digitized,
                bv.created_at,
                bv.updated_at,
                -- Dimensions from mytdp
                bo.state_id,
                s.state_name,
                bo.cluster_id,
                cl.cluster_name,
                bo.unit_id,
                u.unit_name,
                bo.name AS booth_name,
                -- Dimensions from dakavara_pa
                dpb.constituency_id,
                dpc.name AS constituency_name
            FROM booth_voter bv
            JOIN booth bo ON bv.booth_id = bo.id
            JOIN state s ON bo.state_id = s.id
            LEFT JOIN cluster cl ON bo.cluster_id = cl.id
            LEFT JOIN unit u ON bo.unit_id = u.id
            LEFT JOIN dakavara_pa.booth dpb ON bv.booth_id = dpb.booth_id AND dpb.publication_date_id = %s
            LEFT JOIN dakavara_pa.constituency dpc ON dpb.constituency_id = dpc.constituency_id
            WHERE DATE(bv.updated_at) BETWEEN %s AND %s
        """
        rows = self.fetch(db, sql, (publication_date_id, from_date, to_date))
        if not rows:
            return 0

        upsert = self.make_upsert(TABLE, [
            "id", "booth_id", "voter_id", "assembly_id", "parliament_id",
            "serial_no", "kss_id", "sir_verified", "sir_status",
            "sir_verified_by", "sir_mobile_number", "sir_caste_id",
            "sir_political_party_id", "file_path", "form_submitted_to_blo",
            "blo_digitized", "created_at", "updated_at",
            "state_id", "state_name", "cluster_id", "cluster_name",
            "unit_id", "unit_name", "booth_name",
            "constituency_id", "constituency_name",
        ], pk="id")

        params_list = [(
            r["id"], r["booth_id"], r["voter_id"], r["assembly_id"], r["parliament_id"],
            r["serial_no"], r["kss_id"], r["sir_verified"], r["sir_status"],
            r["sir_verified_by"], r["sir_mobile_number"], r["sir_caste_id"],
            r["sir_political_party_id"], r["file_path"], r["form_submitted_to_blo"],
            r["blo_digitized"], r["created_at"], r["updated_at"],
            r["state_id"], r["state_name"], r["cluster_id"], r["cluster_name"],
            r["unit_id"], r["unit_name"], r["booth_name"],
            r["constituency_id"], r["constituency_name"],
        ) for r in rows]

        self.write(db, upsert, params_list)
        logger.info(f"  {TABLE}: {len(rows)} rows denormalized")
        return len(rows)
