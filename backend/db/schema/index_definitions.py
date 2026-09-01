# Various index and mat view creation statements and information

from pydantic import BaseModel, ConfigDict

from backend.constants.taxa import RANK_COLS
from backend.db.schema.base_table import DBTable
from backend.db.schema.gbif_inverts_backbone import GBIF_INVERTS_BACKBONE
from backend.db.schema.gbif_observations import GBIF_OBSERVATIONS_TABLE
from backend.db.schema.geometries import TEXAS_COUNTIES_TABLE, TEXAS_PARKS_TABLE
from backend.db.schema.observation_regions import OBSERVATION_REGIONS_TABLE
from backend.db.schema.regions import REGIONS_VIEW
from backend.db.schema.taxon_lineage import TAXON_LINEAGE_TABLE
from backend.db.schema.taxon_region_presence import TAXON_PRESENCE_TABLE
from backend.db.schema.tx_taxa import TX_TAXA_TABLE
from backend.db.schema.us_invasives_checklist import US_INVASIVES_TABLE
from psycopg import sql


class IndexDefinition(BaseModel):
    name: str
    table: DBTable
    clause: sql.Composable

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    def create_sql(self) -> sql.Composed:
        return sql.SQL('CREATE INDEX {name} ON {table} {clause}').format(
            name=sql.Identifier(self.name),
            table=sql.Identifier(self.table.name),
            clause=self.clause
        )


_all_indexes = [

    ### OBSERVATIONS_TABLE ###

    IndexDefinition(
        name='idx_gbif_observations_taxon_key',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(taxon_key)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_accepted_taxon_key',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(accepted_taxon_key)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_taxon_rank',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(taxon_rank)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_geom',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('USING GIST(geometry)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_id',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(gbif_id)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_start_date',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(collection_start_date)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_end_date',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(collection_end_date)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_taxon_date_not_null',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL(
            '(accepted_taxon_key) WHERE collection_start_date IS NOT NULL')
    ),
    IndexDefinition(
        name='idx_gbif_observations_geom_3857',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('USING GIST(ST_Transform(geometry, 3857))')
    ),
    IndexDefinition(
        name='idx_gbif_observations_institution_code',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(institution_code)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_dataset_key',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(dataset_key)')
    ),
    IndexDefinition(
        name='idx_gbif_observations_coordinate_uncertainty_in_meters',
        table=GBIF_OBSERVATIONS_TABLE,
        clause=sql.SQL('(coordinate_uncertainty_in_meters)')
    ),

    ### BACKBONE ###

    IndexDefinition(
        name='idx_inverts_backbone_taxon_id',
        table=GBIF_INVERTS_BACKBONE,
        clause=sql.SQL('(taxon_id)')
    ),
    IndexDefinition(
        name='idx_inverts_backbone_taxon_rank',
        table=GBIF_INVERTS_BACKBONE,
        clause=sql.SQL('(taxon_rank)')
    ),
    IndexDefinition(
        name='idx_inverts_backbone_normalized_name',
        table=GBIF_INVERTS_BACKBONE,
        clause=sql.SQL('(LOWER(canonical_name) text_pattern_ops)')
    ),
    IndexDefinition(
        name='idx_inverts_backbone_accepted_name_usage_id',
        table=GBIF_INVERTS_BACKBONE,
        clause=sql.SQL('(accepted_name_usage_id)')
    ),
    IndexDefinition(
        name='idx_inverts_backbone_us_invasive',
        table=GBIF_INVERTS_BACKBONE,
        clause=sql.SQL('(us_invasive)')
    ),

    ### TX_TAXA ###

    IndexDefinition(
        name='idx_tx_taxa_normalized_name',
        table=TX_TAXA_TABLE,
        clause=sql.SQL('(LOWER(canonical_name) text_pattern_ops)')
    ),
    IndexDefinition(
        name='idx_tx_taxa_ns_rank_state',
        table=TX_TAXA_TABLE,
        clause=sql.SQL('(ns_rank_state)')
    ),
    IndexDefinition(
        name='idx_tx_taxa_ns_rank_state_no_inat',
        table=TX_TAXA_TABLE,
        clause=sql.SQL('(ns_rank_state_no_inat)')
    ),
    IndexDefinition(
        name='idx_tx_taxa_parent_rank_status_name',
        table=TX_TAXA_TABLE,
        clause=sql.SQL(
            '(parent_name_usage_id, taxon_rank, taxonomic_status, canonical_name)')
    ),
    IndexDefinition(
        name='idx_tx_taxa_us_invasive',
        table=TX_TAXA_TABLE,
        clause=sql.SQL('(us_invasive)')
    ),

    ### INVASIVES TABLE ###

    IndexDefinition(
        name='idx_invasives_taxon_id',
        table=US_INVASIVES_TABLE,
        clause=sql.SQL('(taxon_id)')
    ),

    # REGIONS TABLES

    IndexDefinition(
        name='idx_tx_parks_name',
        table=TEXAS_PARKS_TABLE,
        clause=sql.SQL('(prop_name)')
    ),
    IndexDefinition(
        name='idx_tx_counties_name',
        table=TEXAS_COUNTIES_TABLE,
        clause=sql.SQL('(county)')
    ),
    IndexDefinition(
        name='idx_regions_obs_id',
        table=OBSERVATION_REGIONS_TABLE,
        clause=sql.SQL('(observation_id)')
    ),
    IndexDefinition(
        name='idx_obs_regions_id',
        table=OBSERVATION_REGIONS_TABLE,
        clause=sql.SQL('(region_id)')
    ),
    IndexDefinition(
        name='idx_regions_geometry',
        table=REGIONS_VIEW,
        clause=sql.SQL('USING GIST(geometry)')
    ),
    IndexDefinition(
        name='idx_taxon_presence_region_id',
        table=TAXON_PRESENCE_TABLE,
        clause=sql.SQL('(region_id)')
    ),

    ### TAXON LINEAGE ###

    IndexDefinition(
        name='idx_taxon_lineage_ancestor_id',
        table=TAXON_LINEAGE_TABLE,
        clause=sql.SQL('(ancestor_id)')),
    IndexDefinition(
        name='idx_taxon_lineage_taxon_key',
        table=TAXON_LINEAGE_TABLE,
        clause=sql.SQL('(accepted_taxon_key)')
    ),
    IndexDefinition(
        name='idx_taxon_lineage_ancestor_and_key',
        table=TAXON_LINEAGE_TABLE,
        clause=sql.SQL('(ancestor_id, accepted_taxon_key)')
    )
]

