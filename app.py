from fastapi import FastAPI

app = FastAPI(
    title="Product Image AI",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "project": "Product Image AI",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }