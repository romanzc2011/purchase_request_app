from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
import os

def make_purchase_request_pdf(lines, filename="statement_of_need.pdf"):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    elements = []
    elements.append(logo)
    elements.append(Spacer(1, 12))  # Add 12 points of space below the logo

    # --- 1) Header block ---
    elements.append(Paragraph("STATEMENT OF NEED (SON)", title))
    elements.append(Paragraph(
        "For IT, Director of IT approval  ________________________________",
        normal
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Order to be placed by:   IT Staff      Procurement Contracting Officer",
        normal
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Cybersecurity related – consider funding", normal))
    elements.append(Spacer(1, 12))

    # --- 2) Info row (Requester / CO / Date / RQ1) ---
    info_data = [[
        "Requester:", lines[0]["requester"],
        "CO:",        "",               # fill in as needed
        "Date:",      "",               # or datetime.now().strftime("%m/%d/%y")
        "RQ1:",       ""
    ]]
    # adjust colWidths to fit your page
    info_table = Table(info_data, colWidths=[60, 100, 30, 80, 40, 80, 30, 80])
    info_table.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0),  9),
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
        "BOC",
        "Fund",
        "Location",
        "Description",
        "Qty",
        "Price Each",
        "Estimated\nTotal Cost",
        "Statement of Need/\nJustification"
    ]
    data = [header]
    for line in lines:
        data.append([
            line["budgetObjCode"],
            line["fund"],
            line["location"],
            line["itemDescription"],
            line["quantity"],
            f"${line['priceEach']:.2f}",
            f"${line['totalPrice']:.2f}",
            line["justification"]
        ])

    # Set column widths so everything lines up nicely
    col_widths = [50, 60, 60, 180, 30, 50, 60, 120]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0),  8),
        ("ALIGN",      (0,0), (-1,0), "CENTER"),
        # Body styling
        ("GRID",       (0,0), (-1,-1), 1, colors.gray),
        ("FONTSIZE",   (0,1), (-1,-1),  9),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("ALIGN",      (4,1), (6,-1),   "RIGHT"),
        # Add some padding under header
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

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

    
    
