from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

def generate_receipt_pdf(order):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.7*inch, leftMargin=0.7*inch, topMargin=0.7*inch, bottomMargin=0.7*inch)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#2ecc71'),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=10,
        spaceBefore=12
    )
    
    product_style = ParagraphStyle(
        'ProductStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.black,
        alignment=TA_LEFT,
        leading=14,
    )
    
    content = []
    
    content.append(Paragraph("Oraimo Tech Hub", title_style))
    content.append(Paragraph("Premium Oraimo Products - Kenya", subtitle_style))
    content.append(Spacer(1, 5))
    content.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2ecc71')))
    content.append(Spacer(1, 15))
    content.append(Paragraph(f"ORDER RECEIPT - {order.order_id}", section_style))
    content.append(Spacer(1, 10))
    
    order_data = [
        ['Date:', order.created_at.strftime('%B %d, %Y at %I:%M %p'), 'Customer:', order.customer_name],
        ['Phone:', order.customer_phone, 'Email:', order.customer_email or 'Not provided'],
        ['Delivery Location:', order.delivery_location, 'Address:', order.delivery_address],
        ['Payment Status:', order.payment_status.replace('_', ' ').title(), 'Delivery Status:', order.delivery_status.replace('_', ' ').title()],
    ]
    
    order_table = Table(order_data, colWidths=[1.2*inch, 2.4*inch, 1.2*inch, 2.4*inch])
    order_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (2, -1), colors.HexColor('#4a1d6d')),
        ('TEXTCOLOR', (1, 0), (3, -1), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    content.append(order_table)
    content.append(Spacer(1, 20))
    
    content.append(Paragraph("Items Ordered", section_style))
    content.append(Spacer(1, 8))
    
    item_data = [['#', 'Product', 'Qty', 'Price', 'Total']]
    for idx, item in enumerate(order.items.all(), 1):
        product_name = Paragraph(str(item.product_name), product_style)
        item_data.append([
            str(idx),
            product_name,
            str(item.quantity),
            f"KES {item.price:.2f}",
            f"KES {item.total:.2f}"
        ])
    
    item_table = Table(item_data, colWidths=[0.4*inch, 4.0*inch, 0.6*inch, 1.2*inch, 1.5*inch])
    item_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    content.append(item_table)
    content.append(Spacer(1, 20))
    
    total_data = [
        ['', 'Subtotal:', f"KES {order.subtotal:.2f}"],
        ['', 'Delivery Fee:', f"KES {order.delivery_fee:.2f}"],
        ['', 'TOTAL:', f"KES {order.total_amount:.2f}"],
    ]
    total_table = Table(total_data, colWidths=[4.0*inch, 1.5*inch, 1.5*inch])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    total_table.setStyle(TableStyle([
        ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
        ('FONTNAME', (2, 2), (2, 2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2, 2), (2, 2), colors.HexColor('#2ecc71')),
        ('FONTSIZE', (1, 2), (2, 2), 16),
        ('TOPPADDING', (0, 2), (-1, 2), 10),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 10),
    ]))
    content.append(total_table)
    content.append(Spacer(1, 25))
    
    content.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2ecc71')))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Thank you for shopping with Oraimo Tech Hub!", styles['Normal']))
    content.append(Paragraph("We are an online supplier of genuine Oraimo products in Kenya.", styles['Normal']))
    content.append(Spacer(1, 6))
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    
    doc.build(content)
    buffer.seek(0)
    
    return buffer