from backend.config.data import DATA_OUT_PATH
from backend.data_util.db import get_single_db_connection
from backend.tools.jobs.tasks.database import update_indexes
from backend.tools.jobs.tasks.initialize_db import initialize_all_tables
from backend.tools.jobs.tasks.regions import update_observation_regions
from backend.tools.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.tools.jobs.tasks.occurrence import update_observations
from backend.tools.jobs.tasks.views import refresh_materialized_views
import os


# Automatically update observations table from GBIF
# This function grabs new records (determined by latest modified date value currently in table)
# and ALSO grabs all records with no modified date (as there is no way to vet these)
async def update_database():

    # Insert to database
    conn = await get_single_db_connection()

    # Quick check to make sure tables are created
    await initialize_all_tables(conn)

    # Make sure indexes are ready
    await update_indexes(conn)
    await conn.commit()

    # Update observations, returning new taxon_keys and row_ids
    backbone_update_required, new_row_keys, new_row_ids = await update_observations()

    await update_observation_regions(conn, new_row_ids)

    if backbone_update_required:
        updated = await update_backbone()
        # A bit deceptive, but new_row_keys == None means update ALL rows
        if updated:
            new_row_keys = None

    try:
        # TODO: Bug with new_row_keys. These are under-represented with new observations
        # # Update NatureServe ranks for updated species
        if new_row_keys:
            await update_ns_ranks(conn, new_row_keys)

        # Refresh the materialized views
        await refresh_materialized_views(conn)

        await update_indexes(conn)

        await conn.commit()

    finally:
        await conn.close()
