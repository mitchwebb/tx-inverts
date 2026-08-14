import pytest
from backend.jobs.runners.run_update_backbone import main as run_update_backbone


class TestRunUpdateBackbone:
    @pytest.mark.asyncio
    async def test_create_invasives_table_first(self, mocker):
        mocker.patch(
            'backend.jobs.runners.run_update_backbone.get_single_db_connection',
            new=mocker.AsyncMock()
        )

        create_invasives = mocker.patch(
            'backend.jobs.runners.run_update_backbone.create_invasives_table',
            new=mocker.AsyncMock(side_effect=RuntimeError("test boom"))
        )

        update_backbone = mocker.patch(
            'backend.jobs.runners.run_update_backbone.update_backbone',
            new=mocker.AsyncMock()
        )

        with pytest.raises(RuntimeError):
            await run_update_backbone()

        create_invasives.assert_awaited_once()
        update_backbone.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_ranks_after(self, mocker):
        mocker.patch(
            'backend.jobs.runners.run_update_backbone.get_single_db_connection',
            new=mocker.AsyncMock()
        )

        mocker.patch(
            'backend.jobs.runners.run_update_backbone.create_invasives_table',
            new=mocker.AsyncMock()
        )

        update_backbone = mocker.patch(
            'backend.jobs.runners.run_update_backbone.update_backbone',
            new=mocker.AsyncMock(side_effect=RuntimeError("test boom"))
        )

        update_ns_ranks = mocker.patch(
            'backend.jobs.runners.run_update_backbone.update_ns_ranks',
            new=mocker.AsyncMock()
        )

        with pytest.raises(RuntimeError):
            await run_update_backbone()

        update_backbone.assert_awaited_once()
        update_ns_ranks.assert_not_awaited()
