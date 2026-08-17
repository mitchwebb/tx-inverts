import pytest
from unittest.mock import AsyncMock
from backend.jobs.runners.run_setup import main as run_setup


MODULE = 'backend.jobs.runners.run_setup'


class TestRunSetup:
    @pytest.mark.asyncio
    async def test_call_order(self, mocker):
        """Test to track important call order"""

        conn = AsyncMock()
        order = []

        def track(name):
            def _side_effect(*args, **kwargs):
                order.append(name)
            return _side_effect

        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(
            f'{MODULE}.get_single_db_connection',
            new=AsyncMock(return_value=conn)
        )
        mocker.patch(
            f'{MODULE}.create_test_db',
            new=AsyncMock(side_effect=track('create_test_db'))
        )
        mocker.patch(
            f'{MODULE}.initialize_all_tables',
            new=AsyncMock(side_effect=track('initialize_all_tables'))
        )
        mocker.patch(
            f'{MODULE}.fill_invasives_table',
            new=AsyncMock(side_effect=track('fill_invasives_table'))
        )
        mocker.patch(
            f'{MODULE}.fill_all_geometry_tables',
            new=AsyncMock(side_effect=track('fill_all_geometry_tables'))
        )
        mocker.patch(
            f'{MODULE}.fill_dataset_table',
            new=AsyncMock(side_effect=track('fill_dataset_table'))
        )
        mocker.patch(
            f'{MODULE}.update_backbone',
            new=AsyncMock(side_effect=track('update_backbone'))
        )
        # Return backbone_update_required = True to trigger backbone update
        mocker.patch(
            f'{MODULE}.update_observations',
            new=AsyncMock(side_effect=lambda *a, **
                          kw: (track('update_observations')(), (True, [], []))[1])
        )
        taxon_lineage_refresh = mocker.patch(
            f'{MODULE}.refresh_materialized_view',
            new=AsyncMock(side_effect=track('create_taxon_lineage'))
        )
        mocker.patch(
            f'{MODULE}.update_indexes',
            new=AsyncMock(side_effect=track('update_indexes'))
        )
        mocker.patch(
            f'{MODULE}.update_ns_ranks',
            new=AsyncMock(side_effect=track('update_ns_ranks'))
        )
        mocker.patch(
            f'{MODULE}.update_observation_regions',
            new=AsyncMock(side_effect=track('update_observation_regions'))
        )
        mocker.patch(
            f'{MODULE}.refresh_materialized_views',
            new=AsyncMock(side_effect=track('refresh_materialized_views'))
        )

        await run_setup()

        # Assert that materialized view call was indeed to taxon_lineage
        taxon_lineage_refresh.assert_any_call(conn, 'taxon_lineage')

        assert order == [
            'create_test_db',  # Create test database
            'initialize_all_tables',  # Initialize database tables
            'fill_invasives_table',  # Download invasives dataset and fill
            'fill_all_geometry_tables',  # Fill geometry tables with info
            # Fill table of dataset metadata. The order of this isn't ESSENTIAL, but it does need to be called
            'fill_dataset_table',
            'update_backbone',
            'update_observations',  # Update observations table
            'create_taxon_lineage',  # Create taxon_lineage mat view
            'update_indexes',  # Update indexes
            'update_ns_ranks',  # Update rankings
            'update_observation_regions',  # Update observations_regions
            'refresh_materialized_views',  # Refresh materialized views
        ]
        conn.close.assert_awaited_once()
        conn.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_mid_sequence_rolls_back_and_reraises(self, mocker):
        conn = AsyncMock()
        mocker.patch(f'{MODULE}.get_single_db_connection',
                     new=AsyncMock(return_value=conn))
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(f'{MODULE}.create_test_db', new=AsyncMock())
        mocker.patch(f'{MODULE}.initialize_all_tables', new=AsyncMock())
        mocker.patch(f'{MODULE}.fill_invasives_table', new=AsyncMock())
        mocker.patch(f'{MODULE}.fill_all_geometry_tables', new=AsyncMock())
        mocker.patch(f'{MODULE}.fill_dataset_table', new=AsyncMock())
        mocker.patch(f'{MODULE}.update_backbone', new=AsyncMock())
        # Break on update_observations
        mocker.patch(f'{MODULE}.update_observations', new=AsyncMock(
            side_effect=RuntimeError('big boom')))
        mocker.patch(f'{MODULE}.update_ns_ranks', new=AsyncMock())
        update_matviews = mocker.patch(
            f'{MODULE}.refresh_materialized_views', new=AsyncMock())

        with pytest.raises(RuntimeError, match='big boom'):
            await run_setup()

        conn.rollback.assert_awaited_once()
        conn.close.assert_awaited_once()
        update_matviews.assert_not_awaited()
