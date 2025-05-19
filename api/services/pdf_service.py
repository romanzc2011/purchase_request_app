from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, PolyLine
from reportlab.lib.units import inch
from datetime import datetime
from loguru import logger
from pathlib import Path

page_width, page_height = LETTER

"""
    Generate a purchase request PDF.

    Args:
        rows (List[Dict[str, Any]]):  
            List of dictionaries containing purchase request data.  
        output_path (Path):  
            Path where the PDF will be saved.  
        is_cyber (bool):  
            Whether the request is cybersecurity related.

    Returns:
        Path:  
            The path to the generated PDF.
    """

def make_purchase_request_pdf(rows: list[dict], output_path: Path, is_cyber: bool, comments: list[str]=None) -> Path:
    # ensure output folder exists
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    
    #— fonts & logo setup
    project_root = Path(__file__).resolve().parent.parent.parent
    pdfmetrics.registerFont(TTFont("Play", str(project_root / "src/assets/fonts/Play-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Play-Bold", str(project_root / "src/assets/fonts/Play-Bold.ttf")))

    logo_path = project_root / "src/assets/seal_no_border.png"
    img_w, img_h = 0.85 * inch, 0.85 * inch
    gap = 6  # points of breathing room

    #— styles
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Play"
    bold_style = ParagraphStyle(
        name="BoldStyle",
        parent=normal,
        fontName="Play",
        fontSize=9
    )
    header_style = ParagraphStyle("Header", parent=normal, fontSize=9, leading=10, fontName="Play-Bold")
    cell_style = ParagraphStyle("Cell", parent=normal, fontSize=9, leading=11, fontName="Play")
    no_wrap = ParagraphStyle("NoWrap", parent=normal, fontSize=8, leading=10, fontName="Play")

    comment_style = ParagraphStyle(
        "CommentStyle",
        parent=normal,
        fontName="Play",
        fontSize=9,
        alignment=TA_LEFT,
        allowWidows=1,
        allowOrphans=1
    )

    #— document setup
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=1*inch, rightMargin=1*inch,
        topMargin=img_h + gap + 1*inch, bottomMargin=1*inch
    )

    #— draw header on canvas
    def draw_header(canvas, doc):
        canvas.saveState()
        canvas.setTitle("Statement of Need")

        # logo
        x_logo = 0.2*inch
        y_logo = page_height - 0.2*inch
        canvas.drawImage(str(logo_path), x_logo, y_logo - img_h, width=img_w, height=img_h, mask='auto')

        # title
        canvas.setFont("Play-Bold", 16)
        canvas.drawCentredString(page_width/2, page_height - 0.6*inch, "STATEMENT OF NEED")

        # header text
        canvas.setFont("Play-Bold", 9)
        text_x = 0.2*inch
        text_y = y_logo - img_h - 20
        first = rows[0] if rows else {}
        logger.info(f"First row data for header: {first}")
        logger.info(f"Date needed value: {first.get('dateneed')}")
        items = [
            ("Purchase Req ID:", first.get("ID","")),
            ("IRQ1:", first.get("IRQ1_ID","")),
            ("Requester:", first.get("requester","")),
            ("CO:", first.get("CO","")),
            ("Date Needed:", first.get("dateneed","").split("T")[0] if first.get("dateneed") else "Not specified"),
        ]
        for label, value in items:
            canvas.drawString(text_x, text_y, label)
            canvas.setFont("Play", 9)
            lw = canvas.stringWidth(label, "Play-Bold", 9)
            canvas.drawString(text_x + lw + 6, text_y, str(value))
            canvas.setFont("Play-Bold", 9)
            text_y -= 15

        canvas.restoreState()

    #— build flowables
    elements = []
    elements.append(Spacer(1, 36))

    # line-items table
    headings = ["BOC","Fund","Location","Description","Qty","Price Each","Total Price","Justification"]
    table_data = [[Paragraph(h, header_style) for h in headings]]
    
    for r in rows:
        table_data.append([
            Paragraph(r.get("budgetObjCode",""), cell_style),
            Paragraph(r.get("fund",""), cell_style),
            Paragraph(r.get("location",""), cell_style),
            Paragraph(r.get("itemDescription",""), cell_style),
            Paragraph(str(r.get("quantity","")), cell_style),
            Paragraph(f"${r.get('priceEach',0):.2f}", cell_style),
            Paragraph(f"${r.get('totalPrice',0):.2f}", cell_style),
            Paragraph(r.get("justification",""), cell_style),
        ])
    
    line_table = Table(table_data, colWidths=[50,60,60,180,30,50,60,120], repeatRows=1)
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EEEEEE")),
        ("FONTNAME", (0,0), (-1,0), "Play-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("ALIGN",    (0,0), (-1,0), "CENTER"),
        ("GRID",     (0,0), (-1,-1), 1, colors.gray),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("VALIGN",   (0,0), (-1,-1), "TOP"),
        ("ALIGN",    (4,1), (6,-1), "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 12))

    #########################################################
    # Footer section
    #########################################################
    total = sum(r.get("totalPrice", 0) for r in rows)

    use_cyber = "Yes" if is_cyber else "No"
    # Cybersecurity line with inline checkmark
    cyber_para = Paragraph(
        f"Cybersecurity related - consider funding: <font name='Play-Bold'>{use_cyber}</font>", 
        comment_style
    )
    elements.append(cyber_para)
    elements.append(Spacer(1, 6))

    # Comments paragraph with all collected comments
    if comments:
        comments_text = "Comments/Additional Information Requested:<br/>" + "<br/>".join(comments)
        comments_para = Paragraph(comments_text, comment_style)
        elements.append(comments_para)
        elements.append(Spacer(1, 6))

    # Build TOTAL line
    total_style = ParagraphStyle(
        "TotalValue", parent=header_style, alignment=TA_RIGHT
    )
    total_data = [
        ["", Paragraph(f"TOTAL: ${total:.2f}", total_style)]
    ]
    total_table = Table(
        total_data,
        colWidths=[doc.width - 1.5 * inch, 1.5 * inch]
    )
    total_table.setStyle(TableStyle([
        ("LINEABOVE",       (0, 0), (-1, 0), 1, colors.gray),
        ("ALIGN",           (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING",     (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",    (0, 0), (-1, -1), 4),
        ("TOPPADDING",      (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",   (0, 0), (-1, -1), 2),
    ]))
    elements.append(total_table)

    # Build document
    doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header)
    return output_path