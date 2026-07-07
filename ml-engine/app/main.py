from fastapi import FastAPI

app = FastAPI(title="TerraPulse ML Engine")


@app.get("/")
def root():
    return {"status": "healthy"}


@app.get("/health")
def health():
    return {"status": "healthy"}
