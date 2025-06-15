from api.services.cache_service import cache_service
from fastapi import HTTPException
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

from datetime import datetime, date
from loguru import logger
from pathlib import Path
from api.settings import settings
from api.services.db_service import Approval, JustificationTemplate, SonComment, get_all_son_comments, get_session
from api.services.db_service import get_all_approvals
from api.schemas.comment_schemas import SonCommentSchema
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import api.services.db_service as dbas

class PDFService:
    def __init__(self):
        self.pdf_path = settings.PDF_OUTPUT_FOLDER
        self.pdf_path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
        self.page_width = LETTER
        self.page_height = LETTER

    """
    Generate a purchase request PDF.

    Args:
        id (str): The id of the purchase request.
        is_cyber (bool): Whether the request is cybersecurity related.
        payload (dict): The payload of the purchase request.
        comments (list[str]): The comments of the purchase request.

    Returns:
        Path: The path to the generated PDF.
    """
    def create_pdf(
        self,
        id: str, 
        is_cyber: bool=False,   
        payload: dict=None,
        comments: list[str]=None,
        ) -> Path:
        from api.schemas.approval_schemas import ApprovalDetailSchema
        
        with get_session() as session:
        
            if not id:
                raise HTTPException(status_code=400, detail="id is required")
            
            try:
                # Get all approvals for this id
                stmt = select(Approval).where(Approval.purchase_request_id == id)
                approvals = session.scalars(stmt).all()
                
                logger.info(f"approvals: {approvals}")
                if not approvals:
                    raise HTTPException(status_code=404, detail="No approvals found for this id")
                
                # Convert to list of dicts
                rows = [ApprovalDetailSchema.model_validate(a).model_dump() for a in approvals]
                logger.info(f"rows: {rows}")
                
                # Check if any line items as marked as cyber security related
                is_cyber = any(row.get("is_cyber_sec_related") for row in rows)
                
                comment_arr: list[str] = []
                # Initialize order_type with a default value
                order_type = None
                
                stmt = select(SonComment).where(SonComment.purchase_request_id == id)
                comments = session.scalars(stmt).all()
                
                flags = dbas.fetch_just_flags_by_id(id)
                logger.info(f"Flags: {flags}")
                
                include_train_not_aval = any(flag[0] for flag in flags)
                include_needs_not_meet = any(flag[1] for flag in flags)
                
                logger.info(f"include_train_not_aval: {include_train_not_aval}")
                logger.info(f"include_needs_not_meet: {include_needs_not_meet}")
                
                add_comments = []
                #---------------------------------------------------------------------------
                # Query justification templates
                if include_train_not_aval:
                    stmt = select(JustificationTemplate).where(JustificationTemplate.code == "NOT_AVAILABLE")
                    not_available_comment = session.scalars(stmt).first()
                    add_comments.append(not_available_comment.description)
                    logger.info(f"Not available comment: {not_available_comment}")
							
                if include_needs_not_meet:
                    stmt = select(JustificationTemplate).where(JustificationTemplate.code == "DOESNT_MEET_NEEDS")
                    doesnt_meet_needs_comment = session.scalars(stmt).first()
                    add_comments.append(doesnt_meet_needs_comment.description)
                    logger.info(f"Doesnt meet needs comment: {doesnt_meet_needs_comment}")
            
                if comments:
                    for c in comments:
                        comment_data = SonCommentSchema.model_validate(c)
                        # Only add non-empty comments
                        if comment_data.comment_text is not None:
                            comment_arr.append(comment_data.comment_text)
                                
                    # Check if there are any additional comments in the add_comments field in purchase_requests
                    order_type = cache_service.get_or_set(
                        "order_types",
                        id, 
                        lambda: dbas.get_order_types(id))
                    
                    # Cache the additional comments
                    cache_service.set("comments", id, add_comments)
                    cache_service.set("order_types", id, order_type)
                    
                    if add_comments:
                        # Split comments by semicolon and add each part to the array
                        for comment in add_comments:
                            if comment:
                                comment_arr.extend(comment.split(', '))
                
                logger.info(f"comment_arr: {comment_arr}")

                # Construct the output path with filename
                output_path = self.pdf_path / f"statement_of_need-{id}.pdf"
                                
                # Generate PDF
                return self._make_purchase_request_pdf(rows=rows, output_path=output_path, is_cyber=is_cyber, comments=comment_arr, order_type=order_type)
            
            except Exception as e:
                logger.error(f"Error creating PDF: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            
    """
        Generate a purchase request PDF.

        Args:
            rows (List[Dict[str, Any]]):  
                List of dictionaries containing purchase request data.  
            output_path (Path):  
                Path where the PDF will be saved.  
            is_cyber (bool):  
                Whether the request is cybersecurity related.
            comments (list[str]):
                List of comments to be added to the PDF.

        Returns:
            Path:
                The path to the generated PDF.
        """
    @staticmethod
    def _make_purchase_request_pdf(rows: list[dict], 
                                   output_path: Path, 
                                   is_cyber: bool, 
                                   comments: list[str]=None, 
                                   order_type: str=None
                                   ) -> Path: 
        logger.info(f"#####################################################")
        logger.info("make_purchase_request_pdf()")
        logger.info(f"#####################################################")
        logger.info(f"COMMENTS: {comments}")
        
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
            parent=cell_style,
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

        # Get first row data
        first = rows[0] if rows else {}

        #— draw header on canvas
        def draw_header(canvas, doc):
            canvas.saveState()
            canvas.setTitle("Statement of Need")

            # logo
            x_logo = 0.2*inch
            y_logo = LETTER[1] - 0.2*inch
            canvas.drawImage(str(logo_path), x_logo, y_logo - img_h, width=img_w, height=img_h, mask='auto')

            # title
            canvas.setFont("Play-Bold", 16)
            canvas.drawCentredString(LETTER[0]/2, LETTER[1] - 0.6*inch, "STATEMENT OF NEED")
            
            # header text
            canvas.setFont("Play-Bold", 9)
            text_x = 0.2*inch
            text_y = y_logo - img_h - 20
            logger.info(f"First row data for header: {first}")
            logger.info(f"Date needed value: {first.get('dateneed')}")
            
            date_val = first.get("dateneed")
            # Use the function argument or fallback to row value
            order_type_val_local = order_type if order_type else first.get("order_type")
            date_str = None

            # Format date needed
            if isinstance(date_val, (datetime, date)):
                date_str = date_val.strftime("%Y-%m-%d")
            elif isinstance(date_val, str) and date_val:
                date_str = date_val.split("T", 1)[0]
            elif isinstance(order_type_val_local, str):
                if order_type_val_local == "QUARTERLY_ORDER":
                    date_str = "Quarterly Order"
                elif order_type_val_local == "NO_RUSH":
                    date_str = "No Rush"
                else:
                    date_str = "Not specified"
            else:
                date_str = "Not specified"
            
            items = [
                ("Purchase Req id:", first.get("request_id","")),
                ("IRQ1:", first.get("IRQ1_ID","")),
                ("Requester:", first.get("requester","")),
                ("CO:", first.get("CO","")),
                ("Date Needed:", date_str),
                
            ]
            logger.info(f"items: {items}")
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
                Paragraph(r.get("budget_obj_code",""), cell_style),
                Paragraph(r.get("fund",""), cell_style),
                Paragraph(r.get("location",""), cell_style),
                Paragraph(r.get("item_description",""), cell_style),
                Paragraph(str(r.get("quantity","")), cell_style),
                Paragraph(f"${r.get('priceEach',0):.2f}", cell_style),
                Paragraph(f"${r.get('total_price',0):.2f}", cell_style),
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
        total = sum(r.get("total_price", 0) for r in rows)

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
            comments_text = "<b>Comments/Additional Information Requested:</b><br/>" + "<br/>".join([str(c) for c in comments])
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