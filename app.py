import os
import random
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from canva_teacher_tool.main import generate_employment_letter, DEFAULT_UK_SCHOOLS, TEACHING_POSITIONS, generate_name

app = FastAPI(title="SheerID Verification Tool")

@app.get("/")
def home():
    return {
        "status": "Online", 
        "message": "SheerID Verification API is running",
        "endpoints": {
            "generate_canva": "/generate/canva?name=Ali&surname=Vali"
        }
    }

@app.get("/generate/canva")
def make_canva_doc(name: str = None, surname: str = None):
    # Agar ism kiritilmasa, tasodifiy tanlaydi
    if not name or not surname:
        name, surname = generate_name()
        
    school = random.choice(DEFAULT_UK_SCHOOLS)
    position = random.choice(TEACHING_POSITIONS)
    
    try:
        # Hujjatni yaratish
        file_path = generate_employment_letter(name, surname, school, position)
        
        if "Error" in file_path:
            raise HTTPException(status_code=500, detail=file_path)
            
        # Faylni foydalanuvchiga yuborish
        return FileResponse(
            path=file_path, 
            filename=f"Canva_Proof_{name}_{surname}.png",
            media_type="image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Railway taqdim etadigan PORT orqali ishga tushadi
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
