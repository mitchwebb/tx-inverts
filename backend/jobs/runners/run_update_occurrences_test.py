import pytest
from unittest.mock import AsyncMock
from backend.jobs.runners.run_update_occurrences import main as run_update_occurrences

MODULE = 'backend.jobs.runners.run_update_occurrences'


class TestRunUpdateOccurrences:
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

        await run_update_occurrences()

        assert order == [
            'update_observations',  # Update observations table
            'update_observation_regions',  # Update observations_regions using new observations
            'update_ns_ranks',  # Update rankings using new observations
            'refresh_materialized_views',  # Refresh materialized views
            'update_indexes',  # Update indexes at the end
        ]
        conn.close.assert_awaited_once()
        conn.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_mid_sequence_rolls_back_and_reraises(self, mocker):
        conn = AsyncMock()
        mocker.patch(f'{MODULE}.get_single_db_connection',
                     new=AsyncMock(return_value=conn))
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(f'{MODULE}.update_observations',
                     new=AsyncMock(return_value=(True, [], [])))
        mocker.patch(f'{MODULE}.update_observation_regions',
                     new=AsyncMock(side_effect=RuntimeError('big boom')))
        mocker.patch(
            f'{MODULE}.update_ns_ranks', new=AsyncMock())
        mocker.patch(
            f'{MODULE}.refresh_materialized_views', new=AsyncMock())
        update_indexes = mocker.patch(
            f'{MODULE}.update_indexes', new=AsyncMock())

        with pytest.raises(RuntimeError, match='big boom'):
            await run_update_occurrences()

        conn.rollback.assert_awaited_once()
        conn.close.assert_awaited_once()
        update_indexes.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_backbone_update_suggested(self, mocker):
        conn = AsyncMock()

        mocker.patch(
            f'{MODULE}.get_single_db_connection',
            new=AsyncMock(return_value=conn)
        )
        mocker.patch(f'{MODULE}.setup_logging')
        mocker.patch(
            f'{MODULE}.update_observations',
            new=AsyncMock(return_value=(True, ['row-key'], [123, 456]))
        )
        mocker.patch(
            f'{MODULE}.update_observation_regions',
            new=AsyncMock()
        )
        mocker.patch(
            f'{MODULE}.update_ns_ranks',
            new=AsyncMock()
        )
        mocker.patch(
            f'{MODULE}.refresh_materialized_views',
            new=AsyncMock()
        )
        mocker.patch(
            f'{MODULE}.update_indexes',
            new=AsyncMock()
        )

        tasks_logger = mocker.patch(f'{MODULE}.tasks_logger')

        await run_update_occurrences()

        # See if a log with a 'backbone' related message is logged
        assert any(
            'backbone' in call.args[0].lower()
            for call in tasks_logger.info.call_args_list
        )

        conn.close.assert_awaited_once()
