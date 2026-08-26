from backend.data_util.db import get_single_db_connection
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.jobs.runners.run_async import run_async
from backend.core.logging import setup_logging, tasks_logger
from backend.jobs.tasks.index_tasks import update_indexes
from backend.jobs.tasks.occurrence_tasks import update_observations
from backend.jobs.tasks.region_tasks import update_observation_regions
from backend.jobs.tasks.table_tasks import initialize_all_tables
from backend.jobs.tasks.taxon_tasks import fill_invasives_table, update_backbone, update_ns_ranks
from backend.jobs.tasks.view_tasks import refresh_materialized_views


async def main():
    """
    Automatically update observations table from GBIF.
    This function grabs new records (determined by latest modified date value currently in table).
    It also grabs all records with no modified date (as there is no way to vet these).
    """

    conn = None
    try:
        setup_logging()
        tasks_logger.info("Starting update_database job...")

        # Insert to database
        conn = await get_single_db_connection()

        # Quick check to make sure tables are created
        await initialize_all_tables(conn)

        # Create invasives table
        await fill_invasives_table(conn)

        # Update observations, returning new taxon_keys and row_ids
        backbone_update_required, new_row_keys, new_row_ids = await update_observations(conn, delete_file=True, full_replace=True)

        await update_observation_regions(conn, new_row_ids)

        if backbone_update_required:
            await update_backbone(conn)
            # await resolve_taxon_lineage(conn, GBIF_OBSERVATIONS_TABLE.name)
            # A bit deceptive, but new_row_keys == None means update ALL rows
            new_row_keys = None

        # Update conservation ranks
        await update_ns_ranks(conn, new_row_keys)

        # Refresh the materialized views
        await refresh_materialized_views(conn)

        await update_indexes(conn)

    except Exception as e:
        tasks_logger.exception(f"Update database task failed. Exiting. {e}")
        if conn is not None:
            await conn.rollback()
        raise
    finally:
        if conn is not None:
            await conn.close()

    tasks_logger.info("update_database job finished")


if __name__ == '__main__':
    run_async(main())
