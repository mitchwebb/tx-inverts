# General script for initial Texas Inverts backend setup

from backend.data_util.db import get_single_db_connection
from backend.db_schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db_schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.tools.jobs.runners.run_async import run_async
from backend.tools.jobs.tasks.database import update_indexes
from backend.tools.jobs.tasks.datasets import fill_dataset_table
from backend.tools.jobs.tasks.initialize_db import initialize_all_tables
from backend.tools.jobs.tasks.regions import fill_all_geometry_tables
from backend.tools.jobs.tasks.taxa import update_backbone, update_ns_ranks
from backend.tools.jobs.tasks.occurrence import update_observations
from backend.tools.jobs.tasks.taxa import create_invasives_table
from backend.core.logging import setup_logging, db_logger
from backend.tools.jobs.tasks.views import refresh_materialized_views, refresh_materialized_view
from psycopg import sql


# Initial script to create and populate database for Texas Inverts
async def main():
    setup_logging()

    conn = await get_single_db_connection()

    try:
        # Initialize all tables (including mat views) and associated indexes
        await initialize_all_tables(conn, verbose=True, strict=True)

        # Fill dataset metadata table (provides correct names for datasets)
        await fill_dataset_table(conn)

        # Fill geometry tables with information from geojson and GDB files (mapped to new names)
        await fill_all_geometry_tables(conn, truncate=True)

        # Create invasives table
        await create_invasives_table()

        # Taxonomy table initialization
        await update_backbone()

        # Observations table initialization
        await update_observations(chunk_size=100000)

        # Refresh taxon_lineage view to help with ns_ranks speed
        await refresh_materialized_view(conn, 'taxon_lineage')

        await update_indexes(conn)

        # Update ranks stored in db
        await update_ns_ranks(conn)

        # Fill observation_regions table!
        # TODO: Extract to separate task
        db_logger.info('Filling observations_regions table...')
        async with conn.cursor() as cur:
            query = sql.SQL('''
                INSERT INTO {observation_regions_table}(observation_id, region_id, region_type)
                SELECT o.gbif_id, r.id, r.region_type
                FROM {observations_table} o
                JOIN regions r ON ST_Intersects(o.geometry, r.geometry)
            ''').format(
                observation_regions_table=sql.Identifier(
                    OBSERVATION_REGIONS_TABLE.name),
                observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
            )

            await cur.execute(query)

        await conn.commit()
        db_logger.info('Created observations_regions table')

        # Refresh materialized views now that they're filled
        await refresh_materialized_views(conn)

        # This step could be easier if provided local files
    except Exception as e:
        db_logger.exception(f'Database initialization failed. Exiting. {e}')
        await conn.rollback()
    finally:
        await conn.close()

if __name__ == '__main__':
    run_async(main())
