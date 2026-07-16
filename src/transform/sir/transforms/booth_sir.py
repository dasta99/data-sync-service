"""Booth SIR transform — builds fact_booth_sir from dim_booth_voter."""

import logging
from typing import List

from shared.interfaces import Database
from transform.base import TransformHelper

logger = logging.getLogger("transform.sir.booth_sir")

TABLE = "fact_booth_sir"

DEPENDS_ON: List[str] = ["dim_booth_voter"]


class BoothSIR(TransformHelper):

    def run(self, db: Database, from_date: str, to_date: str, report_date: str, publication_date_id: int) -> int:
        # Single pass aggregation from denormalized table
        sql = """
            SELECT
                booth_id,
                booth_name,
                state_id,
                state_name,
                parliament_id,
                assembly_id,
                cluster_id,
                cluster_name,
                unit_id,
                unit_name,
                constituency_id,
                constituency_name,
                COUNT(DISTINCT voter_id) AS total_voters,
                SUM(CASE WHEN sir_verified = 1 THEN 1 ELSE 0 END) AS verified_voters,
                COUNT(DISTINCT CASE WHEN sir_verified = 1 THEN sir_verified_by END) AS active_users,
                SUM(CASE WHEN sir_status = 'available' THEN 1 ELSE 0 END) AS available_count,
                SUM(CASE WHEN sir_status = 'temporary shift' THEN 1 ELSE 0 END) AS temporary_shift_count,
                SUM(CASE WHEN sir_status = 'permanent shift' THEN 1 ELSE 0 END) AS permanent_shift_count,
                SUM(CASE WHEN sir_status = 'death' THEN 1 ELSE 0 END) AS death_count,
                SUM(CASE WHEN sir_status = 'duplicate' THEN 1 ELSE 0 END) AS duplicate_count,
                SUM(CASE WHEN sir_status = 'double vote' THEN 1 ELSE 0 END) AS double_count,
                SUM(CASE WHEN form_submitted_to_blo = 1 THEN 1 ELSE 0 END) AS forms_submitted_to_blo,
                SUM(CASE WHEN blo_digitized = 1 THEN 1 ELSE 0 END) AS blo_digitized
            FROM dim_booth_voter
            WHERE DATE(updated_at) BETWEEN %s AND %s
            GROUP BY booth_id, booth_name, state_id, state_name, parliament_id,
                     assembly_id, cluster_id, cluster_name, unit_id, unit_name,
                     constituency_id, constituency_name
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        if not rows:
            return 0

        upsert = self.make_upsert(TABLE, [
            "booth_id", "booth_name",
            "state_id", "state_name", "parliament_id",
            "assembly_id", "cluster_id", "cluster_name",
            "unit_id", "unit_name",
            "constituency_id", "constituency_name",
            "total_voters", "verified_voters", "active_users",
            "available_count", "temporary_shift_count", "permanent_shift_count",
            "death_count", "duplicate_count", "double_count",
            "forms_submitted_to_blo", "blo_digitized", "report_date",
        ], pk="booth_id,report_date")

        params_list = [(
            r["booth_id"], r["booth_name"],
            r["state_id"], r["state_name"], r["parliament_id"],
            r["assembly_id"], r["cluster_id"], r["cluster_name"],
            r["unit_id"], r["unit_name"],
            r["constituency_id"], r["constituency_name"],
            r["total_voters"], r["verified_voters"], r["active_users"],
            r["available_count"], r["temporary_shift_count"], r["permanent_shift_count"],
            r["death_count"], r["duplicate_count"], r["double_count"],
            r["forms_submitted_to_blo"], r["blo_digitized"], report_date,
        ) for r in rows]

        self.write(db, upsert, params_list)
        logger.info(f"  {TABLE}: {len(rows)} booths")
        return len(rows)
