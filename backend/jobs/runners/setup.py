# General script for initial Texas Inverts backend setup

from backend.data_util.db import get_single_db_connection
from backend.data_util.execute_psql_query import execute_psql_query
from backend.data_util.gbif.observations_request import APPROVED_DATASETS
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.jobs.runners.run_async import run_async
from backend.jobs.tasks.indexes import update_indexes
from backend.jobs.tasks.datasets import fill_dataset_table
from backend.jobs.tasks.tables import initialize_all_tables
from backend.jobs.tasks.regions import fill_all_geometry_tables, update_observation_regions
from backend.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.jobs.tasks.occurrence import update_observations
from backend.jobs.tasks.taxa import create_invasives_table
from backend.core.logging import setup_logging, db_logger, data_logger, tasks_logger
from backend.jobs.tasks.views import refresh_materialized_views, refresh_materialized_view
from psycopg import sql
from backend.constants.paths import DATA_OUT_PATH
import os


# Initial script to create and populate database for Texas Inverts
async def main():
    setup_logging()

    conn = None

    try:
        if not os.path.exists(DATA_OUT_PATH):
            data_logger.info(f"Making data directory at {DATA_OUT_PATH}")
            os.makedirs(DATA_OUT_PATH)

        conn = await get_single_db_connection()

        create_test_db_query = sql.SQL("""
            CREATE DATABASE test_inverts;
            CREATE_USER test_user WITH ENCRYPTED PASSWORD 'test_pass';
            GRANT ALL PRIVILEGES ON DATABASE test_inverts TO test_user;
        """)
        await execute_psql_query(conn, create_test_db_query)

        # Initialize all tables (including mat views) and associated indexes
        await initialize_all_tables(conn, verbose=True, strict=True)

        # Fill dataset metadata table (provides correct names for datasets)
        await fill_dataset_table(conn, APPROVED_DATASETS)

        # Fill geometry tables with information from geojson and GDB files (mapped to new names)
        await fill_all_geometry_tables(conn, truncate=True)

        # Create invasives table
        await create_invasives_table(conn)

        # Taxonomy table initialization
        await update_backbone(conn)

        # Observations table initialization
        await update_observations(conn, chunk_size=100000)

        # Refresh taxon_lineage view to help with ns_ranks speed
        await refresh_materialized_view(conn, 'taxon_lineage')

        await update_indexes(conn)

        # Update ranks stored in db
        await update_ns_ranks(conn)

        # Fill observation_regions table!
        await update_observation_regions(conn, replace_all=True)

        await conn.commit()
        db_logger.info("Created observations_regions table")

        # Refresh materialized views now that they're filled
        await refresh_materialized_views(conn)

        tasks_logger.info(
            "Texas Inverts initial setup complete! Enjoy the app!")

    except Exception as e:
        db_logger.exception(f"Database initialization failed. Exiting. {e}")
        if conn is not None:
            await conn.rollback()
    finally:
        if conn is not None:
            await conn.close()

if __name__ == '__main__':
    run_async(main())
