import os
import sys
import asyncio
import subprocess
import random
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# --- 1. YO'LLARNI TO'G'RILASH (Import muammosini yechish) ---
current_dir = os.path.dirname(os.path.abspath(__file__))

# canva-teacher-tool papkasini tizim yo'liga qo'shamiz
canva_repo = os.path.join(current_dir, "canva-teacher-tool")
if os.path.exists(canva_repo) and canva_repo not in sys.path:
    sys.path.append(canva_repo)

try:
    # Asosiy funksiyalarni import qilish
    from main import generate_employment_letter, DEFAULT_UK_SCHOOLS, TEACHING_POSITIONS, generate_name
except ImportError:
    try:
        from canva_teacher_tool.main import generate_employment_letter, DEFAULT_UK_SCHOOLS, TEACHING_POSITIONS, generate_name
    except ImportError:
        print("❌ ERROR: canva-teacher-tool moduli topilmadi!")

# --- 2. FASTAPI SOZLAMALARI ---
app = FastAPI(title="SheerID Ultimate Hub")
templates = Jinja2Templates(directory=".")

# Bot skriptlari ro'yxati
TOOLS = {
    "spotify": "spotify-verify-tool/main.py",
    "youtube": "youtube-verify-tool/main.py",
    "canva": "canva-teacher-tool/main.py",
    "gemini": "one-verify-tool/main.py",
    "chatgpt": "k12-verify-tool/main.py"
}

# --- 3. ENDPOINTLAR ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Asosiy sahifani (Frontend) ko'rsatish"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run-bot")
async def run_bot(tool_type: str = Form(...), sheerid_url: str = Form(...)):
    """SheerID Botini ishga tushirish (Terminal uchun oqim)"""
    if tool_type not in TOOLS:
        raise HTTPException(status_code=400, detail="Noma'lum servis")

    script_path = TOOLS[tool_type]

    async def log_generator():
        yield f"data: ⚡ [KERNEL] INITIALIZING {tool_type.upper()} FLOW...\n\n".encode()

        # Subprocess orqali skriptni ishga tushirish
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path, sheerid_url,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        while True:
            line = await process.stdout.readline()
            if not line: break
            # Har bir qatorni terminalga yuborish
            yield f"data: {line.decode()}\n\n".encode()
            await asyncio.sleep(0.05)

        await process.wait()
        yield f"data: ✅ [SYSTEM] OPERATION COMPLETED SUCCESSFULLY.\n\n".encode()

    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/generate-proof")
async def generate_proof(name: str, surname: str):
    """Shahzod Qalandarov uchun Canva hujjatini (PNG) yaratish"""
    try:
        # Tasodifiy maktab va lavozim
        school = random.choice(DEFAULT_UK_SCHOOLS)
        position = random.choice(TEACHING_POSITIONS)

        # Hujjatni yaratish (PNG rasm qaytaradi)
        file_path = generate_employment_letter(name, surname, school, position)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Fayl generatsiya qilinmadi")

        return FileResponse(
            path=file_path,
            filename=f"Canva_Verification_{name}_{surname}.png",
            media_type="image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xatolik: {str(e)}")

# --- 4. SERVERNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    import uvicorn
    # Railway PORT'ini aniqlash
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
