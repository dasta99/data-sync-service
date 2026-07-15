"""SIR handler — orchestrates transforms for SIR/CUBS domain.

Flow:
  1. DenormalizeBoothVoter — single join of booth_voter + all dimensions
  2. BoothSIR — aggregate dim_booth_voter → fact_booth_sir
  3. BoothCUBS — aggregate dim_booth_voter → fact_booth_cubs
  4. VoterLocation — from voter_info → fact_voter_location
"""

import logging
import time
from datetime import date
from typing import Any, Dict, List, Optional

from shared.interfaces import Database
from transform.base import TransformHandler, TransformResult
from transform.sir.transforms.denormalize import DenormalizeBoothVoter
from transform.sir.transforms.booth_sir import BoothSIR
from transform.sir.transforms.booth_cubs import BoothCUBS
from transform.sir.transforms.voter_location import VoterLocation

logger = logging.getLogger("transform.sir")


class Handler(TransformHandler):

    @property
    def name(self) -> str:
        return "sir"

    @property
    def depends_on(self) -> List[str]:
        return [
            "booth_voter", "booth", "assembly", "parliament", "state",
            "mytdp_cluster", "mytdp_unit",
            "dp_booth", "dp_constituency", "dp_voter_info",
        ]

    @property
    def outputs(self) -> List[str]:
        return ["dim_booth_voter", "fact_booth_sir", "fact_booth_cubs", "fact_voter_location"]

    def transform(
        self,
        source_db: Optional[Database],
        dest_db: Database,
        params: Optional[Dict[str, Any]] = None,
    ) -> TransformResult:
        start_time = time.time()
        errors = []
        total_rows = 0
        tables_written = []

        if not dest_db:
            return TransformResult(
                handler_name=self.name, rows_affected=0, tables_written=[],
                duration_ms=0, errors=["dest_db is required"],
            )

        today = date.today()
        from_date = (params or {}).get("from_date", str(today))
        to_date = (params or {}).get("to_date", str(today))
        report_date = (params or {}).get("report_date", str(today))
        publication_date_id = (params or {}).get("publication_date_id", 42)

        # Execute transforms in order (denormalize first, then aggregate)
        transforms = [
            ("dim_booth_voter", DenormalizeBoothVoter()),
            ("fact_booth_sir", BoothSIR()),
            ("fact_booth_cubs", BoothCUBS()),
            ("fact_voter_location", VoterLocation()),
        ]

        for table_name, transform in transforms:
            try:
                rows = transform.run(dest_db, from_date, to_date, report_date, publication_date_id)
                total_rows += rows
                tables_written.append(table_name)
            except Exception as e:
                error_msg = f"{table_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        dest_db.commit()
        duration_ms = int((time.time() - start_time) * 1000)
        return TransformResult(
            handler_name=self.name, rows_affected=total_rows,
            tables_written=tables_written, duration_ms=duration_ms, errors=errors,
        )
