import io
import pandas as pd
from datetime import datetime
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
import os

# ─── Arabic Font & RTL Setup ────────────────────────────────────────────────

ARABIC_FONT_PATH = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"
ARABIC_FONT_BOLD_PATH = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"
ARABIC_FONT_NAME = "NotoNaskhArabic"
ARABIC_FONT_BOLD_NAME = "NotoNaskhArabic-Bold"
_arabic_font_registered = False


def _register_arabic_font():
    """Register Noto Naskh Arabic font once with ReportLab."""
    global _arabic_font_registered
    if _arabic_font_registered:
        return True
    try:
        if os.path.exists(ARABIC_FONT_PATH):
            pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, ARABIC_FONT_PATH))
            if os.path.exists(ARABIC_FONT_BOLD_PATH):
                pdfmetrics.registerFont(TTFont(ARABIC_FONT_BOLD_NAME, ARABIC_FONT_BOLD_PATH))
            _arabic_font_registered = True
            return True
    except Exception:
        pass
    return False


def _reshape_arabic(text: str) -> str:
    """
    Reshape and apply BiDi algorithm to Arabic text for correct rendering in ReportLab.
    ReportLab renders text left-to-right internally, so Arabic must be pre-processed.
    """
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)


def _has_arabic(text: str) -> bool:
    """Quick check if a string contains Arabic characters."""
    try:
        for ch in str(text):
            if '\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u077F':
                return True
    except Exception:
        pass
    return False


def _process_cell(cell_value, arabic_available: bool) -> str:
    """Process a cell value: reshape Arabic text if font is available."""
    text = str(cell_value) if cell_value is not None else ''
    if arabic_available and _has_arabic(text):
        return _reshape_arabic(text)
    return text


def generate_excel(data: list, columns: list, sheet_name: str = "Report") -> io.BytesIO:
    """
    Generate Excel file from list of dictionaries
    data: List of dicts
    columns: List of column names (headers)
    """
    df = pd.DataFrame(data)
    
    # Filter/Order columns if specific columns requested
    if columns:
        # Only keep columns that exist in data
        valid_cols = [c for c in columns if c in df.columns]
        if valid_cols:
            df = df[valid_cols]
            
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Auto-adjust column width
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(df.columns):
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),
                len(str(col))
            )) + 1
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)
            
    output.seek(0)
    return output

def generate_pdf(data: list, title: str, columns: list = None, rtl: bool = None) -> io.BytesIO:
    """
    Generate a PDF report with Arabic/RTL support.
    
    data: List of dictionaries or List of Lists (first element = header if columns=None)
    title: Report Title (can contain Arabic)
    columns: Headers (if data is list of dicts)
    rtl: Force RTL mode. If None, auto-detect from title/data.
    """
    arabic_available = _register_arabic_font()
    
    # Auto-detect RTL
    if rtl is None:
        rtl = arabic_available and (_has_arabic(title) or (
            data and isinstance(data[0], (list, dict)) and
            any(_has_arabic(str(v)) for row in data[:3]
                for v in (row.values() if isinstance(row, dict) else row))
        ))
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    elements = []
    
    styles = getSampleStyleSheet()
    
    if rtl and arabic_available:
        # RTL Arabic styles
        title_style = ParagraphStyle(
            'ArabicTitle',
            fontName=ARABIC_FONT_BOLD_NAME if os.path.exists(ARABIC_FONT_BOLD_PATH) else ARABIC_FONT_NAME,
            fontSize=16,
            alignment=TA_RIGHT,
            spaceAfter=12,
            leading=24,
        )
        normal_style = ParagraphStyle(
            'ArabicNormal',
            fontName=ARABIC_FONT_NAME,
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=6,
            leading=16,
        )
        header_font = ARABIC_FONT_BOLD_NAME if os.path.exists(ARABIC_FONT_BOLD_PATH) else ARABIC_FONT_NAME
        body_font = ARABIC_FONT_NAME
    else:
        title_style = styles['Title']
        normal_style = styles['Normal']
        header_font = 'Helvetica-Bold'
        body_font = 'Helvetica'
    
    elements.append(Paragraph(_process_cell(title, rtl and arabic_available), title_style))
    elements.append(Spacer(1, 8))
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    elements.append(Paragraph(f"{'تاريخ الطباعة' if rtl else 'Generated on'}: {date_str}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Prepare Table Data
    table_data = []
    
    if columns:
        header_row = [_process_cell(c, rtl and arabic_available) for c in columns]
        # Reverse header for RTL
        if rtl:
            header_row = list(reversed(header_row))
        table_data.append(header_row)
    elif data and isinstance(data[0], list):
        # First row is headers
        header_row = [_process_cell(c, rtl and arabic_available) for c in data[0]]
        if rtl:
            header_row = list(reversed(header_row))
        table_data.append(header_row)
        data = data[1:]
        if columns is None:
            columns = data[0] if not table_data else None
    elif data and isinstance(data[0], dict):
        hdr = list(data[0].keys())
        header_row = [_process_cell(c, rtl and arabic_available) for c in hdr]
        if rtl:
            header_row = list(reversed(header_row))
        table_data.append(header_row)
        columns = hdr
    
    # Rows
    for row in data:
        if isinstance(row, dict):
            col_keys = columns or list(row.keys())
            cells = [_process_cell(row.get(c, ''), rtl and arabic_available) for c in col_keys]
        elif isinstance(row, list):
            cells = [_process_cell(c, rtl and arabic_available) for c in row]
        else:
            continue
        if rtl:
            cells = list(reversed(cells))
        table_data.append(cells)
    
    if not table_data:
        elements.append(Paragraph("لا توجد بيانات / No data" if rtl else "No data", normal_style))
    else:
        # Determine column count for width calculation
        col_count = len(table_data[0])
        available_width = A4[0] - 80  # Total width minus margins
        col_width = available_width / max(col_count, 1)
        col_widths = [col_width] * col_count

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        header_bg = colors.HexColor('#2C3E50')
        alt_row_bg = colors.HexColor('#F5F7FA')
        
        table_style = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), header_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), body_font),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, alt_row_bg]),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            # Text alignment
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if rtl else 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        t.setStyle(TableStyle(table_style))
        elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_export_response(file_buffer: io.BytesIO, filename: str, content_type: str):
    return StreamingResponse(
        file_buffer,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
