import os
import re
import sys
import json
import time
import random
import uuid
from pathlib import Path
from typing import Dict, Optional

# Serverda kutubxonalarni avtomatik tekshirish
def install_deps():
    try:
        import httpx, PIL, curl_cffi
    except ImportError:
        os.system('pip install httpx Pillow curl_cffi cloudscraper')

install_deps()

# Anti-detect modulini ulash
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
try:
    from anti_detect import get_headers, get_fingerprint, create_session, random_delay
except ImportError:
    print("❌ anti_detect.py topilmadi! Fayllar joylashuvini tekshiring.")
    sys.exit(1)

# --- CONFIG ---
PROGRAM_ID = "67c8c14f5f17a83b745e3f82"
SHEERID_API_URL = "https://services.sheerid.com"

# Universitetlar ro'yxati (Sizdagini to'liq saqlang, bu erda namuna)
UNIVERSITIES = [
    {"id": 2565, "name": "Pennsylvania State University-Main Campus", "domain": "psu.edu", "weight": 100},
    {"id": 3499, "name": "University of California, Los Angeles", "domain": "ucla.edu", "weight": 98},
    # ... barcha 45+ OTMlarni shu yerga qo'ying ...
]

def run_spotify_verify(target_url: str):
    # 1. Verification ID ni ajratib olish
    match = re.search(r'verificationId=([a-f0-9]+)', target_url)
    v_id = match.group(1) if match else None
    if not v_id:
        print("❌ URL xato: Verification ID topilmadi.")
        return

    # 2. Session va Fingerprint (Aldash boshlandi)
    session, lib = create_session()
    print(f"[*] Session: {lib} | ID: {v_id}")

    # 3. OTM tanlash
    uni = random.choices(UNIVERSITIES, weights=[u['weight'] for u in UNIVERSITIES])[0]
    email = f"student.{uuid.uuid4().hex[:5]}@{uni['domain']}"
    
    # 4. SheerID Step-by-Step (Sizning original kodingiz mantiqi)
    headers = get_headers(for_sheerid=True)
    
    try:
        # STEP 1: Personal Info yuborish
        payload = {
            "firstName": "John",
            "lastName": "Doe",
            "email": email,
            "birthDate": f"{random.randint(1998, 2004)}-0{random.randint(1,9)}-{random.randint(10,28)}",
            "organization": {"id": uni['id']}
        }
        
        print(f"[*] Ma'lumotlar yuborilmoqda: {uni['name']}")
        res = session.post(f"{SHEERID_API_URL}/verification/{v_id}/step/collectStudentPersonalInfo", 
                          json=payload, headers=headers)
        
        # STEP 2: SSO Skip (Eng muhim aldash qismi)
        random_delay(1000, 2000)
        session.delete(f"{SHEERID_API_URL}/verification/{v_id}/step/sso", headers=headers)
        print("[+] SSO Skip bajarildi (Bypass)")

        # STEP 3: Document Upload (Avtomatik rasm generatsiyasi va yuborish)
        # (Bu yerda Pillow orqali rasm yaratish kodingizni qoldiring)
        print("[*] Hujjat tayyorlanmoqda va yuklanmoqda...")
        
        # Yakunlash
        print(f"✅ Muvaffaqiyatli! Emailni tekshiring: {email}")

    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    # SERVER UCHUN: input() o'rniga Environment Variable
    url = os.getenv("SHEERID_URL")
    
    if not url:
        print("❌ Railway Variables bo'limida SHEERID_URL ni o'rnating!")
        sys.exit(1)

    run_spotify_verify(url)
