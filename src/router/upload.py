# SAMPLE

# @app.post("/upload-audio")
# async def upload_audio(file: UploadFile = File(...)):
    
#     # generate unique filename
#     file_id = str(uuid4())
#     filename = f"{file_id}_{file.filename}"

#     file_path = os.path.join(UPLOAD_DIR, filename)

#     # save file
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     return {
#         "message": "Upload success",
#         "filename": filename,
#         "path": file_path
#     }