#import uvicorn
from fastapi import FastAPI , Request
from fastapi.responses import JSONResponse
from routers import cvextract
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#app.include_router(cvextract)
app.include_router(cvextract.router, prefix="/cv", tags=["CV wynt"])

"""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

@app.middleware("http")
async def block_all_requests(request: Request, call_next):
    logger.info(f"Blocked request: {request.method} {request.url}")
    return JSONResponse(status_code=403, content={"detail": "Access forbidden"})