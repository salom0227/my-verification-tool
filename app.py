import os
import sys
import asyncio
import subprocess
import random
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="SheerID Universal Hub")
templates = Jinja2Templates(directory=".")

# RASMDAGI BARCHA SERVISLAR VA ULARNING YO'LLARI
TOOLS = {
    "spotify": "spotify-verify-tool/main.py",
    "youtube": "youtube-verify-tool/main.py",
    "gemini": "one-verify-tool/main.py",
    "bolt": "boltnew-verify-tool/main.py",
    "k12": "k12-verify-tool/main.py",
    "veterans": "veterans-verify-tool/main.py"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run-bot")
async def run_bot(tool_type: str = Form(...), sheerid_url: str = Form(...)):
    if tool_type not in TOOLS:
        raise HTTPException(status_code=400, detail="Noma'lum servis")

    script_path = TOOLS[tool_type]
    
    # Skript mavjudligini tekshirish
    if not os.path.exists(script_path):
        async def error_gen():
            yield f"data: ❌ XATO: {script_path} topilmadi!\n\n".encode()
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    async def log_streamer():
        yield f"data: 🚀 [TIZIM] {tool_type.upper()} ISHGA TUSHIRILDI...\n\n".encode()
        
        # Skriptni subprocess orqali yurgizish
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path, sheerid_url,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        while True:
            line = await process.stdout.readline()
            if not line: break
            yield f"data: {line.decode()}\n\n".encode()
            await asyncio.sleep(0.05)

        await process.wait()
        yield f"data: ✅ [YAKUN] JARAYON TUGADI.\n\n".encode()

    return StreamingResponse(log_streamer(), media_type="text/event-stream")

@app.get("/api/generate-proof")
async def generate_proof(name: str = "Shahzod", surname: str = "Qalandarov"):
    """Canva uchun PNG hujjat yaratish"""
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "canva-teacher-tool"))
        from main import generate_employment_letter, DEFAULT_UK_SCHOOLS, TEACHING_POSITIONS
        
        school = random.choice(DEFAULT_UK_SCHOOLS)
        pos = random.choice(TEACHING_POSITIONS)
        file_path = generate_employment_letter(name, surname, school, pos)
        return FileResponse(path=file_path, filename=f"Proof_{name}.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
