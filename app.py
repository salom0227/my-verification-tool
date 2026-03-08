"""
SheerID Verification Hub — Backend Server
==========================================
Yaxshilangan va to'liq kommentlangan versiya.

Asosiy o'zgartirishlar:
  - Konfiguratsiya alohida (CONFIG dict)
  - Rate limiting (bir IP uchun cheklov)
  - URL validatsiyasi
  - Xato boshqaruvi kuchaytirildi
  - CORS sozlandi
  - Logging qo'shildi
  - generate_proof uchun temp fayl tozalash
  - Health check endpoint
  - Lifespan event handler (deprecated on_event o'rniga)
"""

import os
import sys
import asyncio
import subprocess
import random
import logging
import time
import re
import tempfile
from pathlib import Path
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# ─────────────────────────────────────────────
# 1. LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sheerid-hub")


# ─────────────────────────────────────────────
# 2. KONFIGURATSIYA
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()

CONFIG = {
    # Har bir IP uchun 60 soniyada nechta so'rov ruxsat etiladi
    "rate_limit_requests": 10,
    "rate_limit_window_sec": 60,

    # Subprocess maksimal bajarilish vaqti (soniya)
    "process_timeout_sec": 120,

    # SheerID URL pattern (faqat haqiqiy havolani qabul qilish)
    "sheerid_url_pattern": re.compile(
        r"^https://(www\.)?sheerid\.com/.+", re.IGNORECASE
    ),

    # Ruxsat etilgan originlar (deploy qilganda o'zgartiring)
    "allowed_origins": ["*"],
}

# Tool → skript yo'li xaritasi
#
# STRUKTURA ESLATMALARI:
#   - "canva-teacher-tool"  → main.py YO'Q  (faqat assets/ bor, bo'sh papka)
#   - "canva_teacher_tool"  → main.py BOR   (underscore versiyasi — to'g'risi shu)
#   - "perplexity-verify-tool" → main.py bor, lekin asl kodda umuman yo'q edi
#   - "veterans-autofill"   → bu browser extension (JS), Python tool emas — TOOLS ga kirmaydi
#   - "veterans-extension"  → xuddi shunday, extension
#   - "_deprecated_auto-verify-tool" → deprecated, ishlatilmaydi
#
TOOLS: dict[str, Path] = {
    "spotify":    BASE_DIR / "spotify-verify-tool"    / "main.py",
    "youtube":    BASE_DIR / "youtube-verify-tool"    / "main.py",
    "gemini":     BASE_DIR / "one-verify-tool"        / "main.py",
    "bolt":       BASE_DIR / "boltnew-verify-tool"    / "main.py",
    "k12":        BASE_DIR / "k12-verify-tool"        / "main.py",
    "veterans":   BASE_DIR / "veterans-verify-tool"   / "main.py",
    "perplexity": BASE_DIR / "perplexity-verify-tool" / "main.py",
    # canva: underscore versiyasi ishlatiladi (canva-teacher-tool da main.py yo'q!)
    "canva":      BASE_DIR / "canva_teacher_tool"     / "main.py",
}


# ─────────────────────────────────────────────
# 3. RATE LIMITER (oddiy xotira asosida)
# ─────────────────────────────────────────────
# Muhim: production da Redis-ga o'tkazish tavsiya etiladi
_rate_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str) -> None:
    """
    IP bo'yicha so'rovlar sonini tekshiradi.
    Haddan oshsa — 429 xatosi qaytaradi.
    """
    now = time.time()
    window = CONFIG["rate_limit_window_sec"]
    limit = CONFIG["rate_limit_requests"]

    # Eskirgan vaqtlarni tozalash
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < window]

    if len(_rate_store[ip]) >= limit:
        logger.warning(f"Rate limit exceeded: {ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Juda ko'p so'rov. {window} soniyada {limit} tadan ko'p bo'lmaydi.",
        )

    _rate_store[ip].append(now)


