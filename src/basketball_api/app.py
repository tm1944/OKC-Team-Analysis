from fastapi import FastAPI

app = FastAPI(
    title="Basketball Decision Support API",
    version="0.1.0",
    description="Grounded player analysis from NBA data, a shot model, and retrieval.",
)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}
