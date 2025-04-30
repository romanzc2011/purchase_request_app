from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, PolyLine
from reportlab.lib.units import inch
from datetime import datetime
from loguru import logger
from pathlib import Path
from reportlab.platypus.flowables import Flowable

page_width, page_height = LETTER

#########################################################
# PDF Service
#########################################################   
def make_purchase_request_pdf(
    rows: list[dict],
    output_path: Path
) -> Path:
    # ensure output folder exists
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
    logger.info(f"Writing PDF to: {output_path}")

    #########################################################
    # Fonts
    #########################################################
    project_root = Path(__file__).resolve().parent.parent.parent
    pdfmetrics.registerFont(TTFont("Play",      str(project_root / "src/assets/fonts/Play-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Play-Bold", str(project_root / "src/assets/fonts/Play-Bold.ttf")))

    #########################################################
    # Logo
    #########################################################
    logo_path = project_root / "src/assets/seal_no_border.png"
    img_w = 0.85 * inch
    img_h = 0.85 * inch
    gap   = 6  # points of breathing room below the logo

    #########################################################   
    # Styles
    #########################################################
    styles       = getSampleStyleSheet()
    normal       = styles["Normal"];      normal.fontName = "Play"
    header_style = ParagraphStyle("Header", parent=normal, fontSize=9,  leading=10, fontName="Play-Bold")
    cell_style   = ParagraphStyle("Cell",   parent=normal, fontSize=9,  leading=11, fontName="Play")
    no_wrap      = ParagraphStyle("NoWrap", parent=normal, fontSize=8,  leading=10, fontName="Play")
    check_style  = ParagraphStyle("Check",  parent=normal, fontSize=8,  leading=10, fontName="Play")

    #########################################################
    # Document setup
    #########################################################   
    # — document setup: reserve space for logo + gap at top
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin   = 1 * inch,  # Standard margin for main content
        rightMargin  = 1 * inch,
        topMargin    = img_h + gap + 1 * inch,  # Extra space for header
        bottomMargin = 1 * inch,
    )

    #########################################################
    # Draw header
    #########################################################
    def draw_header(canvas, doc):
        canvas.saveState()
        
        # Set PDF's metadata title
        canvas.setTitle("Statement of Need")
        
        # Draw logo
        x = 0.2 * inch
        top_offset = 0.2 * inch
        y = page_height - top_offset
        canvas.drawImage(
            str(logo_path),
            x, y - img_h,
            width=img_w, height=img_h,
            mask="auto"
        )
        
        #########################################################
        # Draw title
        #########################################################
        
        canvas.setFont("Play-Bold", 16)
        title_x = page_width / 2
        title_y = page_height - (0.6 * inch)
        canvas.drawCentredString(title_x, title_y, "STATEMENT OF NEED")

        #########################################################
        # Draw header text
        #########################################################
        canvas.setFont("Play-Bold", 9)
        text_x = 0.2 * inch
        text_y = y - img_h - 20  # Start below logo
        
        #########################################################
        # Header data
        #########################################################
        first       = rows[0] if rows else {}
        requester   = first.get("requester", "") or ""
        date_str    = datetime.now().strftime("%m/%d/%y")
        purchase_id = first.get("purchaseReqID", "") or ""
        irq1        = first.get("IRQ1_ID", "") or ""

        #########################################################
        # Draw labels and values
        #########################################################
        canvas.setFont("Play-Bold", 9)
        header_items = [
            ("Requester:", requester),
            ("Date:", date_str),
            ("Purchase Req ID:", purchase_id),
            ("IRQ1:", irq1)
        ]
        
        for label, value in header_items:
            canvas.drawString(text_x, text_y, label)
            canvas.setFont("Play", 9)
            # Calculate position right after the label
            label_width = canvas.stringWidth(label, "Play-Bold", 9)
            value_x = text_x + label_width + 6  # Add small gap (6 points) after label
            canvas.drawString(value_x, text_y, value)
            canvas.setFont("Play-Bold", 9)
            text_y -= 15  # Move down for next line

        canvas.restoreState()

    # — build the flowables (main content only)
    elements = []

    #########################################################
    # TABLE DATA
    #########################################################
    # Line-item table with its own independent style
    headings   = ["BOC","Fund","Location","Description","Qty","Price Each","Total Price","Justification"]
    table_data = [[Paragraph(h, header_style) for h in headings]]
    for row in rows:
        
        table_data.append([
            Paragraph(row.get("budgetObjCode",""),   cell_style),
            Paragraph(row.get("fund",""),            cell_style),
            Paragraph(row.get("location",""),        cell_style),
            Paragraph(row.get("itemDescription",""), cell_style),
            Paragraph(str(row.get("quantity","")),   cell_style),
            Paragraph(f"${row.get('priceEach',0):.2f}", cell_style),
            Paragraph(f"${row.get('totalPrice',0):.2f}",cell_style),
            Paragraph(row.get("justification",""),   cell_style),
        ])

    col_widths = [50,60,60,180,30,50,60,120]
    line_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    line_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#EEEEEE")),
        ("FONTNAME",    (0,0), (-1,0), "Play-Bold"),
        ("FONTSIZE",    (0,0), (-1,0), 8),
        ("ALIGN",       (0,0), (-1,0), "CENTER"),
        ("GRID",        (0,0), (-1,-1), 1, colors.gray),
        ("FONTSIZE",    (0,1), (-1,-1), 9),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("ALIGN",       (4,1), (6,-1), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING",(0,0), (-1,-1), 6),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ]))
    # Build your main content into `elements`
    elements = []
    elements.append(line_table)
    elements.append(Spacer(1, 12))
    #########################################################
    # Footer    
    #########################################################
    
    # Calculate total before footer table
    total = sum(r.get("totalPrice", 0) for r in rows)
    
    # Right-aligned style for the total value
    total_value_style = ParagraphStyle(
        "TotalValue",
        parent=header_style,
        alignment=TA_RIGHT
    )
    
    checkbox = Drawing(10, 10)
    checkbox.add(PolyLine(
        points=[(2, 6), (4, 3), (8, 9)],
        strokeWidth=1,
    ))
    
    inner = Table(
    [[
        Paragraph("Cybersecurity related – consider funding", normal),
        checkbox
    ]],
    colWidths=[None, 0.2*inch]   # first col auto-sizes, second is 0.2"
    )

    footer_data = [
        [Paragraph(
            "*This statement of need approved with a 10% or $100 allowance…",
            no_wrap
        ), ''],
        [inner, ""],
        [Paragraph("TOTAL:", header_style),
         Paragraph(f"${total:.2f}", total_value_style)],
        [Paragraph("Final Approval for Purchase (SON):", normal), ''],
        [Paragraph("Comments/Additional Information Requested:", normal), '']
    ]
    
    # build a tiny 2-column row just for the cyber-note
   
    inner.setStyle(TableStyle([("LEFTPADDING",(0,0),(0,0),0),
                            ("RIGHTPADDING",(1,0),(1,0),0)]))

    # Build the footer table
    footer_table = Table(footer_data, colWidths=[4.5*inch, 2.0*inch])
    footer_table.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0), (-1,-1), 4),
        ("TOPPADDING",  (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        # line above the TOTAL row (row 2)
        ("LINEABOVE",   (0,2), (-1,2),   1, colors.gray),
        # override the paddings for the cyber-sec row (row 1):
        #   - cell (0,1) is the Paragraph
        ("RIGHTPADDING", (0,1), (0,1), 0),
        #   - cell (1,1) is the Drawing
        ("LEFTPADDING",  (1,1), (1,1), 0),
    ]))
    elements.append(footer_table)
    
    # Build document
    doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header)

    return output_path