import logging

from fastapi import FastAPI

from app.routes import register_quiz_errors, router as quiz_router
from app.ws import router as ws_router


def configure_logging() -> None:
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


configure_logging()

app = FastAPI(title="Real-Time Vocabulary Quiz")
register_quiz_errors(app)
app.include_router(quiz_router)
app.include_router(ws_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
