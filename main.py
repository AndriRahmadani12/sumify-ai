from fastapi import FastAPI

from src.router import transcribe

app = FastAPI(title="Sumify AI")

# Register routers
# app.include_router(transcribe.router)


@app.get("/")
async def root():
    return {"message": "Hello Iam Sumify AI"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
