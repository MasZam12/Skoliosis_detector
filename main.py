from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/results", StaticFiles(directory="results"), name="results")

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = 'uploads/'
RESULT_FOLDER = 'results/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def hitung_kemiringan(point1, point2):
    delta_x = point2[0] - point1[0]
    delta_y = point2[1] - point1[1]
    angle = np.arctan2(delta_y, delta_x) * (180.0 / np.pi)
    return angle

def diagnosa_skoliosis(angle):
    if abs(angle) < 10:
        return "Normal"
    elif 10 <= abs(angle) <= 25:
        return "Skoliosis Ringan"
    else:
        return "Skoliosis Berat"

def buat_histogram(image, filename):
    histogram, bins = np.histogram(image.flatten(), bins=256, range=[0, 256])
    plt.figure()
    plt.title("Histogram")
    plt.xlabel("Pixel Intensity")
    plt.ylabel("Frequency")
    plt.plot(histogram, color='black')
    plt.xlim([0, 256])
    plt.grid()

    histogram_filename = f"histogram_{filename}.png"
    histogram_path = os.path.join(RESULT_FOLDER, histogram_filename)
    plt.savefig(histogram_path)
    plt.close()
    return histogram_filename

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/deteksi", response_class=HTMLResponse)
async def deteksi(request: Request):
    return templates.TemplateResponse("deteksi.html", {"request": request})

@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a JPG or PNG image.")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise HTTPException(status_code=400, detail="Failed to read image.")

    try:
        # Generate and save histogram
        histogram_filename = buat_histogram(img, file.filename)

        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        blurred_filename = f"blurred_{file.filename}"
        blurred_path = os.path.join(RESULT_FOLDER, blurred_filename)
        cv2.imwrite(blurred_path, blurred)

        equalized = cv2.equalizeHist(blurred)
        equalized_filename = f"equalized_{file.filename}"
        equalized_path = os.path.join(RESULT_FOLDER, equalized_filename)
        cv2.imwrite(equalized_path, equalized)

        edges = cv2.Canny(equalized, 50, 150)
        edges_filename = f"edges_{file.filename}"
        edges_path = os.path.join(RESULT_FOLDER, edges_filename)
        cv2.imwrite(edges_path, edges)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            spine_contour = max(contours, key=cv2.contourArea)
            top_point = tuple(spine_contour[spine_contour[:, :, 1].argmin()][0])
            bottom_point = tuple(spine_contour[spine_contour[:, :, 1].argmax()][0])
            angle = hitung_kemiringan(top_point, bottom_point)
            diagnosis = diagnosa_skoliosis(angle)

            img_result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            cv2.line(img_result, top_point, bottom_point, (0, 255, 0), 2)
            cv2.drawContours(img_result, [spine_contour], -1, (255, 0, 0), 2)

            result_filename = f"result_{file.filename}"
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            cv2.imwrite(result_path, img_result)

            return {
                "histogram_url": f"/results/{histogram_filename}",
                "blurred_url": f"/results/{blurred_filename}",
                "equalized_url": f"/results/{equalized_filename}",
                "edges_url": f"/results/{edges_filename}",
                "result_url": f"/results/{result_filename}",
                "diagnosis": diagnosis,
                "angle": angle
            }
        else:
            raise HTTPException(status_code=400, detail="Kontur tulang belakang tidak ditemukan.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
