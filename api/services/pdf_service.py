from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

import os

def make_purchase_request_pdf(lines, filename="statement_of_need.pdf"):
    # Register Play font
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    font_path = os.path.join(project_root, "src", "assets", "fonts", "Play-Regular.ttf")
    font_path_bold = os.path.join(project_root, "src", "assets", "fonts", "Play-Bold.ttf")

    img_path = os.path.join(project_root, "src", "assets", "seal_no_border.png")
    logo = Image(img_path, width=95, height=95)
    
    doc = SimpleDocTemplate(
        filename, pagesize=LETTER,
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=18
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title  = styles["Title"]
    title.fontSize = 14
    
    # Register the fonts
    pdfmetrics.registerFont(TTFont("Play", font_path))
    pdfmetrics.registerFont(TTFont("Play-Bold", font_path_bold))
    
    # Create custom styles with Play font
    normal.fontName = "Play"
    title.fontName = "Play-Bold"
    no_wrap = ParagraphStyle(name="NoWrap", parent=normal, fontSize=8, leading=10, fontName="Play")
    header_style = ParagraphStyle(name="Header", parent=normal, fontSize=9, leading=10, fontName="Play-Bold")
    # Add cell style for wrapping text
    cell_style = ParagraphStyle(name="Cell", parent=normal, fontSize=9, leading=11, fontName="Play")

    elements = []
    elements.append(logo)
    elements.append(Spacer(1, 12))  # Add 12 points of space below the logo
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Cybersecurity related – consider funding", normal))
    elements.append(Spacer(1, 12))

    # --- 2) Info row (Requester / CO / Date / RQ1) ---
    info_data = [[
        "Requester:", lines[0]["requester"],
        "CO:",        "",               # fill in as needed
        "Date:",      datetime.now().strftime("%m/%d/%y"),               # or datetime.now().strftime("%m/%d/%y")
        "RQ1:",       ""
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

    # --- 3) JOFOC paragraph ---
    elements.append(Paragraph(
        "Attached is JOFOC (AO370) for other than full and open competition.",
        normal
    ))
    elements.append(Spacer(1, 12))

    # --- 4) Main data table with multi-line headers ---
    # Build your header row exactly as the PDF shows, using "\n" for line breaks:
    header = [
    Paragraph("BOC", header_style),
    Paragraph("Fund", header_style),
    Paragraph("Location", header_style),
    Paragraph("Description", header_style),
    Paragraph("Qty", header_style),
    Paragraph("Price Each", header_style),
    Paragraph("Estimated<br/>Total Cost", header_style),
    Paragraph("Statement of Need/<br/>Justification", header_style),
    ]
    
    data = [header]
    IT_fund = False
    
    for line in lines:
        data.append([
            Paragraph(str(line["budgetObjCode"]), cell_style),
            Paragraph(str(line["fund"]), cell_style),
            Paragraph(str(line["location"]), cell_style),
            Paragraph(str(line["itemDescription"]), cell_style),
            Paragraph(str(line["quantity"]), cell_style),
            Paragraph(f"${line['priceEach']:.2f}", cell_style),
            Paragraph(f"${line['totalPrice']:.2f}", cell_style),
            Paragraph(str(line["justification"]), cell_style)
        ])
        
        # Determine if fund is 51140E or 51140X
        if line["fund"] == "51140E" or line["fund"] == "51140X":
            IT_fund = True
        else:
            IT_fund = False 

    # Set column widths so everything lines up nicely
    col_widths = [50, 60, 60, 180, 30, 50, 60, 120]
    table = Table(data, colWidths=col_widths, repeatRows=1)
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

    # --- 5) Footer (TOTAL line, final approval, comments) ---
    elements.append(Paragraph(
        f"TOTAL: {sum(line['totalPrice'] for line in lines):.2f}", normal
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "Final Approval for Purchase (SON)  (Signature/Date) ________________________",
        normal
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Comments/Additional Information Requested:", normal))

    doc.build(elements)

    
    
