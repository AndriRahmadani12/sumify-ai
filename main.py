from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.router import (
    meetings,
    pdf_generator,
    pdf_templates,
    summary,
    transcribe,
    upload,
)

app = FastAPI(title="Sumify AI")

# Izinkan frontend memanggil API dari origin lain.
# Untuk produksi, ganti allow_origins dengan daftar domain yang spesifik.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kontrak API untuk aplikasi Android (sumify-ai-fe)
app.include_router(meetings.router)

# Endpoint per tahap, dipakai untuk pengujian dan pemakaian manual
app.include_router(upload.router)
app.include_router(transcribe.router)
app.include_router(summary.router)
app.include_router(pdf_templates.router)
app.include_router(pdf_generator.router)


@app.get("/")
async def root():
    return {"message": "Hello Iam Sumify AI"}


if __name__ == "__main__":
    import uvicorn

    # proxy_headers + forwarded_allow_ips diperlukan saat backend diakses
    # lewat tunnel (Cloudflare, ngrok). Tanpa itu, URL yang dibangun server
    # memakai skema http meski pengguna mengaksesnya lewat https.
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
