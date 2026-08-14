import pytest
from backend.jobs.runners.run_fill_dataset_table import main as run_fill_dataset_table


class TestFillDatasetTable:
    @pytest.mark.asyncio
    async def test_check_order(self, mocker):
        """
        Verify that initialization is called before fill.
        Also happens to test error raising.
        """

        mocker.patch(
            "backend.jobs.runners.run_fill_dataset_table.get_single_db_connection",
            new=mocker.AsyncMock()
        )

        initialize_call = mocker.patch(
            "backend.jobs.runners.run_fill_dataset_table.initialize_table",
            new=mocker.AsyncMock(side_effect=RuntimeError("test boom")),
        )

        fill_call = mocker.patch(
            "backend.jobs.runners.run_fill_dataset_table.fill_dataset_table",
            new=mocker.AsyncMock(),
        )

        with pytest.raises(RuntimeError):
            await run_fill_dataset_table()

        initialize_call.assert_awaited_once()
        fill_call.assert_not_awaited()
