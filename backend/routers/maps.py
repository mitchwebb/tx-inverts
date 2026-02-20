import json
from fastapi import APIRouter, Request
from backend.data_util.execute_psql_query import execute_psql_query


router = APIRouter()


# Get parks shapefile as GeoJSON
@router.get("/parks.geojson")
async def get_parks_geojson(request: Request):
    # ST_AsGeoJSON is a PostGIS function that converts geometry to GeoJSON format
    query = """
        SELECT id, name, ST_AsGeoJSON(geometry) AS geometry
        FROM state_parks
    """
    async with request.app.state.db_pool.connection() as conn:
        async with execute_psql_query(conn, request, query, fetch='all') as rows:
            columns = ['id', 'name', 'geometry']
            features = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                # already GeoJSON string
                geom_json = json.loads(row_dict.pop('geometry'))
                features.append({
                    "type": "Feature",
                    "geometry": geom_json,
                    "properties": row_dict
                })
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            return JSONResponse(content=geojson)
