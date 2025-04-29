from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect
from datetime import datetime
from settings import settings
from loguru import logger
from pathlib import Path
import os

def make_purchase_request_pdf(
    rows: list[dict],
    output_path: Path
) -> Path:

    # ensure output folder exits
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    logger.info(f"Writing PDF to: {output_path}")
        
    # register fonts
    project_root = Path(__file__).resolve().parent.parent.parent

    font_path = project_root / "src" / "assets" / "fonts" / "Play-Regular.ttf"
    font_path_bold = project_root / "src" / "assets" / "fonts" / "Play-Bold.ttf"

    pdfmetrics.registerFont(TTFont("Play", str(font_path)))
    pdfmetrics.registerFont(TTFont("Play-Bold", str(font_path_bold)))

    # build document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # build document
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Play"
    header_style = ParagraphStyle(
        name="Header", parent=normal, 
        fontSize=9, leading=11, fontName="Play-Bold"
    )
    cell_style = ParagraphStyle(
        name="Cell", parent=normal, 
        fontSize=9, leading=11, fontName="Play"
    )
    title  = styles["Title"]
    title.fontSize = 14
    
    no_wrap = ParagraphStyle(name="NoWrap", parent=normal, fontSize=8, leading=10, fontName="Play")
    header_style = ParagraphStyle(name="Header", parent=normal, fontSize=9, leading=10, fontName="Play-Bold")
    # Add cell style for wrapping text
    cell_style = ParagraphStyle(name="Cell", parent=normal, fontSize=9, leading=11, fontName="Play")
    check_style = ParagraphStyle(name="Check", parent=normal, fontSize=8, leading=10, fontName="Play")

    elements = []
    
    # load logo
    img_path = os.path.join(project_root, "src", "assets", "seal_no_border.png")
    logo = Image(img_path, width=95, height=95)
    
    elements.append(logo)
    elements.append(Spacer(1, 12))  # Add 12 points of space below the logo
    elements.append(Spacer(1, 6))
    
    # --- 2) Info row (Requester / CO / Date / RQ1) ---
    first = rows[0]
    info_data = [[
        "Requester:", first.get("requester", ""),
        "Date:", datetime.now().strftime("%m/%d/%y"),
        "RQ1:", first.get("IRQ1_ID", "")
    ]]
    # adjust colWidths to fit your page
    info_table = Table(info_data, colWidths=[60, 100, 30, 80, 40, 80, 30, 80])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("FONTNAME",   (0,0), (-1,0), "Play-Bold"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW",  (1,0), (1,0),   1, colors.black),
        ("LINEBELOW",  (3,0), (3,0),   1, colors.black),
        ("LINEBELOW",  (5,0), (5,0),   1, colors.black),
        ("LINEBELOW",  (7,0), (7,0),   1, colors.black),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))
    
    # header row for table
    header = [
        Paragraph("BOC", header_style),
        Paragraph("Fund", header_style),
        Paragraph("Location", header_style),
        Paragraph("Description", header_style),
        Paragraph("Qty", header_style),
        Paragraph("Price Each", header_style),
        Paragraph("Total Price", header_style),
        Paragraph("Justification", header_style),
    ]
    table_data = [header]  # Add header row to table_data
    
    # data rows
    for row in rows:
        table_data.append([
            Paragraph(row.get("budgetObjCode", ""), cell_style),
            Paragraph(row.get("fund", ""), cell_style),
            Paragraph(row.get("location", ""), cell_style),
            Paragraph(row.get("itemDescription", ""), cell_style),
            Paragraph(str(row.get("quantity", "")), cell_style),
            Paragraph(f"${row.get('priceEach', 0):.2f}", cell_style),
            Paragraph(f"${row.get('totalPrice', 0):.2f}", cell_style),
            Paragraph(row.get("justification", ""), cell_style)
        ])

    # Set column widths so everything data up nicely
    col_widths = [50, 60, 60, 180, 30, 50, 60, 120]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("FONTNAME",   (0,0), (-1,0), "Play-Bold"),  # Make header bold
        ("FONTSIZE",   (0,0), (-1,0),  8),
        ("ALIGN",      (0,0), (-1,0), "CENTER"),
        # Body styling
        ("GRID",       (0,0), (-1,-1), 1, colors.gray),
        ("FONTSIZE",   (0,1), (-1,-1),  9),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("ALIGN",      (4,1), (6,-1),   "RIGHT"),
        # Add some padding under header
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        # Add padding to cells
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("*This statement of need approved with a 10% or $100 allowance, whichever is lower, "
                              "for any additional cost over the estimated amount", no_wrap))
    
    # Add cybersecurity text at the bottom left
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Cybersecurity related – consider funding", normal))

    # --- 5) Footer (TOTAL line, final approval, comments) ---
    elements.append(Paragraph(
        f"TOTAL: {sum(row['totalPrice'] for row in rows):.2f}", normal
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "Final Approval for Purchase (SON)  (Signature/Date) ________________________",
        normal
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Comments/Additional Information Requested:", normal))
    
    # Cybersecurity option
    # make a 10×10 pt box with a 1-pt stroke
    d = Drawing(12, 12)
    d.add(Rect(0, 0, 10, 10, strokeWidth=1, strokeColor=colors.black, fillColor=None))

    small_text = Paragraph("Cybersecurity related – consider funding", check_style)
    elements.append(Spacer(1, 6))
    elements.append(
        Table(
        [[d, small_text]],
        colWidths=[12, 300],  # adjust as you like
        style=[("VALIGN", (0,0), (-1,-1), "MIDDLE")]
        )
    )

    doc.build(elements)
    
    return output_path