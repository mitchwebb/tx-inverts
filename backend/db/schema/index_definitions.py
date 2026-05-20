# Various index and mat view creation statements and information

from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.regions import REGIONS_VIEW
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from backend.routers.taxa import RANK_COLS
from psycopg import sql


INDEX_DEFINITIONS = {
    'idx_gbif_observations_taxon_key': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_taxon_key 
            ON {gbif_observations} (taxon_key)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_accepted_taxon_key': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_accepted_taxon_key 
            ON {gbif_observations} (accepted_taxon_key)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_taxon_rank': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_taxon_rank 
            ON {gbif_observations} (taxon_rank)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_geom': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_geom 
            ON {gbif_observations} USING GIST(geometry)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_id': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_id 
            ON {gbif_observations} (gbif_id)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_start_date': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_start_date 
            ON {gbif_observations} (collection_start_date)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_end_date': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_end_date 
            ON {gbif_observations} (collection_end_date)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_taxon_date_not_null': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_taxon_date_not_null 
            ON {gbif_observations} (accepted_taxon_key) 
            WHERE collection_start_date IS NOT NULL
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_geom_3857': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_geom_3857
            ON {gbif_observations} USING GIST(ST_Transform(geometry, 3857))
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_institution_code': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_institution_code
            ON {gbif_observations} (institution_code)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_gbif_observations_dataset_key': {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_gbif_observations_dataset_key
            ON {gbif_observations} (dataset_key)
        ''').format(
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    'idx_inverts_backbone_taxon_id': {
        'table': GBIF_INVERTS_BACKBONE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_inverts_backbone_taxon_id
            ON {gbif_inverts_backbone} (taxon_id)
        ''').format(
            gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
    },
    'idx_inverts_backbone_taxon_rank': {
        'table': GBIF_INVERTS_BACKBONE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_inverts_backbone_taxon_rank
            ON {gbif_inverts_backbone} (taxon_rank)
        ''').format(
            gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
    },
    'idx_inverts_backbone_normalized_name': {
        'table': GBIF_INVERTS_BACKBONE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_inverts_backbone_normalized_name
            ON {gbif_inverts_backbone} (LOWER(canonical_name) text_pattern_ops);
        ''').format(
            gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
    },
    'idx_inverts_backbone_accepted_name_usage_id': {
        'table': GBIF_INVERTS_BACKBONE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_inverts_backbone_accepted_name_usage_id
            ON {gbif_inverts_backbone} (accepted_name_usage_id);
          ''').format(
            gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name)
        )
    },
    'idx_tx_taxa_normalized_name': {
        'table': TX_TAXA_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_taxa_normalized_name
            ON {tx_taxa} (LOWER(canonical_name) text_pattern_ops)
        ''').format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name))
    },
    'idx_tx_taxa_ns_rank_state': {
        'table': TX_TAXA_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_taxa_ns_rank_state
            ON {tx_taxa} (ns_rank_state)
        ''').format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name))
    },
    'idx_tx_taxa_ns_rank_state_no_inat': {
        'table': TX_TAXA_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_taxa_ns_rank_state_no_inat
            ON {tx_taxa} (ns_rank_state_no_inat)
        ''').format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name))
    },
    'idx_tx_taxa_parent_rank_status_name': {
        'table': TX_TAXA_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_taxa_parent_rank_status_name
            ON {tx_taxa} (parent_name_usage_id, taxon_rank, taxonomic_status, canonical_name);
        ''').format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name))
    },
    'idx_tx_taxa_us_invasive': {
        'table': TX_TAXA_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_taxa_us_invasive
            ON {tx_taxa} (us_invasive)
        ''').format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name))
    },
    'idx_inverts_backbone_us_invasive': {
        'table': GBIF_INVERTS_BACKBONE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_inverts_backbone_us_invasive
            ON {gbif_inverts_backbone} (us_invasive);
        ''').format(gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name))
    },
    'idx_invasives_taxon_id': {
        'table': US_INVASIVES_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_invasives_taxon_id
            ON {us_invasives_checklist} (taxon_id);
        ''').format(us_invasives_checklist=sql.Identifier(US_INVASIVES_TABLE.name))
    },
    'idx_tx_parks_name': {
        'table': TEXAS_PARKS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_parks_name
            ON {tx_parks} (prop_name);
        ''').format(tx_parks=sql.Identifier(TEXAS_PARKS_TABLE.name))
    },
    'idx_tx_counties_name': {
        'table': TEXAS_COUNTIES_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_tx_counties_name
            ON {tx_counties} (county);
        ''').format(tx_counties=sql.Identifier(TEXAS_COUNTIES_TABLE.name))
    },
    'idx_regions_obs_id': {
        'table': OBSERVATION_REGIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_regions_obs_id
            ON {observation_regions} (observation_id);
        ''').format(observation_regions=sql.Identifier(OBSERVATION_REGIONS_TABLE.name))
    },
    'idx_obs_regions_id': {
        'table': OBSERVATION_REGIONS_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_obs_regions_id
            ON {observation_regions} (region_id);
        ''').format(observation_regions=sql.Identifier(OBSERVATION_REGIONS_TABLE.name))
    },
    'idx_regions_geometry': {
        'table': REGIONS_VIEW.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_regions_geometry
            ON {regions} USING GIST (geometry);
        ''').format(regions=sql.Identifier(REGIONS_VIEW.name))
    },
    'idx_taxon_presence_region_id': {
        'table': TAXON_PRESENCE_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_taxon_presence_region_id
            ON {taxon_region_presence} (region_id)
        ''').format(taxon_region_presence=sql.Identifier(TAXON_PRESENCE_TABLE.name))
    },
    'idx_taxon_lineage_ancestor_id': {
        'table': TAXON_LINEAGE_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_taxon_lineage_ancestor_id 
            ON {taxon_lineage} (ancestor_id);
        ''').format(taxon_lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name))
    },
    'idx_taxon_lineage_taxon_key': {
        'table': TAXON_LINEAGE_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_taxon_lineage_taxon_key
            ON {taxon_lineage} (accepted_taxon_key)
        ''').format(taxon_lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name))
    },
    'idx_taxon_lineage_ancestor_and_key': {
        'table': TAXON_LINEAGE_TABLE.name,
        'create_sql': sql.SQL('''
            CREATE INDEX idx_taxon_lineage_ancestor_and_key
            ON {taxon_lineage} (ancestor_id, accepted_taxon_key);
        ''').format(taxon_lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name))
    }
}

