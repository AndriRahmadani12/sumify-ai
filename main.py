from fastapi import FastAPI

app = FastAPI(title="Sumify AI")


@app.get("/")
async def root():
    return {"message": "Hello Iam Sumify AI"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
