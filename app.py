import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# Bot yo'lini kiritamiz
sys.path.insert(0, str(Path(__file__).parent / "spotify-verify-tool"))
try:
    from main import run_spotify_verify
except ImportError:
    def run_spotify_verify(url): print(f"Bot started for: {url}")

app = FastAPI()
templates = Jinja2Templates(directory=".")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run")
async def start_bot(background_tasks: BackgroundTasks, sheerid_url: str = Form(...)):
    if "services.sheerid.com" not in sheerid_url:
        return JSONResponse(content={"status": "error", "message": "Noto'g'ri SheerID linki!"}, status_code=400)
    
    # Bot orqa fonda ishga tushadi
    background_tasks.add_task(run_spotify_verify, sheerid_url)
    
    return JSONResponse(content={"status": "success", "message": "Bot ishga tushdi! Railway loglarini kuzating."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
