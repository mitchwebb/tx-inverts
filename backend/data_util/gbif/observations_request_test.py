import json
import aiohttp
import pytest
from backend.config import get_settings
from backend.data_util.gbif.observations_request import build_observations_request

settings = get_settings()


# Using GBIF UAT credentials (if provided in env), make sure build_observations_request
# returns a well-formed body
@pytest.mark.asyncio
@pytest.mark.requires_external_api
@pytest.mark.skipif(
    not settings.gbif.uat_user or not settings.gbif.uat_password,
    reason="GBIF UAT credentials not configured"
)
async def test_observations_request_not_malformed():
    request_body = build_observations_request(
        settings.gbif.uat_user or '',
        settings.gbif.uat_email or ''
    )
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            'https://api.gbif-uat.org/v1/occurrence/download/request',
            data=json.dumps(request_body),
            auth=aiohttp.BasicAuth(
                settings.gbif.uat_user or '',
                settings.gbif.uat_password or ''
            ),
            headers={'Content-Type': 'application/json'}
        )
        assert response.status == 201
