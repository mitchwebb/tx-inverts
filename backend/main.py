from contextlib import asynccontextmanager
from backend.core.exception_handler import global_exception_handler
from backend.core.logging import setup_logging
from fastapi import FastAPI
from backend.core.logging import api_logger
from backend.routers.occurrence import router as occurrence_router
from backend.routers.maps import router as maps_router
from backend.routers.taxa import router as taxa_router
from backend.routers.natureserve import router as natureserve_router
from backend.routers.downloads import router as downloads_router
from backend.config import get_settings
from psycopg_pool import AsyncConnectionPool
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables from .env
settings = get_settings()


# FastAPI new lifescycle management style
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup logic

    # Make database connection available to all routes (with dict_row factory)
    dsn = (
        f"dbname={settings.database.name} "
        f"user={settings.database.user} "
        f"password={settings.database.password} "
        f"host={settings.database.host} "
        f"port={settings.database.port}"
    )
    app.state.db_pool = AsyncConnectionPool(
        conninfo=dsn,
        min_size=5,
        max_size=30
    )
    # await app.state.db_pool.open()

    yield

    # Shutdown logic

    # Setup database connection close on shutdown
    if hasattr(app.state, "db_pool"):
        await app.state.db_pool.close()


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# TODO: Limit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors.domain],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(occurrence_router, prefix='/occurrence')
app.include_router(maps_router, prefix='/maps')
app.include_router(taxa_router, prefix='/taxa')
app.include_router(natureserve_router, prefix='/natureserve')
app.include_router(downloads_router, prefix='/downloads')

# Register exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Set up loggers
setup_logging()

api_logger.info("Started API logger...")

# Print routes (for debugging)
api_logger.debug("Routes:")
for route in app.routes:
    api_logger.debug(f"  {route.path} - {','.join(route.methods)}")