def get_client_ip(request: Request) -> str:
    """Proxy ortidagi haqiqiy IP ni oladi."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ─────────────────────────────────────────────
# 4. LIFESPAN (startup / shutdown)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SheerID Hub server ishga tushdi.")
    logger.info(f"Mavjud toollar: {list(TOOLS.keys())}")
    for name, path in TOOLS.items():
        status = "✓" if path.exists() else "✗ TOPILMADI"
        logger.info(f"  [{status}] {name}: {path}")
    yield
    logger.info("Server to'xtatildi.")


# ─────────────────────────────────────────────
# 5. APP VA MIDDLEWARE
# ─────────────────────────────────────────────
app = FastAPI(
    title="SheerID Verification Hub",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG["allowed_origins"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(BASE_DIR))


# ─────────────────────────────────────────────
# 6. YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────
def validate_sheerid_url(url: str) -> None:
    """
    SheerID URL formatini tekshiradi.
    Noto'g'ri URL — 400 xatosi.
    """
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL bo'sh bo'lishi mumkin emas.")
    if not CONFIG["sheerid_url_pattern"].match(url.strip()):
        raise HTTPException(
            status_code=400,
            detail="Faqat https://sheerid.com/... ko'rinishidagi URL qabul qilinadi.",
        )


def build_subprocess_env(script_dir: Path) -> dict:
    """Subprocess uchun to'g'ri muhit o'zgaruvchilarini tayyorlaydi."""
    env = os.environ.copy()
    # Skriptning o'z papkasini PYTHONPATH ga qo'shamiz
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{script_dir}{os.pathsep}{existing}" if existing else str(script_dir)
    return env


