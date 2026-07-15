"""Voter location transform — builds fact_voter_location."""

import logging
from typing import List

from shared.interfaces import Database
from transform.base import TransformHelper

logger = logging.getLogger("transform.sir.voter_location")

TABLE = "fact_voter_location"

DEPENDS_ON: List[str] = [
    "dp_voter_info",
    "dp_state",
    "dp_constituency",
]


class VoterLocation(TransformHelper):

    def run(self, db: Database, from_date: str, to_date: str, report_date: str, publication_date_id: int) -> int:
        sql = """
            SELECT
                vi.report_level_value AS location_id,
                CASE vi.location_scope_id
                    WHEN 2 THEN 'state'
                    WHEN 10 THEN 'parliament'
                    WHEN 4 THEN 'constituency'
                    WHEN 17 THEN 'cluster'
                    WHEN 18 THEN 'unit'
                    WHEN 9 THEN 'booth'
                    WHEN 5 THEN 'tehsil'
                    WHEN 6 THEN 'panchayat'
                    WHEN 7 THEN 'town'
                END AS location_type,
                CASE WHEN vi.location_scope_id IN (10,4,17,18,9,5,6,7) THEN dpc.state_id ELSE ds.state_id END AS state_id,
                CASE WHEN vi.location_scope_id IN (10,4,17,18,9,5,6,7) THEN ds.state_name ELSE NULL END AS state_name,
                CASE WHEN vi.location_scope_id IN (4,17,18,9,5,6,7) THEN dpc.parliament_id ELSE NULL END AS parliament_id,
                CASE WHEN vi.location_scope_id IN (4,17,18,9,5,6,7) THEN dpp.name ELSE NULL END AS parliament_name,
                CASE WHEN vi.location_scope_id IN (17,18,9,5,6,7) THEN dpc.constituency_id ELSE NULL END AS constituency_id,
                CASE WHEN vi.location_scope_id IN (17,18,9,5,6,7) THEN dpc.name ELSE NULL END AS constituency_name,
                vi.total_voters,
                vi.publication_date_id
            FROM dakavara_pa.voter_info vi
            LEFT JOIN dakavara_pa.state ds ON vi.report_level_value = ds.state_id AND vi.location_scope_id = 2
            LEFT JOIN dakavara_pa.constituency dpc ON vi.report_level_value = dpc.constituency_id AND vi.location_scope_id IN (4, 10)
            LEFT JOIN dakavara_pa.constituency dpp ON dpc.parliament_id = dpp.constituency_id AND vi.location_scope_id IN (4, 10)
            WHERE vi.publication_date_id = %s
              AND vi.location_scope_id IN (2, 4, 10, 17, 18, 9, 5, 6, 7)
        """
        rows = self.fetch(db, sql, (publication_date_id,))
        if not rows:
            return 0

        upsert = self.make_upsert(TABLE, [
            "location_id", "location_type",
            "state_id", "state_name", "parliament_id", "parliament_name",
            "assembly_id", "assembly_name", "constituency_id", "constituency_name",
            "total_voters", "publication_date_id",
        ], pk="location_id,location_type,publication_date_id")

        params_list = [(
            r["location_id"], r["location_type"],
            r["state_id"], r["state_name"], r["parliament_id"], r["parliament_name"],
            None, None,
            r["constituency_id"], r["constituency_name"],
            r["total_voters"], r["publication_date_id"],
        ) for r in rows]

        self.write(db, upsert, params_list)
        logger.info(f"  {TABLE}: {len(rows)} locations")
        return len(rows)
