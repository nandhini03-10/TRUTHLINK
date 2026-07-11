from fastapi import FastAPI
from .api.routes import router

app = FastAPI(
    title="TruthLink Rumor Verification Engine",
    description="A prototype engine that verifies claims using verified stakeholders and official evidence.",
    version="0.1.0",
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "truthlink"}
