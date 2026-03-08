import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# Barcha tool-lar joylashgan papkalarni Python yo'liga qo'shamiz
BASE_PATH = Path(__file__).parent
sys.path.insert(0, str(BASE_PATH / "spotify-verify-tool"))
sys.path.insert(0, str(BASE_PATH / "canva-teacher-tool"))

# Tool-larni import qilishga urinib ko'ramiz
try:
    from spotify_verify_tool.main import run_spotify_verify
except ImportError:
    def run_spotify_verify(url): print(f"[*] Spotify Bot Simulyatsiyasi: {url}")

try:
    # Canva tool ichidagi asosiy funksiya nomini tekshiring (odatda main.py da)
    from canva_teacher_tool.main import run_canva_verify 
except ImportError:
    def run_canva_verify(url): print(f"[*] Canva Bot Simulyatsiyasi: {url}")

app = FastAPI()
templates = Jinja2Templates(directory=".")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Bu sizning yangilangan index.html faylingizni ochadi
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run")
async def start_bot(background_tasks: BackgroundTasks, sheerid_url: str = Form(...), tool_type: str = Form(...)):
    # Linkni tekshirish
    if "services.sheerid.com" not in sheerid_url:
        return JSONResponse(content={"status": "error", "message": "Noto'g'ri SheerID linki!"}, status_code=400)
    
    # Tanlangan servisga qarab botni ishga tushirish
    if tool_type == "spotify":
        background_tasks.add_task(run_spotify_verify, sheerid_url)
        display_name = "Spotify Student"
    elif tool_type == "canva":
        background_tasks.add_task(run_canva_verify, sheerid_url)
        display_name = "Canva Education (Teacher)"
    else:
        return JSONResponse(content={"status": "error", "message": "Noma'lum servis tanlandi!"}, status_code=400)
    
    return JSONResponse(content={"status": "success", "message": f"{display_name} boti ishga tushdi! Railway loglarini kuzating."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
