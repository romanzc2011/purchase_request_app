import asyncio
from api.schemas.enums import ItemStatus
from api.services.progress_tracker.steps.submit_request_steps import SubmitRequestStepName
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
from reportlab.lib.units import inch

from datetime import datetime, date
from loguru import logger
from pathlib import Path
from fastapi import Depends
from api.schemas.comment_schemas import SonCommentSchema
import api.services.db_service as dbas
from datetime import datetime
from pathlib import Path
from sqlalchemy import select
from api.utils.misc_utils import get_justifications_and_comments
from api.utils.misc_utils import format_username
from sqlalchemy.ext.asyncio import AsyncSession
from api.services.auth_service import AuthService
from api.services.ldap_service import LDAPService
from api.schemas.ldap_schema import LDAPUser
from api.services.progress_tracker.steps.download_steps import DownloadStepName
from api.services.progress_tracker.steps.submit_request_steps import SubmitRequestStepName
from api.services.progress_tracker.progress_manager import get_active_tracker, get_approval_tracker, get_download_tracker, get_submit_request_tracker, ProgressTrackerType
import api.services.socketio_server.sio_events as sio_events
from api.settings import settings

# Create auth service instance locally to prevent the circular import issue
ldap_service = LDAPService(
    ldap_url=settings.ldap_server,
    bind_dn=settings.ldap_service_user,
    bind_password=settings.ldap_service_password,
    group_dns=[
        settings.it_group_dns,
        settings.cue_group_dns,
        settings.access_group_dns,
    ],
)
auth_service = AuthService(ldap_service=ldap_service)

