import backend.constants.map as map
from backend.routers.taxa import RANK_COLS
from psycopg import sql


INDEX_DEFINITIONS = {
    'idx_gbif_observations_taxon_key': {
        'table': 'gbif_observations',
        'create_sql': 'CREATE INDEX idx_gbif_observations_taxon_key ON gbif_observations (taxon_key)'
    },
    'idx_gbif_observations_accepted_taxon_key': {
        'table': 'gbif_observations',
        'create_sql': 'CREATE INDEX idx_gbif_observations_accepted_taxon_key ON gbif_observations (accepted_taxon_key)'
    },
    'idx_gbif_observations_taxon_rank': {
        'table': 'gbif_observations',
        'create_sql': 'CREATE INDEX idx_gbif_observations_taxon_rank ON gbif_observations (taxon_rank)'
    },
    'idx_gbif_observations_geom': {
        'table': 'gbif_observations',
        'create_sql': 'CREATE INDEX idx_gbif_observations_geom ON gbif_observations USING GIST (geometry)'
    },
    'idx_gbif_observations_geom_3857': {
        'table': 'gbif_observations',
        'create_sql': '''
  			CREATE INDEX idx_gbif_observations_geom_3857 
     		ON gbif_observations USING GIST(ST_Transform(geometry, 3857))
    	'''
    },
    'idx_gbif_observations_institution_code': {
        'table': 'gbif_observations',
        'create_sql': '''
  			CREATE INDEX idx_gbif_observations_institution_code
     		ON gbif_observations(institution_code)
    	'''
    },
    'idx_inverts_backbone_taxon_id': {
        'table': 'gbif_inverts_backbone',
        'create_sql': '''
  			CREATE INDEX idx_inverts_backbone_taxon_id 
     		ON gbif_inverts_backbone(taxon_id)
       '''
    },
    'idx_inverts_backbone_taxon_rank': {
        'table': 'gbif_inverts_backbone',
        'create_sql': '''
  			CREATE INDEX idx_inverts_backbone_taxon_rank
  			ON gbif_inverts_backbone(taxon_rank)
    '''
    },
    'idx_inverts_backbone_normalized_name': {
        'table': 'gbif_inverts_backbone',
        'create_sql': '''
			CREATE INDEX idx_inverts_backbone_normalized_name
			ON gbif_inverts_backbone (LOWER(canonical_name) text_pattern_ops);
  		'''
    },
    'idx_inverts_backbone_accepted_name_usage_id': {
        'table': 'gbif_inverts_backbone',
        'create_sql': '''
			CREATE INDEX idx_inverts_backbone_accepted_name_usage_id
			ON gbif_inverts_backbone (accepted_name_usage_id);
  		'''
    },
    'idx_tx_taxa_normalized_name': {
        'table': 'tx_taxa',
        'create_sql': 'CREATE INDEX idx_tx_taxa_normalized_name ON tx_taxa(LOWER(canonical_name) text_pattern_ops)'
    },
    'idx_tx_taxa_ns_rank_state': {
        'table': 'tx_taxa',
        'create_sql': 'CREATE INDEX idx_tx_taxa_ns_rank_state ON tx_taxa(ns_rank_state)'
    },
    'idx_tx_taxa_parent_rank_status_name': {
        'table': 'tx_taxa',
        'create_sql': '''
  			CREATE INDEX idx_tx_taxa_parent_rank_status_name
			ON tx_taxa (parent_name_usage_id, taxon_rank, taxonomic_status, canonical_name);
        '''
    },
    'idx_tx_taxa_us_invasive': {
        'table': 'tx_taxa',
        'create_sql': '''
			CREATE INDEX idx_tx_taxa_us_invasive
			ON tx_taxa (us_invasive)
    	'''
    }
    # 'idx_taxon_tile_cache_tile_coords': {
    # 	'table': 'taxon_tile_cache',
    # 	'create_sql': '''
    # 		CREATE INDEX idx_taxon_tile_cache_tile_coords
    # 		ON taxon_tile_cache (zoom, x_bin, y_bin);
    # 	'''
    # },
    # 'idx_taxon_tile_cache_zoom_taxon': {
    # 	'table': 'taxon_tile_cache',
    # 	'create_sql': '''
    # 		CREATE INDEX idx_taxon_tile_cache_zoom_taxon
    # 		ON taxon_tile_cache (zoom, taxon_id);
    # 	'''
    # },
    # 'idx_taxon_tile_cache_geom': {
    # 	'table': 'taxon_tile_cache',
    # 	'create_sql': '''
    # 		CREATE INDEX idx_taxon_tile_cache_geom
    #  		ON taxon_tile_cache USING gist (geom);
    #  	'''
    # },
    # 'idx_taxon_tile_cache_institution_code': {
    # 	'table': 'taxon_tile_cache',
    # 	'create_sql': '''
    # 		CREATE INDEX idx_taxon_tile_cache_institution_code
    #  		ON taxon_tile_cache (institution_code);
    #  	'''
    # },
    # 'idx_taxon_descendant_cache_ancestor_key': {
    # 	'table': 'taxon_descendant_cache',
    # 	'create_sql': '''
    # 		CREATE INDEX idx_taxon_descendant_cache_ancestor_key
    # 		ON taxon_descendant_cache (ancestor_key);
    # 	'''
    # },
    # 'idx_taxon_descendant_cache_descendant_key': {
    # 	'table': 'taxon_descendant_cache',
    # 	'create_sql': '''
    # 		CREATE INDEX idx_taxon_descendant_cache_descendant_key
    # 		ON taxon_descendant_cache (descendant_key);
    # 	'''
    # }
}

