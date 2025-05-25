from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional
from PIL import Image
import pytesseract
import pandas as pd
import shutil
import os
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Table

app = FastAPI()

def extract_from_image(file_path):
    image = Image.open(file_path).convert("L")
    text = pytesseract.image_to_string(image, lang="eng")
    return {"text": text, "tables": []}

def extract_from_pdf(file_path):
    elements = partition_pdf(filename=file_path, strategy="hi_res")
    text = " ".join([el.text for el in elements if hasattr(el, "text")])
    tables = [el.text for el in elements if isinstance(el, Table)]
    return {"text": text, "tables": tables}

def extract_from_web(url):
    tables = pd.read_html(url)
    return {"text": "", "tables": [table.to_dict() for table in tables]}

@app.post("/extract/")
async def extract_data(
    source_type: str = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    try:
        if source_type in ["image", "pdf"]:
            if not file:
                return JSONResponse(status_code=400, content={"error": "File is required for image/pdf"})
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            if source_type == "image":
                result = extract_from_image(temp_path)
            else:
                result = extract_from_pdf(temp_path)

            os.remove(temp_path)
            return result

        elif source_type == "web":
            if not url:
                return JSONResponse(status_code=400, content={"error": "URL is required for web source"})
            result = extract_from_web(url)
            return result

        else:
            return JSONResponse(status_code=400, content={"error": "Invalid source_type. Must be 'image', 'pdf', or 'web'"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
