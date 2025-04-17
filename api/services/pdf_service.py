from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
import datetime
from loguru import logger

sample_request = {
        'ID': '20250415-0001',
        'requester': 'John Doe',
        'datereq': '2025-04-15',
        'dateneed': '2025-04-30',
        'itemDescription': 'Office supplies including paper, pens, and notebooks',
        'quantity': 10,
        'priceEach': 25.50,
        'totalPrice': 255.00,
        'budgetObjCode': '3101',
        'fund': '51140X',
        'justification': 'Monthly office supplies needed for the department',
        'addComments': 'Please deliver to the main office',
        'status': 'NEW REQUEST'
    }

class PDFService:
    """
    A service class for generating PDF documents using ReportLab.
    Provides methods for creating various types of PDFs with different features.
    """
    
    def __init__(self):
        """
        Initialize the PDF service.
        
        Args:
            output_dir: Directory where PDFs will be saved
        """
        self.output_dir = "../pdf_output"
        self.seal_img = "../src/assets/seal_no_border.png"
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"PDFService initialized with output directory: {self.output_dir}")
    
    def create_pdf(self, output_filename):
        """
        Create a sample PDF document with various ReportLab features
        
        Args:
            output_filename: Name of the output PDF file
            
        Returns:
            Path to the created PDF file
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        subtitle_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        # Add a title
        title = Paragraph("Sample ReportLab PDF", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Add a subtitle
        subtitle = Paragraph("Generated with Python and ReportLab", subtitle_style)
        elements.append(subtitle)
        elements.append(Spacer(1, 12))
        
        # Add some text
        text = """
        This is a sample PDF document created with ReportLab. 
        ReportLab is a powerful Python library for generating PDF documents.
        It supports text, tables, images, and many other elements.
        """
        elements.append(Paragraph(text, normal_style))
        elements.append(Spacer(1, 12))
        
        # Add a table
        data = [
            ["Item", "Quantity", "Price", "Total"],
            ["Widget A", "5", "$10.00", "$50.00"],
            ["Widget B", "3", "$15.00", "$45.00"],
            ["Widget C", "2", "$20.00", "$40.00"],
            ["", "", "Total:", "$135.00"]
        ]
        
        table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 12))
        
        # Add a custom paragraph style
        custom_style = ParagraphStyle(
            'CustomStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        elements.append(Paragraph("This text uses a custom style", custom_style))
        
        # Add a page break
        elements.append(Spacer(1, 12))
        
        # Add a section with different alignments
        elements.append(Paragraph("Left-aligned text", ParagraphStyle('LeftAlign', parent=styles['Normal'], alignment=TA_LEFT)))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("Center-aligned text", ParagraphStyle('CenterAlign', parent=styles['Normal'], alignment=TA_CENTER)))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("Right-aligned text", ParagraphStyle('RightAlign', parent=styles['Normal'], alignment=TA_RIGHT)))
        
        # Build the PDF
        doc.build(elements)
        
        # Add the seal image to the PDF
        self._add_BKSEAL_to_pdf(self.seal_img, output_path)
        
        logger.info(f"PDF created successfully at: {os.path.abspath(output_path)}")
        return output_path
    
    def _add_BKSEAL_to_pdf(self, image_path, pdf_path):
        """
        Add an image to an existing PDF
        
        Args:
            image_path: Path to the image file
            pdf_path: Path to the PDF file to modify
            
        Returns:
            Path to the modified PDF file
        """
        # Create a temporary file for the modified PDF
        temp_path = pdf_path.replace('.pdf', '_with_seal.pdf')
        
        # Create a new PDF with the image
        c = canvas.Canvas(temp_path, pagesize=A4)
        
        # Draw the image with transparency support in the top left corner
        # A4 page size is 595 x 842 points (8.27 x 11.69 inches)
        # Position at (50, 750) which is near the top left corner
        c.drawImage(image_path, 50, 750, width=100, height=100, mask='auto')
        
        # Add some text
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 450, "PDF with Image")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, 430, "This is an example of adding an image to a PDF")
        
        # Save the PDF
        c.save()
        
        # Replace the original PDF with the modified one
        os.replace(temp_path, pdf_path)
        
        logger.info(f"Image added to PDF at: {os.path.abspath(pdf_path)}")
        return pdf_path
    
    def create_pdf_with_header_footer(self, output_filename="header_footer_report.pdf"):
        """
        Create a PDF with headers and footers on each page
        
        Args:
            output_filename: Name of the output PDF file
            
        Returns:
            Path to the created PDF file
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        class HeaderFooterCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs)
                self.pages = []
                self.seal_img = kwargs.get('seal_img')
            
            def showPage(self):
                self.pages.append(dict(self.__dict__))
                self._startPage()
            
            def save(self):
                page_count = len(self.pages)
                for page in self.pages:
                    self.__dict__.update(page)
                    self.draw_header()
                    self.draw_footer()
                    canvas.Canvas.showPage(self)
                canvas.Canvas.save(self)
            
            def draw_header(self):
                # Header
                self.setFont("Helvetica-Bold", 12)
                self.drawString(72, 800, "Company Name")
                self.drawString(72, 780, "Report Title")
                self.line(72, 770, 522, 770)  # Horizontal line
                
                # Add the seal image if available in the top left corner
                if self.seal_img and os.path.exists(self.seal_img):
                    # Position at (50, 750) which is near the top left corner
                    self.drawImage(self.seal_img, 30, 750, width=80, height=80, mask='auto')
            
            def draw_footer(self):
                # Footer
                self.setFont("Helvetica", 9)
                self.drawString(72, 72, "Generated on: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.drawRightString(522, 72, f"Page {len(self.pages)}")
                self.line(72, 82, 522, 82)  # Horizontal line
        
        # Create the PDF with custom canvas
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Add content
        elements.append(Paragraph("Document with Headers and Footers", styles["Heading1"]))
        elements.append(Spacer(1, 12))
        
        for i in range(1, 4):  # Add some content
            elements.append(Paragraph(f"Section {i}", styles["Heading2"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("This is some sample content for the document.", styles["Normal"]))
            elements.append(Spacer(1, 12))
        
        # Build the PDF with custom canvas, passing the seal image
        doc.build(elements, canvasmaker=lambda *args, **kwargs: HeaderFooterCanvas(*args, seal_img=self.seal_img, **kwargs))
        
        logger.info(f"PDF with headers and footers created at: {os.path.abspath(output_path)}")
        return output_path
    
    def create_multi_page_pdf(self, output_filename="multi_page_report.pdf"):
        """
        Create a multi-page PDF document
        
        Args:
            output_filename: Name of the output PDF file
            
        Returns:
            Path to the created PDF file
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Add content for multiple pages
        for i in range(1, 6):  # Create 5 pages
            elements.append(Paragraph(f"Page {i}", styles["Heading1"]))
            elements.append(Spacer(1, 12))
            
            # Add some sample text
            text = f"""
            This is page {i} of the multi-page PDF document.
            Each page can have different content and layout.
            """
            elements.append(Paragraph(text, styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            # Add a page break after each page (except the last one)
            if i < 5:
                elements.append(PageBreak())
        
        # Build the PDF
        doc.build(elements)
        
        logger.info(f"Multi-page PDF created at: {os.path.abspath(output_path)}")
        return output_path
    
    def create_purchase_request_pdf(self, request_data=sample_request, output_filename=None):
        """
        Create a PDF for a purchase request
        
        Args:
            request_data: Dictionary containing purchase request data
            output_filename: Name of the output PDF file (optional)
            
        Returns:
            Path to the created PDF file
        """
        if output_filename is None:
            # Generate a filename based on the request ID
            request_id = request_data.get('ID', 'unknown')
            output_filename = f"purchase_request_{request_id}.pdf"
        
        output_path = os.path.join(self.output_dir, output_filename)
        self._add_BKSEAL_to_pdf(self.seal_img, output_path)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        subtitle_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        # Add a title
        title = Paragraph("Purchase Request", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Add request details
        elements.append(Paragraph(f"Request ID: {request_data.get('ID', 'N/A')}", normal_style))
        elements.append(Paragraph(f"Requester: {request_data.get('requester', 'N/A')}", normal_style))
        elements.append(Paragraph(f"Date Requested: {request_data.get('datereq', 'N/A')}", normal_style))
        elements.append(Paragraph(f"Date Needed: {request_data.get('dateneed', 'N/A')}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Add item details
        elements.append(Paragraph("Item Details", subtitle_style))
        elements.append(Spacer(1, 6))
        
        # Create a table for item details
        data = [
            ["Description", "Quantity", "Price Each", "Total Price"],
            [
                request_data.get('itemDescription', 'N/A'),
                str(request_data.get('quantity', 'N/A')),
                f"${request_data.get('priceEach', '0.00')}",
                f"${request_data.get('totalPrice', '0.00')}"
            ]
        ]
        
        table = Table(data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 12))
        
        # Add budget information
        elements.append(Paragraph("Budget Information", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"Budget Object Code: {request_data.get('budgetObjCode', 'N/A')}", normal_style))
        elements.append(Paragraph(f"Fund: {request_data.get('fund', 'N/A')}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Add justification
        elements.append(Paragraph("Justification", subtitle_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(request_data.get('justification', 'N/A'), normal_style))
        elements.append(Spacer(1, 12))
        
        # Add additional comments if any
        if request_data.get('addComments'):
            elements.append(Paragraph("Additional Comments", subtitle_style))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(request_data.get('addComments', ''), normal_style))
            elements.append(Spacer(1, 12))
        
        # Add status
        elements.append(Paragraph(f"Status: {request_data.get('status', 'N/A')}", normal_style))
        
        # Build the PDF
        doc.build(elements)
        
        logger.info(f"Purchase request PDF created at: {os.path.abspath(output_path)}")
        return output_path

# Example usage
if __name__ == "__main__":
    # Create an instance of the PDF service
    pdf_service = PDFService()
    
    # Create a basic PDF
    pdf_service.create_pdf()
    
    # Create a multi-page PDF
    pdf_service.create_multi_page_pdf()
    
    # Create a PDF with headers and footers
    pdf_service.create_pdf_with_header_footer()
    
    # Create a sample purchase request PDF
    
    pdf_service.create_purchase_request_pdf(sample_request)