class PDFService:
    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    """
    Generate a purchase request PDF.

    Args:
        ID (str): The ID of the purchase request.
        is_cyber (bool): Whether the request is cybersecurity related.
        payload (dict): The payload of the purchase request.
        comments (list[str]): The comments of the purchase request.

    Returns:
        Path: The path to the generated PDF.
    """
    async def create_pdf(
        self,
        ID: str,
        db: AsyncSession,                         # ← Injected session
        payload: dict | None = None,
        comments: list[str] | None = None,
        is_cyber: bool = False,
        current_user: LDAPUser = None
    ) -> Path:
        logger.info(f"#####################################################")
        logger.info("create_pdf()")
        logger.info(f"#####################################################")
        
        if not ID:
            raise HTTPException(status_code=400, detail="ID is required")
        
        tracker = get_active_tracker()
        sid = sio_events.get_user_sid(current_user)
        
        # Init local trackers to prevent error
        download_tracker = None
        approval_tracker = None
        submit_request_tracker = None

        # Get appropriate tracker based on active tracker type
        if tracker:
            match tracker.active_tracker:
                case ProgressTrackerType.DOWNLOAD:
                    download_tracker = get_download_tracker()
                    
                case ProgressTrackerType.SUBMIT_REQUEST:
                    submit_request_tracker = get_submit_request_tracker()
                    
                case ProgressTrackerType.APPROVAL:
                    approval_tracker = get_approval_tracker()
        
        if sid and download_tracker:
            download_tracker.send_start_msg(sid)
            step_data = download_tracker.mark_step_done(DownloadStepName.VERIFY_FILE_EXISTS)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        if submit_request_tracker:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_GENERATION_STARTED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        # Fetch the flattened approval rows, and final approve data with timestamps
        rows = await dbas.fetch_flat_approvals(db, ID=ID)
        final_approved_result = await dbas.get_final_approved_by_id(db, ID)
        if final_approved_result:
            final_approved = final_approved_result[0]
            final_approved_at = final_approved_result[1]
        else:
            final_approved = None
            final_approved_at = None
            
        #!-PROGRESS TRACKING --------------------------------------------------------------
        # Only run if this is from the download pdf signal
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.FETCH_APPROVAL_DATA)
            if step_data:
                await sio_events.progress_update(sid, step_data)
                
            step_data = download_tracker.mark_step_done(DownloadStepName.FETCH_FLAT_APPROVALS)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        if not rows:
            raise HTTPException(status_code=404, detail="No approvals found for this ID")
        
        # Turn Pydantic models into dicts
        rows = [row.model_dump() for row in rows]

        # 2️⃣ Determine if any line items are cyber‐related
        is_cyber = any(r.get("isCyberSecRelated") for r in rows)
        
        # ------------------------------------------------------------------------
        # Build justifcation template if true for trainNotAval or needsNotMeet
        # Fetch additional comment fr   om database if present
        additional_comments = await get_justifications_and_comments(db, ID)
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.GET_JUSTIFICATIONS_AND_COMMENTS)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        contracting_officer = await dbas.get_contracting_officer_by_id(db, ID)
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.GET_CONTRACTING_OFFICER_BY_ID)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        # ------------------------------------------------------------------------
        # 3️⃣ Load SonComments via async select
        # Try to get SonComments through both line_item_uuid and approvals_uuid
        from api.services.db_service import PurchaseRequestLineItem
        
        # First, get line item UUIDs for this purchase request
        line_items_stmt = (
            select(PurchaseRequestLineItem.UUID)
            .where(PurchaseRequestLineItem.purchase_request_id == ID)
        )
        line_items_result = await db.execute(line_items_stmt)
        line_item_uuids = [row[0] for row in line_items_result.all()]
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.GET_LINE_ITEMS)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        # Get SonComments by line_item_uuid (more reliable)
        son_comments_stmt = (
            select(dbas.SonComment)
            .where(dbas.SonComment.line_item_uuid.in_(line_item_uuids))
            .where(dbas.SonComment.comment_text.is_not(None))
        )
        result = await db.execute(son_comments_stmt)
        son_comments = result.scalars().all()
        
        # Also try to get SonComments through approvals_uuid as backup
        approvals_stmt = (
            select(dbas.SonComment)
            .join(dbas.Approval, dbas.SonComment.approvals_uuid == dbas.Approval.UUID)
            .where(dbas.Approval.purchase_request_id == ID)
            .where(dbas.SonComment.comment_text.is_not(None))
        )
        approvals_result = await db.execute(approvals_stmt)
        approvals_son_comments = approvals_result.scalars().all()
        
        # Combine both results, avoiding duplicates
        all_son_comments = list(son_comments) + list(approvals_son_comments)
        unique_son_comments = list({comment.UUID: comment for comment in all_son_comments}.values())
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.GET_SON_COMMENTS)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        # Build your comment arrayrrr
        comment_arr: list[str] = []
        for c in unique_son_comments:
            cdata = SonCommentSchema.model_validate(c)
            if cdata.comment_text:
                comment_arr.append(cdata.comment_text)
                
        if additional_comments:
            comment_arr.extend(additional_comments)

        order_type = dbas.get_order_types(ID)
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.GET_ORDER_TYPES)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        #!-PROGRESS TRACKING --------------------------------------------------------------
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.LOAD_PDF_TEMPLATE)
            if step_data:
                await sio_events.progress_update(sid, step_data)
            
        if submit_request_tracker:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_TEMPLATE_LOADED)
            if step_data:
                await sio_events.progress_update(sid, step_data)
        
        # 5️⃣ Render the PDF
        output_path = self.output_dir / f"statement_of_need-{ID}.pdf"
        
        result = await asyncio.to_thread(
            self._make_purchase_request_pdf,
            rows=rows,
            output_path=output_path,
            is_cyber=is_cyber,
            use_comments=False,
            comments=comment_arr,
            order_type=order_type,
            contracting_officer=contracting_officer,
            download_tracker=download_tracker,
            final_approved=format_username(final_approved) if final_approved else None,
            final_approved_at=final_approved_at,
        )
        
        # Progress tracking after PDF generation is complete
        if download_tracker:
            step_data = download_tracker.mark_step_done(DownloadStepName.MERGE_DATA_INTO_TEMPLATE)
            await sio_events.progress_update(sid, step_data)
                
            step_data = download_tracker.mark_step_done(DownloadStepName.RENDER_PDF_BINARY)
            await sio_events.progress_update(sid, step_data)
                
            step_data = download_tracker.mark_step_done(DownloadStepName.SAVE_PDF_TO_DISK)
            await sio_events.progress_update(sid, step_data)
        
        if submit_request_tracker:
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_DATA_MERGED)
            await sio_events.progress_update(sid, step_data)
            
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_RENDERED)
            await sio_events.progress_update(sid, step_data)
            
            step_data = submit_request_tracker.mark_step_done(SubmitRequestStepName.PDF_SAVED_TO_DISK)
            await sio_events.progress_update(sid, step_data)
        
        return result
            
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
                                   use_comments: bool,
                                   comments: list[str]=None, 
                                   order_type: str=None,
                                   contracting_officer: str=None,
                                   download_tracker=None,
                                   final_approved: str=None,
                                   final_approved_at: datetime=None,
                                   ) -> Path: 
        logger.info(f"#####################################################")
        logger.info("make_purchase_request_pdf()")
        logger.info(f"#####################################################")
        
        # ensure output folder exists
        output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        # Try to get submit request tracker, but don't fail if it doesn't exist
        submit_request_tracker = None
        try:
            submit_request_tracker = get_submit_request_tracker()
        except RuntimeError:
            # Submit request tracker doesn't exist, which is fine for download operations
            pass
        
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

        #— document setup
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=LETTER,
            leftMargin=1*inch, rightMargin=1*inch,
            topMargin=img_h + gap + 1*inch, bottomMargin=1*inch
        )

        # Get first row data
        first = rows[0] if rows else {}
        logger.debug(f"first: {first}")

        # Get the final approved by
        logger.debug(f"final_approved: {final_approved}")

        #— draw header on canvas
        def draw_header(canvas, doc):
            canvas.saveState()
            canvas.setTitle("Statement of Need")

            # ----------------------------------------------------------------------------
            # logo
            x_logo = 0.2*inch
            y_logo = LETTER[1] - 0.2*inch
            canvas.drawImage(str(logo_path), x_logo, y_logo - img_h, width=img_w, height=img_h, mask='auto')

            # ----------------------------------------------------------------------------
            # title
            canvas.setFont("Play-Bold", 16)
            canvas.drawCentredString(LETTER[0]/2, LETTER[1] - 0.6*inch, "STATEMENT OF NEED")
            
            # ----------------------------------------------------------------------------
            # header text
            canvas.setFont("Play-Bold", 9)
            text_x = 0.2*inch
            text_y = y_logo - img_h - 20
            date_val = first.get("dateneed")
            
            # Use the function argument or fallback to row value
            order_type_val_local = order_type if order_type else first.get("orderType")
            date_str = None

            # ----------------------------------------------------------------------------
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
                
            # Format final approved at
            if final_approved and final_approved_at:
                approved_text = f"{final_approved} at {final_approved_at.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                approved_text = "None"
                
            items = [
                ("Purchase Request ID:", first.get("purchase_request_id","")),
                ("RQ1:", first.get("IRQ1_ID","")),
                ("Requester:", format_username(first.get("requester","") or "")),
                ("CO:", contracting_officer or "None"),
                ("Date Needed:", date_str),
                ("Status:", ItemStatus(first.get("status","")).value),
                ("Approved By:", approved_text),
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
        elements.append(Spacer(1, 56))

        # line-items table
        headings = ["BOC","Fund","Location","Description","Qty","Price Each","Total Price","Statement of Need/Justification"]
        table_data = [[Paragraph(h, header_style) for h in headings]]
        
        # Note: Progress tracking is handled in the main async method, not in this thread-based method
        
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
            '<font name="Play-Bold">Cybersecurity related - consider funding:</font> <font name="Play">{}</font>'.format(use_cyber),
            cell_style
        )
        
        legal_10_percent_para = Paragraph(
            '<font name="Play">*This statement of need approved with a 10% or $100 allowance, whichever is lower, for any additional cost over the estimated amount.</font>',
            cell_style
        )
        elements.append(cyber_para)
        elements.append(Spacer(1, 6))
        
        elements.append(legal_10_percent_para)
        elements.append(Spacer(1, 6))

        # Comments paragraph with all collected comments
        if use_comments:
            comments_html = (
                '<font name="Play-Bold">Comments/Additional Information Requested:</font><br/>' +
                "<br/>".join(f'<font name="Play">{c}</font>' for c in comments)
            )
            comments_para = Paragraph(comments_html, cell_style)
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
        
        # Note: Progress tracking is handled in the main async method, not in this thread-based method
        
        return output_path
        