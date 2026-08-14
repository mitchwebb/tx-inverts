import pytest
from unittest.mock import AsyncMock

from backend.jobs.runners.run_update_ns_ranks import main as run_update_ns_ranks


class TestUpdateNSRanks:
    @pytest.mark.asyncio
    async def test_rollback_on_error(self, mocker):
        conn = AsyncMock()

        mocker.patch(
            "backend.jobs.runners.run_update_ns_ranks.get_single_db_connection",
            return_value=conn,
        )

        mocker.patch(
            'backend.jobs.runners.run_update_ns_ranks.update_ns_ranks',
            new=AsyncMock(side_effect=RuntimeError('big boom'))
        )
        with pytest.raises(RuntimeError, match='big boom'):
            await run_update_ns_ranks()

        conn.rollback.assert_awaited_once()
        conn.close.assert_awaited_once()
