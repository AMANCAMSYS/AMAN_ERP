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
import os

# Register Arabic font if available, otherwise fallback
# Note: In a real environment, ensure an Arabic-supporting font (like Arial or Traditional Arabic) is available
# For this environment, we'll try to use a standard font or skip if not found
try:
    # This path might need adjustment based on the OS
    # Using a common path or a bundled font is better
    # For now, we will use standard fonts and assume English/transliteration if Arabic fails rendering in standard
    pass 
except:
    pass

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
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
            
    output.seek(0)
    return output

def generate_pdf(data: list, title: str, columns: list = None) -> io.BytesIO:
    """
    Generate a simple PDF report
    data: List of dictionaries or List of Lists
    title: Report Title
    columns: Headers (if data is list of dicts)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # Prepare Table Data
    table_data = []
    
    # Headers
    if columns:
        table_data.append(columns)
    elif data and isinstance(data[0], dict):
        headers = list(data[0].keys())
        table_data.append(headers)
        columns = headers
    
    # Rows
    for row in data:
        if isinstance(row, dict):
            table_data.append([str(row.get(c, '')) for c in columns])
        elif isinstance(row, list):
            table_data.append([str(c) for c in row])
            
    # Table Styling
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
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