# Rank column indexes
for rank in RANK_COLS:
    _all_indexes.append(
        IndexDefinition(
            name=f'idx_gbif_observations_{rank}',
            table=GBIF_OBSERVATIONS_TABLE,
            clause=sql.SQL('({rank})').format(rank=sql.Identifier(rank)))
    )

INDEX_DEFINITIONS = {d.name: d for d in _all_indexes}

# View definitions (the order of these matters)
# These include index definitions for UNIQUE INDEX creation in order to
# allow CONCURRENT refreshes
MATERIALIZED_VIEWS = {
    'tx_taxa': {
        'create_sql': sql.SQL("""
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
                    AND parent.taxon_id != child.taxon_id
            )
            SELECT DISTINCT *
                FROM ancestors
        """).format(
            tx_taxa=sql.Identifier(TX_TAXA_TABLE.name),
            gbif_inverts_backbone=sql.Identifier(GBIF_INVERTS_BACKBONE.name),
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        ),
        'index_sql': sql.SQL(
            "CREATE UNIQUE INDEX ON {tx_taxa} (taxon_id)"
        ).format(tx_taxa=sql.Identifier(TX_TAXA_TABLE.name)),
    },
    # TODO: Ecoregions are currently hosted only on mapbox
    # If we want them to be searchable, we'll need to add them to local tables
    'regions': {
        'create_sql': sql.SQL("""
            CREATE MATERIALIZED VIEW {regions} AS
            SELECT id, 'county' AS region_type, county AS name, geometry FROM {tx_counties}
            UNION ALL
            SELECT id, 'park' AS region_type, prop_name AS name, geometry FROM {tx_parks}
        """).format(
            regions=sql.Identifier(REGIONS_VIEW.name),
            tx_counties=sql.Identifier(TEXAS_COUNTIES_TABLE.name),
            tx_parks=sql.Identifier(TEXAS_PARKS_TABLE.name),
        ),
        'index_sql': sql.SQL(
            "CREATE UNIQUE INDEX ON {regions} (region_type, id)"
        ).format(regions=sql.Identifier(REGIONS_VIEW.name)),
    },
    'taxon_region_presence': {
        'create_sql': sql.SQL("""
            CREATE MATERIALIZED VIEW {taxon_region_presence} AS
            SELECT DISTINCT accepted_taxon_key, region_id
            FROM {observations_table} o
            JOIN {observation_regions_table} r
                ON r.observation_id = o.gbif_id
        """).format(
            taxon_region_presence=sql.Identifier(TAXON_PRESENCE_TABLE.name),
            observations_table=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name),
            observation_regions_table=sql.Identifier(
                OBSERVATION_REGIONS_TABLE.name)
        ),
        'index_sql': sql.SQL(
            "CREATE UNIQUE INDEX ON {taxon_region_presence} (accepted_taxon_key, region_id)"
        ).format(taxon_region_presence=sql.Identifier(TAXON_PRESENCE_TABLE.name)),
    },
    'taxon_lineage': {
        'create_sql': sql.SQL("""
            CREATE MATERIALIZED VIEW {taxon_lineage} AS
            SELECT DISTINCT accepted_taxon_key,
            unnest(array_remove(ARRAY[
                accepted_taxon_key,
                {RANK_COLS}
            ], NULL)) AS ancestor_id
            FROM {gbif_observations}
            WHERE accepted_taxon_key IS NOT NULL;
        """).format(
            taxon_lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name),
            RANK_COLS=sql.SQL(', ').join(sql.Identifier(c) for c in RANK_COLS),
            gbif_observations=sql.Identifier(GBIF_OBSERVATIONS_TABLE.name)
        ),
        'index_sql': sql.SQL(
            "CREATE UNIQUE INDEX ON {taxon_lineage} (accepted_taxon_key, ancestor_id)"
        ).format(taxon_lineage=sql.Identifier(TAXON_LINEAGE_TABLE.name)),
    },
}
