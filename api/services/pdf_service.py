from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def make_purchase_request_pdf(lines, filename="statement_of_need.pdf"):
    """
    lines: list of dicts, each with keys:
        ID, requester,
        budgetObjCode, fund, location,
        itemDescription, quantity, priceEach, totalPrice, justification
    filename: output PDF path
    """
    doc = SimpleDocTemplate(filename, pagesize=LETTER,
                            rightMargin=30,leftMargin=30,
                            topMargin=30,bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header
    id = lines[0]['ID']
    requester = lines[0]['requester']
    elements.append(Paragraph(f"Purchase Request &nbsp;&nbsp; ID: <b>{id}</b>", styles['Title']))
    elements.append(Paragraph(f"Requester: <b>{requester}</b>", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Table data
    data = [["BOC","Fund","Location","Description","Qty","Price Each","Total","Justification"]]
    for line in lines:
        data.append([
            line['budgetObjCode'], line['fund'], line['location'],
            line['itemDescription'], line['quantity'],
            f"{line['priceEach']:.2f}", f"{line['totalPrice']:.2f}", 
            line['justification']
        ])
    
    # Table
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee")),
        ("GRID", (0,0), (-1,-1), 1, colors.gray),
        ("ALIGN", (4,0), (6,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE",     (0,0), (-1,-1),  9),
        ("BOTTOMPADDING",(0,0),(-1,0),   6),
    ]))
    elements.append(table)
    doc.build(elements)
    
    
