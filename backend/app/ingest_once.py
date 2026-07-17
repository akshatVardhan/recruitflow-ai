"""RF-92: Cloud Run Job entrypoint for document ingestion.

Invoked as `python -m app.ingest_once` by the recruitflow-ingest Job,
triggered per upload via app/core/ingestion_trigger.py. Reads DOCUMENT_ID
from the environment (set as a per-execution container override, not baked
into the job's static config) and runs the shared ingestion pipeline once.
"""

import asyncio
import logging
import os
import sys

from app.core.ingestion_pipeline import run_ingestion_pipeline

logger = logging.getLogger(__name__)


def main() -> int:
    document_id = os.environ.get("DOCUMENT_ID")
    if not document_id:
        print("DOCUMENT_ID environment variable is required", file=sys.stderr)
        return 1

    final_status = asyncio.run(run_ingestion_pipeline(document_id))
    if final_status != "completed":
        logger.error(
            f"Ingestion did not complete for document {document_id}: "
            f"status={final_status}"
        )
        return 1

    logger.info(f"Ingestion complete for document {document_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