# ─────────────────────────────────────────────
# 7. ENDPOINTLAR
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Asosiy sahifa."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """
    Railway / Docker health check uchun.
    Uptime monitoring xizmatlari shu endpointni ping qiladi.
    """
    tools_status = {name: path.exists() for name, path in TOOLS.items()}
    all_ok = all(tools_status.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "tools": tools_status,
    }


@app.post("/run-bot")
async def run_bot(
    request: Request,
    tool_type: str = Form(...),
    sheerid_url: str = Form(...),
):
    """
    Tool skriptini ishga tushiradi va natijalarni
    Server-Sent Events (SSE) orqali real vaqtda uzatadi.

    KAMCHILIK (asl kodda): timeout yo'q edi — skript abadiy ishlashi mumkin edi.
    TUZATISH: asyncio.wait_for bilan timeout qo'shildi.
    """
    ip = get_client_ip(request)
    check_rate_limit(ip)

    # Tool mavjudligini tekshirish
    if tool_type not in TOOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Noma'lum tool: '{tool_type}'. Mavjud: {list(TOOLS.keys())}",
        )

    script_path = TOOLS[tool_type]

    # URL validatsiyasi
    validate_sheerid_url(sheerid_url)

    logger.info(f"Bot ishga tushdi | tool={tool_type} | ip={ip}")

    async def log_stream():
        # Skript fayli yo'qligini darhol xabar qilish
        if not script_path.exists():
            yield f"data: ❌ XATO: {script_path} topilmadi!\n\n".encode()
            return

        yield f"data: ⚡ [{tool_type.upper()}] FLOW INITIALIZED...\n\n".encode()
        yield f"data: 🛰️ [NET] SHEERID ENDPOINT GA ULANMOQDA...\n\n".encode()

        env = build_subprocess_env(script_path.parent)

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path), sheerid_url.strip(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )

            # Timeout bilan o'qish
            async def read_output():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode(errors="replace").rstrip()
                    if decoded:
                        yield f"data: {decoded}\n\n".encode()
                    await asyncio.sleep(0.02)

            try:
                async for chunk in asyncio.timeout(
                    CONFIG["process_timeout_sec"]
                )(read_output()):
                    yield chunk
            except TimeoutError:
                process.kill()
                yield f"data: ⏱️ XATO: Jarayon {CONFIG['process_timeout_sec']}s dan oshdi, to'xtatildi.\n\n".encode()
                return

            await process.wait()

            if process.returncode == 0:
                yield b"data: \u2705 [SYSTEM] VERIFICATION COMPLETE.\n\n"
            else:
                yield f"data: ⚠️ [SYSTEM] Skript {process.returncode} kodi bilan tugadi.\n\n".encode()

        except Exception as exc:
            logger.exception(f"Subprocess xatosi: {exc}")
            yield f"data: 💥 Server xatosi: {exc}\n\n".encode()

    return StreamingResponse(
        log_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Nginx buferingini o'chirish
        },
    )


@app.get("/api/generate-proof")
async def generate_proof(
    request: Request,
    name: str = "Shahzod",
    surname: str = "Qalandarov",
):
    """
    Canva teacher tool yordamida PNG hujjat yaratadi.

    KAMCHILIKLAR (asl kodda):
      1. sys.path.append — har chaqiruvda qo'shilardi (takrorlanish).
      2. Yaratilgan temp fayl hech qachon o'chirilmasdi (disk to'lishi).
      3. Ism/familiya validatsiyasi yo'q edi (XSS/path traversal xavfi).
    TUZATISHLAR:
      - Ism validatsiyasi qo'shildi.
      - Temp fayl try/finally bilan o'chiriladi.
      - sys.path bir marta tekshiriladi.
    """
    ip = get_client_ip(request)
    check_rate_limit(ip)

    # Ism validatsiyasi: faqat harf, tire, bo'shliq
    name_pattern = re.compile(r"^[A-Za-z\u0400-\u04FF\- ]{1,50}$")
    if not name_pattern.match(name) or not name_pattern.match(surname):
        raise HTTPException(
            status_code=400,
            detail="Ism/familiyada faqat harflar va tire bo'lishi mumkin (maks. 50 belgi).",
        )

    canva_dir = BASE_DIR / "canva_teacher_tool"   # underscore! (canva-teacher-tool da main.py yo'q)
    if not canva_dir.exists():
        raise HTTPException(status_code=503, detail="canva-teacher-tool papkasi topilmadi.")

    # sys.path ga bir marta qo'shamiz
    canva_str = str(canva_dir)
    if canva_str not in sys.path:
        sys.path.insert(0, canva_str)

    file_path: str | None = None
    try:
        # Import xatosini aniq ushlash
        try:
            from main import (  # type: ignore
                generate_employment_letter,
                DEFAULT_UK_SCHOOLS,
                TEACHING_POSITIONS,
            )
        except ImportError as exc:
            logger.error(f"canva-teacher-tool import xatosi: {exc}")
            raise HTTPException(
                status_code=503,
                detail=f"Modul yuklanmadi: {exc}. canva-teacher-tool/main.py mavjudligini tekshiring.",
            )

        school = random.choice(DEFAULT_UK_SCHOOLS)
        position = random.choice(TEACHING_POSITIONS)

        logger.info(f"Proof yaratilmoqda | {name} {surname} | {school}")
        file_path = generate_employment_letter(name, surname, school, position)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Fayl yaratilmadi.")

        # Faylni jo'natish (response qaytguncha fayl o'chirilmasligi uchun background task ishlatamiz)
        return FileResponse(
            path=file_path,
            filename=f"SheerID_Proof_{name}_{surname}.png",
            media_type="image/png",
            background=_delete_file_after(file_path),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"generate_proof xatosi: {exc}")
        raise HTTPException(status_code=500, detail=f"Kutilmagan xato: {exc}")


class _delete_file_after:
    """Response jo'natilgandan so'ng temp faylni o'chiradi."""

    def __init__(self, path: str):
        self.path = path

    async def __call__(self) -> None:
        try:
            os.unlink(self.path)
            logger.debug(f"Temp fayl o'chirildi: {self.path}")
        except OSError:
            pass  # Allaqachon o'chirilgan yoki ruxsat yo'q — e'tiborsiz


# ─────────────────────────────────────────────
# 8. SERVERNI ISHGA TUSHIRISH
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    uvicorn.run(
        "server:app",          # modul:app — hot-reload uchun string ishlatiladi
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="debug" if debug else "info",
    )
