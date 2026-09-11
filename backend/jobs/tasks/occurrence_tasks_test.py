from unittest.mock import AsyncMock

import pytest

from backend.jobs.tasks.occurrence_tasks import update_observations


# Helper to return a sample observations DF chunk
def make_chunk():
    import pandas as pd
    return pd.DataFrame([
        {
            'gbif_id': 1,
            'taxon_key': 1,
            'accepted_taxon_key': 1,
            'decimal_latitude': 5.0,
            'decimal_longitude': 5.0,
            'parent_name_usage_id': 1
        }
    ])


class TestUpdateObservations:
    # Test that, when not provided with an fp, update_observations calls get_gbif_inverts_file
    @pytest.mark.asyncio
    async def test_update_observations_calls_get_file(
        self,
        mocker,
        conn,
        setup_gbif_schema  # Make sure tables exist for test
    ):

        mock_get_file = mocker.patch(
            'backend.jobs.tasks.occurrence_tasks.get_gbif_inverts_file',
            return_value=''

        )

        with pytest.raises(Exception):
            await update_observations(conn, fp=None)

        mock_get_file.assert_called_once()
