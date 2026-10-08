import io
import json
import os
import re

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QR_DIR = os.path.join(BASE_DIR, "static", "qr_codes")
QR_BOX_SIZE = 10
QR_BORDER = 1

PDF_MARGEM = 10 * mm
PDF_QR = 8 * mm
PDF_GAP_COLUNA = 3 * mm
PDF_ALTURA_ROTULO = 3.5 * mm
PDF_GAP_LINHA = 1.5 * mm


def ensure_qr_dir():
    os.makedirs(QR_DIR, exist_ok=True)


def qr_content(registro):
    data = registro.to_dict()
    data["qrcode"] = "bipagen"
    return json.dumps(data, ensure_ascii=False)


def qr_safe_name(nome_cepa):
    return re.sub(r"[\x00-\x1f/]", "_", nome_cepa or "")


def qr_filename(nome_cepa):
    return os.path.join(QR_DIR, f"{qr_safe_name(nome_cepa)}.png")


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


def _grid_pdf():
    page_w, page_h = A4
    passo_x = PDF_QR + PDF_GAP_COLUNA
    passo_y = PDF_QR + PDF_ALTURA_ROTULO + PDF_GAP_LINHA
    colunas = max(1, int((page_w - 2 * PDF_MARGEM + PDF_GAP_COLUNA) // passo_x))
    linhas = max(1, int((page_h - 2 * PDF_MARGEM + PDF_GAP_LINHA) // passo_y))
    return colunas, linhas, passo_x, passo_y


def generate_qr_pdf(registros, output_path=None):
    page_w, page_h = A4
    colunas, linhas, passo_x, passo_y = _grid_pdf()
    por_pagina = colunas * linhas

    buffer = io.BytesIO() if output_path is None else None
    c = canvas.Canvas(output_path or buffer, pagesize=A4)

    for i, registro in enumerate(registros):
        if i and i % por_pagina == 0:
            c.showPage()
        col = i % colunas
        linha = i // colunas
        path = qr_filename(registro.nome_cepa)
        if not os.path.exists(path):
            generate_qr(registro)
            path = qr_filename(registro.nome_cepa)
        x = PDF_MARGEM + col * passo_x + (passo_x - PDF_QR) / 2
        y = page_h - PDF_MARGEM - linha * passo_y - PDF_QR
        c.drawImage(
            path, x, y, width=PDF_QR, height=PDF_QR, preserveAspectRatio=True, mask="auto"
        )
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + PDF_QR / 2, y - 2.2 * mm, registro.codigo_unico or "")

    c.save()
    if output_path is None:
        buffer.seek(0)
        return buffer
    return output_path
