"""Booth CUBS transform — builds fact_booth_cubs from dim_booth_voter."""

import logging
from typing import List

from shared.interfaces import Database
from transform.base import TransformHelper

logger = logging.getLogger("transform.sir.booth_cubs")

TABLE = "fact_booth_cubs"

DEPENDS_ON: List[str] = ["dim_booth_voter"]


class BoothCUBS(TransformHelper):

    def run(self, db: Database, from_date: str, to_date: str, report_date: str, publication_date_id: int) -> int:
        # Single pass aggregation from denormalized table (sir_verified = 1 only)
        sql = """
            SELECT
                booth_id,
                booth_name,
                state_id,
                state_name,
                parliament_id,
                constituency_id,
                constituency_name,
                cluster_id,
                cluster_name,
                unit_id,
                unit_name,
                COUNT(DISTINCT sir_mobile_number) AS mobile_count,
                COUNT(sir_caste_id) AS caste_count,
                COUNT(sir_political_party_id) AS party_count,
                COUNT(file_path) AS forms_count,
                SUM(CASE WHEN sir_status = 'available' THEN 1 ELSE 0 END) AS available_count,
                SUM(CASE WHEN sir_status = 'temporary shift' THEN 1 ELSE 0 END) AS temporary_shift_count,
                SUM(CASE WHEN sir_status = 'permanent shift' THEN 1 ELSE 0 END) AS permanent_shift_count,
                SUM(CASE WHEN sir_status = 'death' THEN 1 ELSE 0 END) AS death_count,
                SUM(CASE WHEN sir_status = 'duplicate' THEN 1 ELSE 0 END) AS duplicate_count,
                SUM(CASE WHEN sir_status = 'double vote' THEN 1 ELSE 0 END) AS double_count
            FROM dim_booth_voter
            WHERE sir_verified = 1 AND DATE(updated_at) BETWEEN %s AND %s
            GROUP BY booth_id, booth_name, state_id, state_name, parliament_id,
                     constituency_id, constituency_name,
                     cluster_id, cluster_name, unit_id, unit_name
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        if not rows:
            return 0

        upsert = self.make_upsert(TABLE, [
            "booth_id", "booth_name",
            "state_id", "state_name", "parliament_id",
            "constituency_id", "constituency_name",
            "cluster_id", "cluster_name", "unit_id", "unit_name",
            "mobile_count", "caste_count", "party_count", "forms_count",
            "available_count", "temporary_shift_count", "permanent_shift_count",
            "death_count", "duplicate_count", "double_count", "report_date",
        ], pk="booth_id,report_date")

        params_list = [(
            r["booth_id"], r["booth_name"],
            r["state_id"], r["state_name"], r["parliament_id"],
            r["constituency_id"], r["constituency_name"],
            r["cluster_id"], r["cluster_name"], r["unit_id"], r["unit_name"],
            r["mobile_count"], r["caste_count"], r["party_count"], r["forms_count"],
            r["available_count"], r["temporary_shift_count"], r["permanent_shift_count"],
            r["death_count"], r["duplicate_count"], r["double_count"], report_date,
        ) for r in rows]

        self.write(db, upsert, params_list)
        logger.info(f"  {TABLE}: {len(rows)} booths")
        return len(rows)
