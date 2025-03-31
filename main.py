from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import zipfile
import os
import csv
from llm import get_llm_response  # Importing the LLM function

app = FastAPI()

@app.post("/api/")
async def process_question(
    question: str = Form(...),
    file: UploadFile = File(None)
):
    """
    API endpoint to process a question and an optional file.
    """
    try:
        file_content = None  # Default to None if no file is uploaded

        if file:
            temp_zip_path = f"/tmp/{file.filename}"
            with open(temp_zip_path, "wb") as temp_file:
                temp_file.write(await file.read())

            # Extract the zip file
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall("/tmp/extracted_files")

            # Find and read the CSV file
            extracted_files = os.listdir("/tmp/extracted_files")
            csv_file_path = None
            for f in extracted_files:
                if f.endswith(".csv"):
                    csv_file_path = f"/tmp/extracted_files/{f}"
                    break

            if not csv_file_path:
                raise HTTPException(status_code=400, detail="No CSV file found in the uploaded ZIP.")

            # Read CSV content
            with open(csv_file_path, mode="r") as csvfile:
                reader = csv.DictReader(csvfile)
                file_content = "\n".join([str(row) for row in reader])  # Convert rows to text

            os.remove(temp_zip_path)  # Clean up
            os.remove(csv_file_path)

        # Get answer from LLM
        response = get_llm_response(question, file_content)
        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