# Rank column indexes
for rank in RANK_COLS:
    INDEX_DEFINITIONS[f'idx_gbif_observations_{rank}'] = {
        'table': GBIF_OBSERVATIONS_TABLE.name,
        'create_sql': sql.SQL("""
            CREATE INDEX {index_name}
            ON {observations_table} ({rank})
        """).format(
            index_name=sql.Identifier(f'idx_gbif_observations_{rank}'),
            observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            rank=sql.Identifier(rank)
        )
    }

# View definitions (the order of these matters)
MATERIALIZED_VIEWS = {
    'tx_taxa': {
        'create_sql': sql.SQL('''
            CREATE MATERIALIZED VIEW {tx_taxa} AS
            WITH RECURSIVE ancestors AS (
                SELECT backbone.*
                FROM {gbif_inverts_backbone} backbone
                WHERE backbone.taxon_id IN (
                    SELECT DISTINCT taxon_key FROM {gbif_observations}
                )

                UNION ALL

                SELECT parent.*
                FROM {gbif_inverts_backbone} parent
                JOIN ancestors child
                    ON parent.taxon_id IN (
                        child.parent_name_usage_id,
                        child.accepted_name_usage_id
                    )
            )
            SELECT DISTINCT *
                FROM ancestors
        ''').format(
            tx_taxa=sql.Identifier(TX_TAXA_TABLE.name),
            gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    # TODO: Ecoregions are currently hosted only on mapbox
    # If we want them to be searchable, we'll need to add them to local tables
    'regions': {
        'create_sql': sql.SQL('''
            CREATE MATERIALIZED VIEW {regions} AS
            SELECT id, 'county' AS region_type, county AS name, geometry FROM {tx_counties}
            UNION ALL
            SELECT id, 'park' AS region_type, prop_name AS name, geometry FROM {tx_parks}
        ''').format(
            regions=sql.Identifier(REGIONS_VIEW.name),
            tx_counties=sql.Identifier(TEXAS_COUNTIES_TABLE.name),
            tx_parks=sql.Identifier(TEXAS_PARKS_TABLE.name),
        )
    },
    'taxon_region_presence': {
        'create_sql': sql.SQL('''
            CREATE MATERIALIZED VIEW {taxon_region_presence} AS
            SELECT DISTINCT accepted_taxon_key, region_id
            FROM {observations_table} o
            JOIN {observation_regions_table} r
                ON r.observation_id = o.gbif_id
        ''').format(
            taxon_region_presence=sql.Identifier(TAXON_PRESENCE_TABLE.name),
            observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            observation_regions_table=sql.Identifier(
                OBSERVATION_REGIONS_TABLE.name)
        )
    },
    'taxon_lineage': {
        'create_sql': sql.SQL('''
            CREATE MATERIALIZED VIEW {taxon_lineage} AS
            SELECT DISTINCT accepted_taxon_key,
            unnest(ARRAY[accepted_taxon_key, kingdom_id, phylum_id, class_id, order_id, family_id, genus_id, species_id, subspecies_id]) AS ancestor_id
            FROM {gbif_observations}
            WHERE accepted_taxon_key IS NOT NULL;
        ''').format(
            taxon_lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name),
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        )
    },
    # The most imposing thing here are the cell location calculations
    # These convert lat/lon manually into Web Mercator coords in meters
    # where (2 * half_world) / 2 ^ zoom = tile_width in meters
    # 'taxon_tile_cache': {
    # 	'create_sql': sql.SQL('''
    # 		CREATE MATERIALIZED VIEW taxon_tile_cache AS
    # 		WITH zoom_levels AS (
    # 			SELECT unnest({zoom_levels}) AS zoom
    # 		),
    # 		transformed_obs AS (
    # 			SELECT
    # 				o.taxon_key,
    # 				o.publisher,
    # 				descendant.ancestor_key AS taxon_id,
    # 				ST_Transform(o.geometry, 3857) AS geom_3857
    # 			FROM {gbif_observations} o
    # 			JOIN taxon_descendant_cache descendant
    # 				ON descendant.descendant_key = o.taxon_key
    # 		),
    # 		grid AS (
    # 			SELECT
    # 				t.taxon_id,
    # 				t.publisher,
    # 				z.zoom,
    # 				FLOOR(ST_X(t.geom_3857) / b.bin_size)::int AS x_bin,
    # 				FLOOR(ST_Y(t.geom_3857) / b.bin_size)::int AS y_bin,
    # 				COUNT(*) AS observation_count,
    # 				ST_SetSRID(
    # 					ST_MakeEnvelope(
    # 						FLOOR(ST_X(t.geom_3857) / b.bin_size)::int * b.bin_size,
    # 						FLOOR(ST_Y(t.geom_3857) / b.bin_size)::int * b.bin_size,
    # 						(FLOOR(ST_X(t.geom_3857) / b.bin_size)::int + 1) * b.bin_size,
    # 						(FLOOR(ST_Y(t.geom_3857) / b.bin_size)::int + 1) * b.bin_size
    # 					),
    # 					3857
    # 				) AS geom
    # 			FROM transformed_obs t
    # 			JOIN zoom_levels z ON TRUE
    # 			CROSS JOIN LATERAL (
    # 				SELECT ((2 * {half_world}) / (2^z.zoom * (256 / {pixels_per_grid}))) AS bin_size
    # 			) b
    # 			GROUP BY t.taxon_id, z.zoom, x_bin, y_bin, t.publisher, b.bin_size
    # 		)
    # 		SELECT * FROM grid;
    # 	''').format(
    # 		pixels_per_grid = sql.Literal(map.PIXELS_PER_GRID),
    # 		zoom_levels = sql.Literal(map.BIN_ZOOM_LEVELS),
    # 		half_world = sql.Literal(map.HALF_WORLD)
    #    	)
    # },
    # 'ns_values_cache': {
    # 	'create_sql': sql.SQL('''

    #     ''')
    # }
}
