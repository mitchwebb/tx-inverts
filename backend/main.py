from starlette import routing
from contextlib import asynccontextmanager

from fastapi.exceptions import RequestValidationError
from backend.core.exception_handler import global_exception_handler, validation_error_handler
from backend.core.logging import setup_logging
from fastapi import FastAPI
from backend.core.logging import api_logger
from backend.routers.occurrence_router import occurrence_router
from backend.routers.taxa_router import taxa_router
from backend.routers.rankings_router import rankings_router
from backend.routers.downloads_router import downloads_router
from backend.routers.regions_router import regions_router
from backend.config import get_settings
from psycopg_pool import AsyncConnectionPool
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables from .env
settings = get_settings()

# Set up loggers
setup_logging()
api_logger.info("Started API logger...")


# FastAPI new lifescycle management style
@asynccontextmanager
async def lifespan(app: FastAPI):
    api_logger.info("Opening DB pool...")
    # Startup logic
    # Make database connection available to all routes (with dict_row factory)
    dsn = (
        f'dbname={settings.database.name} '
        f'user={settings.database.user} '
        f'password={settings.database.password} '
        f'host={settings.database.host} '
        f'port={settings.database.port}'
    )

    app.state.db_pool = AsyncConnectionPool(
        conninfo=dsn,
        min_size=5,
        max_size=30,
        open=False
    )
    await app.state.db_pool.open(wait=True)
    api_logger.info("DB pool opened successfully")

    yield

    # Shutdown logic

    # Setup database connection close on shutdown
    if hasattr(app.state, 'db_pool'):
        await app.state.db_pool.close()


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# TODO: Limit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors.domain],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Add routers
app.include_router(occurrence_router, prefix='/occurrence')
app.include_router(taxa_router, prefix='/taxa')
app.include_router(rankings_router, prefix='/rankings')
app.include_router(downloads_router, prefix='/downloads')
app.include_router(regions_router, prefix='/regions')

# Register exception handler
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


# Print routes (for startup debugging)
api_logger.debug("Routes:")
for route in app.routes:
    if isinstance(route, routing.Route):
        api_logger.debug(
            f"  {route.path} - {','.join(route.methods if route.methods is not None else set())}")
