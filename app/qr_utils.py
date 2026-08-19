import io
import json
import os

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QR_DIR = os.path.join(BASE_DIR, "static", "qr_codes")
QR_SIZE_MM = 28
QR_BOX_SIZE = 10
QR_BORDER = 1


def ensure_qr_dir():
    os.makedirs(QR_DIR, exist_ok=True)


def qr_content(registro):
    data = registro.to_dict()
    data["qrcode"] = "bipagen"
    return json.dumps(data, ensure_ascii=False)


def qr_filename(nome_cepa):
    return os.path.join(QR_DIR, f"{nome_cepa}.png")


def generate_qr(registro):
    ensure_qr_dir()
    img = qrcode.make(
        qr_content(registro),
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    path = qr_filename(registro.nome_cepa)
    img.save(path)
    return path


def generate_qr_pdf(registros, output_path=None):
    page = landscape(A4)
    page_w, page_h = page
    margin = 10 * mm
    qr_w = QR_SIZE_MM * mm
    qr_h = qr_w
    cols = 3
    cell_w = (page_w - 2 * margin) / cols
    cell_h = qr_h + 20 * mm

    buffer = io.BytesIO() if output_path is None else None
    c = canvas.Canvas(output_path or buffer, pagesize=page)

    for i, registro in enumerate(registros):
        path = qr_filename(registro.nome_cepa)
        if not os.path.exists(path):
            generate_qr(registro)
            path = qr_filename(registro.nome_cepa)
        col = i % cols
        row = i // cols
        per_page = int((page_h - 2 * margin) // cell_h)
        if per_page <= 0:
            per_page = 1
        page_index = row // per_page
        pos_in_page = row % per_page
        if pos_in_page == 0 and page_index > 0:
            c.showPage()
        x = margin + col * cell_w
        y = page_h - margin - (pos_in_page + 1) * cell_h
        c.setFillColor(colors.white)
        c.rect(x, y, qr_w, qr_h, stroke=0, fill=1)
        c.drawImage(path, x, y, width=qr_w, height=qr_h, preserveAspectRatio=True, mask="auto")
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(x, y - 12, f"{registro.nome_cepa}")
        c.setFont("Helvetica", 8)
        c.drawString(x, y - 21, f"{registro.genero} {registro.especie}"[:32])

    c.save()
    if output_path is None:
        buffer.seek(0)
        return buffer
    return output_path
