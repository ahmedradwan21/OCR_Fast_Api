from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
import re
import easyocr

app = FastAPI()
reader = easyocr.Reader(['en'])

def extract_values_from_text(text):
    values = {}
    lines = text.split('\n')
    for line in lines:
        if 'Platelet' in line:
            platelet_value = re.search(r"\d+\.\d+", line)
            values['Platelet'] = platelet_value.group() if platelet_value else None
        elif 'RBC' in line:
            rbc_value = re.search(r"\d+\.\d+", line)
            values['RBC'] = rbc_value.group() if rbc_value else None
        elif 'WBC' in line:
            wbc_value = re.search(r"\d+\.\d+", line)
            values['WBC'] = wbc_value.group() if wbc_value else None
        elif 'Hemoglobin' in line:
            hemoglobin_value = re.search(r"\d+\.\d+", line)
            values['Hemoglobin'] = hemoglobin_value.group() if hemoglobin_value else None
    return values

def build_model_and_predict(values):
    platelet_min = 150
    platelet_max = 400
    rbc_min = 4.40
    rbc_max = 6.00
    wbc_min = 4.00
    wbc_max = 11.00
    hemoglobin_min = 13.5
    hemoglobin_max = 18.0

    platelet = float(values.get('Platelet', 0)) if values.get('Platelet') is not None else 0
    rbc = float(values.get('RBC', 0)) if values.get('RBC') is not None else 0
    wbc = float(values.get('WBC', 0)) if values.get('WBC') is not None else 0
    hemoglobin = float(values.get('Hemoglobin', 0)) if values.get('Hemoglobin') is not None else 0

    result = "NORMAL" if (platelet_min <= platelet <= platelet_max and
                           rbc_min <= rbc <= rbc_max and
                           wbc_min <= wbc <= wbc_max and
                           hemoglobin_min <= hemoglobin <= hemoglobin_max) else "ABNORMAL"

    if result == "NORMAL":
        return "NORMAL", hemoglobin

    return result, None

async def process_image(image_data):
    try:
        nparr = np.frombuffer(image_data.read(), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

        result = reader.readtext(image, detail=0, paragraph=True)
        text = "\n".join(result)

        values = extract_values_from_text(text)

        result, hemoglobin_value = build_model_and_predict(values)
        return result, hemoglobin_value
    except Exception as e:
        return "An error occurred: " + str(e), None

@app.post("/")
async def upload_image(image: UploadFile = File(...)):
    result, hemoglobin_value = await process_image(image.file)
    if hemoglobin_value is not None:
        return {'result': result, 'Hemoglobin': hemoglobin_value}
    else:
        return {'result': result}
