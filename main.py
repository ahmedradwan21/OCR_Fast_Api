from fastapi import FastAPI, UploadFile, File, HTTPException
import cv2
import numpy as np
import pytesseract
import re

app = FastAPI()

def extract_values_from_text(text):
    values = {}
    lines = text.split('\n')
    for line in lines:
        if 'Platelet' in line:
            platelet_value = re.search(r"\d+\.\d+", line)
            values['Platelet'] = float(platelet_value.group()) if platelet_value else None
        elif 'RBC' in line:
            rbc_value = re.search(r"\d+\.\d+", line)
            values['RBC'] = float(rbc_value.group()) if rbc_value else None
        elif 'WBC' in line:
            wbc_value = re.search(r"\d+\.\d+", line)
            values['WBC'] = float(wbc_value.group()) if wbc_value else None
        elif 'Hemoglobin' in line:
            hemoglobin_value = re.search(r"\d+\.\d+", line)
            values['Hemoglobin'] = float(hemoglobin_value.group()) if hemoglobin_value else None
    return values

def compare_values(values):
    platelet_min = 150
    platelet_max = 400
    rbc_min = 4.40
    rbc_max = 6.00
    wbc_min = 4.00
    wbc_max = 11.00
    hemoglobin_min = 13.5
    hemoglobin_max = 18.0
    
    result = "NORMAL" if (platelet_min <= values.get('Platelet', 0) <= platelet_max and
                          rbc_min <= values.get('RBC', 0) <= rbc_max and
                          wbc_min <= values.get('WBC', 0) <= wbc_max and
                          hemoglobin_min <= values.get('Hemoglobin', 0) <= hemoglobin_max) else "ABNORMAL"
    
    return result

async def process_image(image_data):
    try:
        nparr = np.frombuffer(image_data.read(), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)

        values = extract_values_from_text(text)
        result = compare_values(values)

        filtered_values = {'Hemoglobin': values.get('Hemoglobin')} if 'Hemoglobin' in values else {}

        return {'result': result, 'values': filtered_values}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/")
async def upload_file(image: UploadFile = File(...)):
    result = await process_image(image.file)
    return result
