from fastapi import FastAPI

app = FastAPI(title="Real-Time Vocabulary Quiz")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
