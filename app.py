import os
import sys
import subprocess
import asyncio
import random
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Import yo'llarini tekshirish (Papka nomingizga qarab: canva_teacher_tool)
try:
    from canva_teacher_tool.main import generate_employment_letter, DEFAULT_UK_SCHOOLS, TEACHING_POSITIONS, generate_name
except ImportError:
    # Agar papka nomi chiziqcha bilan bo'lsa
    sys.path.append(os.path.join(os.path.dirname(__file__), "canva-teacher-tool"))
    from main import generate_employment_letter, DEFAULT_UK_SCHOOLS, TEACHING_POSITIONS, generate_name

app = FastAPI(title="SheerID Ultimate Dashboard")
templates = Jinja2Templates(directory=".")

TOOLS = {
    "spotify": "spotify-verify-tool/main.py",
    "youtube": "youtube-verify-tool/main.py",
    "canva": "canva-teacher-tool/main.py",
    "gemini": "one-verify-tool/main.py"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- 1. JONLI LOGLAR BILAN BOTNI ISHGA TUSHIRISH ---
@app.post("/run-bot")
async def run_bot(tool_type: str = Form(...), sheerid_url: str = Form(...)):
    if tool_type not in TOOLS:
        raise HTTPException(status_code=400, detail="Noma'lum servis")

    script_path = TOOLS[tool_type]
    
    async def event_generator():
        yield f"data: 🚀 [SYSTEM] {tool_type.upper()} FLOW INITIALIZED...\n\n".encode()
        
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
        yield f"data: ✅ [SUCCESS] OPERATION COMPLETED.\n\n".encode()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- 2. PROFESSIONAL HUJJAT GENERATORI ---
@app.get("/api/generate-proof")
async def generate_proof(name: str, surname: str):
    try:
        school = random.choice(DEFAULT_UK_SCHOOLS)
        pos = random.choice(TEACHING_POSITIONS)
        
        # PNG rasm yaratish
        file_path = generate_employment_letter(name, surname, school, pos)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Hujjat yaratishda xato")
            
        return FileResponse(path=file_path, filename=f"SheerID_Proof_{name}.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
