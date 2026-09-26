from fastapi import FastAPI

from app.routes import register_quiz_errors, router as quiz_router
from app.ws import router as ws_router

app = FastAPI(title="Real-Time Vocabulary Quiz")
register_quiz_errors(app)
app.include_router(quiz_router)
app.include_router(ws_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
