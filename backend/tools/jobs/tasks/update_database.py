from backend.data_util.db import get_single_db_connection
from backend.tools.jobs.tasks.database import update_indexes
from backend.tools.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.tools.jobs.tasks.occurrence import update_observations
from backend.tools.jobs.tasks.views import refresh_materialized_views


# Automatically update observations table from GBIF
# This function grabs new records (determined by latest modified date value currently in table)
# and ALSO grabs all records with no modified date (as there is no way to vet these)
async def update_database():
    backbone_update_required, new_row_keys = await update_observations()

    if backbone_update_required:
        await update_backbone()

    # # Insert to database
    conn = await get_single_db_connection()

    try:
        # # Update NatureServe ranks for updated species
        if new_row_keys:
            await update_ns_ranks(conn, new_row_keys)

        # Refresh the materialized views
        await refresh_materialized_views(conn)

        await update_indexes(conn)

        await conn.commit()

    finally:
        await conn.close()
