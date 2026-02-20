from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging


logger = logging.getLogger("api_logger")


class TaxonNotFoundError(Exception):
    pass


class InvalidTaxonRankError(Exception):
    pass


async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={'detail': exc.detail}
        )

    if isinstance(exc, TaxonNotFoundError):
        return JSONResponse(
            status_code=404,
            content={'detail': str(exc)}
        )

    if isinstance(exc, InvalidTaxonRankError):
        return JSONResponse(
            status_code=400,
            content={'detail': str(exc)}
        )

    logger.exception("Unhandled exception", exc_info=exc)

    return JSONResponse(
        status_code=500,
        content={'detail': 'Internal server error'}
    )
