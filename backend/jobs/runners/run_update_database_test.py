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

        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(
            f'{MODULE}.get_single_db_connection',
            new=AsyncMock(return_value=conn)
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
            f'{MODULE}.update_backbone',
            new=AsyncMock(side_effect=track('update_backbone'))
        )
        mocker.patch(
            f'{MODULE}.update_observations',
            new=AsyncMock(side_effect=track('update_observations'))
        )
        mocker.patch(
            f'{MODULE}.update_observation_regions',
            new=AsyncMock(side_effect=track('update_observation_regions'))
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
            'update_backbone',  # Update backbone
            'update_observations',  # Update observations table
            'update_observation_regions',  # Update observations_regions using new observations
            'update_ns_ranks',  # Update rankings using new observations
            'refresh_materialized_views',  # Refresh materialized views
            'update_indexes',  # Update indexes at the end
        ]
        # In this case (without update_backbone_required)
        conn.close.assert_awaited_once()
        conn.rollback.assert_not_awaited()

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
        update_indexes.assert_not_awaited()
