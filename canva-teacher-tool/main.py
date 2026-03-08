import os
import sys
import json
import random
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ Error: PyMuPDF required. Install: pip install pymupdf")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("❌ Error: Pillow required. Install: pip install Pillow")
    sys.exit(1)

# ============ CONFIG ============
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============ UK SCHOOLS DATABASE ============
DEFAULT_UK_SCHOOLS = [
    {"name": "Leeds Grammar School", "address": "Alwoodley Gates, Harrogate Road", "town": "Leeds", "postcode": "LS17 8GS", "phone": "0139 1219 502", "lea": "Leeds LEA"},
    {"name": "Manchester Grammar School", "address": "Old Hall Lane", "town": "Manchester", "postcode": "M13 0XT", "phone": "0161 224 7201", "lea": "Manchester LEA"},
    {"name": "Eton College", "address": "High Street", "town": "Windsor", "postcode": "SL4 6DW", "phone": "01753 370 100", "lea": "Windsor LEA"},
]

# ============ GENERATORS ============
UK_FIRST_NAMES = ["James", "Oliver", "Harry", "Emma", "Olivia", "Amelia"]
UK_LAST_NAMES = ["Smith", "Jones", "Williams", "Taylor", "Brown"]
TEACHING_POSITIONS = ["Head of Science", "Senior Teacher", "Class Teacher", "Year Group Leader"]

def generate_name(): return random.choice(UK_FIRST_NAMES), random.choice(UK_LAST_NAMES)
def generate_staff_id(): return f"STF-{random.randint(2020, 2025)}-{random.randint(100000, 999999)}"

# ============ DOCUMENT GENERATORS ============

def generate_employment_letter(first: str, last: str, school: Dict, position: str) -> str:
    """Employment Letter yaratish va PNG yo'lini qaytarish"""
    pdf_path = TEMPLATES_DIR / "Employment_Letter.pdf"
    if not pdf_path.exists(): return "Error: Template missing"
    
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    current_date = datetime.now().strftime("%d %B %Y")
    
    replacements = [
        ("Leeds Grammar School", school["name"]),
        ("Angela Ramirez", f"{first} {last}"),
        ("Head of Drama Department", position),
        ("07 January 2026", current_date)
    ]
    
    for old_text, new_text in replacements:
        areas = page.search_for(old_text)
        for rect in areas:
            page.add_redact_annot(rect, fill=(1, 1, 1))
    
    page.apply_redactions()
    
    # PNG sifatida saqlash
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    out_file = OUTPUT_DIR / f"letter_{first}_{last}.png"
    pix.save(str(out_file))
    doc.close()
    return str(out_file)

def generate_teacher_id_card(first: str, last: str, school: Dict, position: str) -> str:
    """Teacher ID Card yaratish va PNG yo'lini qaytarish"""
    pdf_path = TEMPLATES_DIR / "Teacher_ID_Card.pdf"
    if not pdf_path.exists(): return "Error: Template missing"
    
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    replacements = [
        ("LEEDS GRAMMAR SCHOOL", school["name"].upper()),
        ("ANGELA RAMIREZ", f"{first.upper()} {last.upper()}"),
        ("HEAD OF DRAMA", position.upper())
    ]
    
    for old_text, new_text in replacements:
        areas = page.search_for(old_text)
        for rect in areas:
            page.add_redact_annot(rect, fill=(1, 1, 1))
    
    page.apply_redactions()
    
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    out_file = OUTPUT_DIR / f"id_card_{first}_{last}.png"
    pix.save(str(out_file))
    doc.close()
    return str(out_file)

if __name__ == "__main__":
    # Test qilish uchun
    f, l = generate_name()
    sch = random.choice(DEFAULT_UK_SCHOOLS)
    pos = random.choice(TEACHING_POSITIONS)
    print(f"Yaratilmoqda: {generate_employment_letter(f, l, sch, pos)}")
