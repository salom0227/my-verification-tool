from fpdf import FPDF
import os

# Papkalarni yaratish
paths = [
    "canva-teacher-tool/assets/templates",
    "canva_teacher_tool/assets/templates", # Ikkala variant uchun ham
    "canva-teacher-tool/output",
    "canva_teacher_tool/output"
]

for path in paths:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"✅ Papka tayyor: {path}")

def create_pdf(save_dir, filename, title):
    pdf = FPDF()
    pdf.add_page()
    
    # Header - Maktab logosi o'rniga matn
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(0, 51, 102) # To'q ko'k rang
    pdf.cell(200, 15, txt="LEEDS GRAMMAR SCHOOL", ln=True, align='C')
    
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(200, 5, txt="Alwoodley Gates, Harrogate Road, Leeds LS17 8GS", ln=True, align='C')
    pdf.cell(200, 5, txt="Tel: +44 113 229 1552 | Web: www.gsal.org.uk", ln=True, align='C')
    
    pdf.ln(15)
    pdf.set_draw_color(0, 51, 102)
    pdf.line(10, 50, 200, 50) # Gorizontal chiziq
    
    # Hujjat turi
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=f"DOCUMENT: {title}", ln=True, align='L')
    
    # Sana
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Date: 07 January 2026", ln=True, align='R')
    
    # Asosiy matn
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    text = (
        "To Whom It May Concern,\n\n"
        "This official letter serves to confirm that Angela Ramirez is currently employed "
        "as a full-time professional educator at Leeds Grammar School.\n\n"
        "Position: Head of Drama Department\n"
        "Employment Status: Permanent / Active\n"
        "Faculty Member ID: STF-2024-881922\n\n"
        "We can confirm that she is a valued member of our academic staff and is "
        "eligible for all professional educator benefits and resources."
    )
    pdf.multi_cell(0, 8, txt=text)
    
    # Imzo qismi
    pdf.ln(25)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="__________________________", ln=True)
    pdf.cell(200, 8, txt="Dr. S. Evans", ln=True)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 5, txt="Headmaster of Leeds Grammar School", ln=True)
    
    # Faylni saqlash
    full_path = os.path.join(save_dir, filename)
    pdf.output(full_path)
    print(f"📄 Yaratildi: {full_path}")

# Fayllarni generatsiya qilish
for p in ["canva-teacher-tool/assets/templates", "canva_teacher_tool/assets/templates"]:
    if os.path.exists(p):
        create_pdf(p, "Employment_Letter.pdf", "EMPLOYMENT VERIFICATION")
        create_pdf(p, "Teacher_ID_Card.pdf", "OFFICIAL STAFF ID")

print("\n🚀 SHABLONLAR TAYYOR! Endi 'git push' qilish mumkin.")
