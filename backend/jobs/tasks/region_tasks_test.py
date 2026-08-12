from backend.jobs.tasks.region_tasks import update_observation_regions
import pytest


class TestUpdateObservationRegions:
    @pytest.mark.asyncio
    async def test_updates_indexes_first(self, mocker, conn):
        # Watch update_index
        update_index = mocker.patch(
            "backend.jobs.tasks.region_tasks.update_index",
            new=mocker.AsyncMock(),
        )
        # Patch execute_psql_query to error
        mocker.patch(
            "backend.jobs.tasks.region_tasks.execute_psql_query",
            new=mocker.AsyncMock(side_effect=RuntimeError("test_boom")),
        )
        mocker.patch.object(conn, "rollback", new=mocker.AsyncMock())

        # Run with error
        with pytest.raises(RuntimeError):
            await update_observation_regions(conn)

        # Verify that our indexes were updated before the failure
        update_index.assert_any_await(conn, 'idx_obs_regions_id')
        update_index.assert_any_await(conn, 'idx_regions_geometry')
        assert update_index.await_count == 2

    @pytest.mark.asyncio
    async def test_commits_on_success(self, mocker, conn):
        mocker.patch(
            "backend.jobs.tasks.region_tasks.update_index", new=mocker.AsyncMock()
        )
        mocker.patch(
            "backend.jobs.tasks.region_tasks.execute_psql_query",
            new=mocker.AsyncMock(),
        )
        commit = mocker.patch.object(conn, "commit", new=mocker.AsyncMock())

        await update_observation_regions(conn, new_observation_ids=[1])

        commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self, mocker, conn):
        mocker.patch(
            "backend.jobs.tasks.region_tasks.update_index",
            new=mocker.AsyncMock(side_effect=RuntimeError("boom")),
        )
        rollback = mocker.patch.object(conn, "rollback", new=mocker.AsyncMock())
        commit = mocker.patch.object(conn, "commit", new=mocker.AsyncMock())

        with pytest.raises(RuntimeError):
            await update_observation_regions(conn, new_observation_ids=[1])

        rollback.assert_awaited_once()
        commit.assert_not_awaited()

    ### BRANCH ORDERING ###
    @pytest.mark.asyncio
    async def test_replace_all_true_truncates_and_recomputes(self, mocker, conn):
        """Basic ordering check to see that replace_all=True triggers truncate -> insert queries."""

        mocker.patch("backend.jobs.tasks.region_tasks.update_index",
                     new=mocker.AsyncMock())
        execute_query = mocker.patch(
            "backend.jobs.tasks.region_tasks.execute_psql_query", new=mocker.AsyncMock()
        )
        mocker.patch.object(conn, "commit", new=mocker.AsyncMock())

        await update_observation_regions(conn, replace_all=True)

        queries = [call.args[1].as_string(None)
                   for call in execute_query.await_args_list]
        assert execute_query.await_count == 2
        assert "TRUNCATE" in queries[0]
        assert "INSERT INTO" in queries[1]
        assert "WHERE" not in queries[1]

    @pytest.mark.asyncio
    async def test_no_ids_provided_truncates_and_recomputes(self, mocker, conn):
        """Basic ordering check to see that empty ids triggers truncate -> insert queries"""

        mocker.patch("backend.jobs.tasks.region_tasks.update_index",
                     new=mocker.AsyncMock())
        execute_query = mocker.patch(
            "backend.jobs.tasks.region_tasks.execute_psql_query", new=mocker.AsyncMock()
        )
        mocker.patch.object(conn, "commit", new=mocker.AsyncMock())

        await update_observation_regions(conn, new_observation_ids=None, replace_all=False)

        queries = [call.args[1].as_string(None)
                   for call in execute_query.await_args_list]
        assert execute_query.await_count == 2
        assert "TRUNCATE" in queries[0]
        assert "INSERT INTO" in queries[1]
        assert "WHERE" not in queries[1]

    @pytest.mark.asyncio
    async def test_specific_ids_deletes_and_inserts_only_those(self, mocker, conn):
        """Basic ordering check to see that providing ids triggers targeted replacement queries"""

        mocker.patch("backend.jobs.tasks.region_tasks.update_index",
                     new=mocker.AsyncMock())
        execute_query = mocker.patch(
            "backend.jobs.tasks.region_tasks.execute_psql_query", new=mocker.AsyncMock()
        )
        mocker.patch.object(conn, "commit", new=mocker.AsyncMock())

        await update_observation_regions(conn, new_observation_ids=[1, 2, 3])

        queries = [call.args[1].as_string(None)
                   for call in execute_query.await_args_list]
        assert execute_query.await_count == 2
        assert "DELETE FROM" in queries[0]
        assert "INSERT INTO" in queries[1] and "WHERE" in queries[1]

    @pytest.mark.asyncio
    async def test_replace_all_wins_over_provided_ids(self, mocker, conn):
        """Basic ordering check to see that ids are ignored when replace_all=True"""

        mocker.patch("backend.jobs.tasks.region_tasks.update_index",
                     new=mocker.AsyncMock())
        execute_query = mocker.patch(
            "backend.jobs.tasks.region_tasks.execute_psql_query", new=mocker.AsyncMock()
        )
        mocker.patch.object(conn, "commit", new=mocker.AsyncMock())

        await update_observation_regions(conn, new_observation_ids=[1, 2, 3], replace_all=True)

        queries = [call.args[1].as_string(None)
                   for call in execute_query.await_args_list]
        assert "TRUNCATE" in queries[0]
        assert not any("DELETE" in q for q in queries)
