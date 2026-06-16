from unittest.mock import patch

from backend.data_util.taxa import get_observation_count


class TestGetObservationCount:
    # Make sure get_observation_count returns count on successful query
    async def test_result_returns_row(self, mocker, mock_conn):
        mocker.patch('backend.data_util.taxa.execute_psql_query',
                     return_value=(2, ))
        result = await get_observation_count(mock_conn, 334272)
        assert result == 2

    # Make sure get_observation_count returns None on empty query
    async def test_empty_result_returns_none(self, mocker, mock_conn):
        mocker.patch('backend.data_util.taxa.execute_psql_query',
                     return_value=None)
        result = await get_observation_count(mock_conn, 403258)
        assert result == None


# class TestBuildLineages:
