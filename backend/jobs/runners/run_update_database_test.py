import pytest
from unittest.mock import AsyncMock

from backend.jobs.runners.run_update_database import main as run_update_database

MODULE = 'backend.jobs.runners.run_update_database'


class TestUpdateDatabase:
    @pytest.mark.asyncio
    async def test_call_order(self, mocker):
        """Test to track important call order"""

        conn = AsyncMock()
        order = []

        def track(name):
            def _side_effect(*args, **kwargs):
                order.append(name)
            return _side_effect

        mocker.patch(
            f'{MODULE}.get_single_db_connection',
            new=AsyncMock(return_value=conn)
        )
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(
            f'{MODULE}.initialize_all_tables',
            new=AsyncMock(side_effect=track('initialize_all_tables'))
        )
        mocker.patch(
            f'{MODULE}.fill_invasives_table',
            new=AsyncMock(side_effect=track('fill_invasives_table'))
        )
        # Return backbone_update_required = True to trigger backbone update
        mocker.patch(
            f'{MODULE}.update_observations',
            new=AsyncMock(side_effect=lambda *a, **
                          kw: (track('update_observations')(), (True, [], []))[1])
        )
        mocker.patch(
            f'{MODULE}.update_observation_regions',
            new=AsyncMock(side_effect=track('update_observation_regions'))
        )
        mocker.patch(
            f'{MODULE}.update_backbone',
            new=AsyncMock(side_effect=track('update_backbone'))
        )
        mocker.patch(
            f'{MODULE}.update_ns_ranks',
            new=AsyncMock(side_effect=track('update_ns_ranks'))
        )
        mocker.patch(
            f'{MODULE}.refresh_materialized_views',
            new=AsyncMock(side_effect=track('refresh_materialized_views'))
        )

        mocker.patch(
            f'{MODULE}.update_indexes',
            new=AsyncMock(side_effect=track('update_indexes'))
        )

        await run_update_database()

        assert order == [
            'initialize_all_tables',  # Make sure tables exist
            'fill_invasives_table',
            'update_observations',  # Update observations table
            'update_observation_regions',  # Update observations_regions using new observations
            'update_backbone',  # Update backbone (on backbone_update_required)
            'update_ns_ranks',  # Update rankings using new observations
            'refresh_materialized_views',  # Refresh materialized views
            'update_indexes',  # Update indexes at the end
        ]
        # In this case (without update_backbone_required)
        conn.close.assert_awaited_once()
        conn.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_backbone_update_required_true(self, mocker):
        """Make sure backbone update gets triggered correctly"""

        conn = AsyncMock()
        # Patch various functions to skip through
        mocker.patch(
            f'{MODULE}.get_single_db_connection',
            new=AsyncMock(return_value=conn)
        )
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(f'{MODULE}.fill_invasives_table', new=AsyncMock())
        mocker.patch(f'{MODULE}.initialize_all_tables', new=AsyncMock())
        mocker.patch(f'{MODULE}.update_indexes', new=AsyncMock())
        # Return backbone_update_required = True and dummy keys
        mocker.patch(
            f'{MODULE}.update_observations',
            new=AsyncMock(return_value=(True, ['key1'], ['id1']))
        )
        mocker.patch(f'{MODULE}.update_observation_regions', new=AsyncMock())
        update_backbone = mocker.patch(
            f'{MODULE}.update_backbone', new=AsyncMock(side_effect=RuntimeError('big boom')))

        with pytest.raises(RuntimeError, match='big boom'):
            await run_update_database()

        update_backbone.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_backbone_update_required_false(self, mocker):
        """Make sure backbone update gets skipped if update_observations returns backbone_update_required=False"""

        conn = AsyncMock()
        # Patch various functions to skip through
        mocker.patch(f'{MODULE}.get_single_db_connection',
                     new=AsyncMock(return_value=conn))
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(f'{MODULE}.initialize_all_tables', new=AsyncMock())
        mocker.patch(f'{MODULE}.fill_invasives_table', new=AsyncMock())
        mocker.patch(f'{MODULE}.update_indexes', new=AsyncMock())
        # Return backbone_update_required = False and dummy keys
        mocker.patch(f'{MODULE}.update_observations', new=AsyncMock(
            return_value=(False, ['key1', 'key2'], ['id1'])))
        mocker.patch(f'{MODULE}.update_observation_regions', new=AsyncMock())
        # Keep track of update_backbone to see if it runs
        update_backbone = mocker.patch(
            f'{MODULE}.update_backbone', new=AsyncMock())
        mocker.patch(
            f'{MODULE}.update_ns_ranks', new=AsyncMock(side_effect=RuntimeError('big boom'))
        )

        with pytest.raises(RuntimeError, match='big boom'):
            await run_update_database()

        update_backbone.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_mid_sequence_rolls_back_and_reraises(self, mocker):
        conn = AsyncMock()
        mocker.patch(f'{MODULE}.get_single_db_connection',
                     new=AsyncMock(return_value=conn))
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(f'{MODULE}.initialize_all_tables', new=AsyncMock())
        mocker.patch(f'{MODULE}.fill_invasives_table', new=AsyncMock())
        mocker.patch(f'{MODULE}.update_observations',
                     new=AsyncMock(return_value=(True, [], [])))
        mocker.patch(f'{MODULE}.update_observation_regions',
                     new=AsyncMock(side_effect=RuntimeError('big boom')))
        update_backbone = mocker.patch(
            f'{MODULE}.update_backbone', new=AsyncMock())
        mocker.patch(
            f'{MODULE}.update_ns_ranks', new=AsyncMock())
        mocker.patch(
            f'{MODULE}.refresh_materialized_views', new=AsyncMock())
        update_indexes = mocker.patch(
            f'{MODULE}.update_indexes', new=AsyncMock())

        with pytest.raises(RuntimeError, match='big boom'):
            await run_update_database()

        conn.rollback.assert_awaited_once()
        conn.close.assert_awaited_once()
        update_backbone.assert_not_awaited()
        update_indexes.assert_not_awaited()