# Rank column indexes
for rank in RANK_COLS:
    INDEX_DEFINITIONS[f'idx_gbif_observations_{rank}'] = {
        'table': 'gbif_observations',
        'create_sql': f'''
			CREATE INDEX idx_gbif_observations_{rank}
			ON gbif_observations ({rank})
		'''
    }

# Materialized view definitions (the order of these matters)
MATERIALIZED_VIEWS = {
    'tx_taxa': {
        'create_sql': sql.SQL('''
			CREATE MATERIALIZED VIEW tx_taxa AS
			WITH RECURSIVE ancestors AS (
				SELECT backbone.*
				FROM gbif_inverts_backbone backbone
				WHERE backbone.taxon_id IN (
					SELECT DISTINCT taxon_key FROM gbif_observations
				)
				
    			UNION ALL
				
    			SELECT parent.*
				FROM gbif_inverts_backbone parent
				JOIN ancestors child 
					ON parent.taxon_id IN (
         				child.parent_name_usage_id, 
             			child.accepted_name_usage_id
            		)
			)
			SELECT DISTINCT *
				FROM ancestors
		''')
    },
    'data_providers': {
        'create_sql': sql.SQL('''
            CREATE MATERIALIZED VIEW data_providers AS
            SELECT DISTINCT(dataset_key), publisher, institution_code
            FROM gbif_observations
            WHERE publisher IS NOT NULL
		''')
    }
    # 'taxon_descendant_cache': {
    # 	'create_sql': sql.SQL('''
    # 		CREATE MATERIALIZED VIEW taxon_descendant_cache AS
    # 		WITH RECURSIVE descendant_pairs AS (
    # 			SELECT
    # 				taxon_id AS ancestor_key,
    # 				taxon_id AS descendant_key,
    # 				taxon_rank AS descendant_taxon_rank
    # 			FROM gbif_inverts_backbone
    # 			UNION ALL
    # 			SELECT
    # 				dt.ancestor_key,
    # 				b.taxon_id,
    # 				b.taxon_rank
    # 			FROM gbif_inverts_backbone b
    # 			JOIN descendant_pairs dt ON b.parent_name_usage_id = dt.descendant_key
    # 		)
    # 		SELECT * FROM descendant_pairs;
    # 	''')
    # },
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
    # 			FROM gbif_observations o
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
