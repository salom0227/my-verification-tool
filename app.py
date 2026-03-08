import os
import sys
import subprocess
import asyncio
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="SheerID Universal Bot")

# HTML shablonlari uchun (index.html ildizda)
templates = Jinja2Templates(directory=".")

# Toollar ro'yxati va ularning manzillari (Papka nomlarini tekshiring!)
TOOLS = {
    "spotify": "spotify-verify-tool/main.py",
    "youtube": "youtube-verify-tool/main.py",
    "canva": "canva-teacher-tool/main.py",
    "gemini": "one-verify-tool/main.py",
    "chatgpt": "k12-verify-tool/main.py"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run")
async def run_tool(tool_type: str = Form(...), sheerid_url: str = Form(...)):
    if tool_type not in TOOLS:
        raise HTTPException(status_code=400, detail="Noma'lum servis tanlandi")

    script_path = TOOLS[tool_type]
    
    # Skript mavjudligini tekshirish
    if not os.path.exists(script_path):
        return StreamingResponse(iter([f"❌ Xato: {script_path} topilmadi!".encode()]), media_type="text/plain")

    async def run_script():
        # Skriptni ishga tushirish va loglarni oqim (stream) ko'rinishida olish
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path, sheerid_url,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        yield f"🚀 {tool_type.upper()} jarayoni boshlandi...\n".encode()
        yield f"🔗 URL: {sheerid_url[:30]}...\n\n".encode()

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            # Har bir qatorni brauzerga darhol yuboramiz
            yield line
            await asyncio.sleep(0.1) # Serverni zo'riqtirmaslik uchun

        return_code = await process.wait()
        if return_code == 0:
            yield "\n✅ JARAYON MUVAFFAQIYATLI YAKUNLANDI!".encode()
        else:
            yield f"\n❌ XATO: Skript {return_code} kodi bilan to'xtadi.".encode()

    return StreamingResponse(run_script(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
