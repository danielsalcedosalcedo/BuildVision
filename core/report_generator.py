"""
BuildVision AI - Generador de Reporte Semanal en PDF (RF-08, Pantalla 7d)
Genera documento ejecutivo formal con ReportLab:
- Resumen ejecutivo y KPIs de avance real vs plan
- Tabla de pesos y avance por componente (Fórmula Sección 5)
- Desglose por vanos y alertas de desviación
- Registro de auditoría HITL y estado de firma electrónica
"""
import io
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

def generate_weekly_pdf_report(
    project_name: str,
    level_name: str,
    week_number: int,
    ito_name: str,
    level_data: Dict[str, Any],
    audit_logs: List[Dict[str, Any]],
    notes: str = ""
) -> bytes:
    """
    Genera el archivo PDF binario en memoria usando ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Estilos tipográficos modernos
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A')
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    section_h2 = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # 1. ENCABEZADO INSTITUCIONAL
    header_table_data = [
        [
            Paragraph("<b>BUILDVISION AI</b><br/><font color='#64748B' size='8'>Monitoreo de Avance Físico con Visión Computacional · AEC + IA</font>", title_style),
            Paragraph(f"<b>REPORTE SEMANAL #{week_number}</b><br/>Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>Versión: 1.0 (MVP)", subtitle_style)
        ]
    ]
    header_table = Table(header_table_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284C7'), spaceBefore=4, spaceAfter=12))

    # 2. METADATOS DE LA INSPECCIÓN
    meta_data = [
        [
            Paragraph(f"<b>Proyecto:</b> {project_name}", table_cell),
            Paragraph(f"<b>Sector / Nivel:</b> {level_name}", table_cell),
        ],
        [
            Paragraph(f"<b>Partida ancla:</b> Red de rociadores contra incendio (PCI)", table_cell),
            Paragraph(f"<b>Inspector Técnico de Obra (ITO):</b> {ito_name}", table_cell)
        ],
        [
            Paragraph(f"<b>Fuente de conteo:</b> Modelo, JSON o conteo manual", table_cell),
            Paragraph(f"<b>Validación:</b> Revisión Human-in-the-Loop (HITL)", table_cell)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. RESUMEN EJECUTIVO (KPIs)
    zones = level_data.get('zones', [])
    level_pct = level_data.get('level_progress_pct', 0.0)
    total_plan_units = sum(z.get('plan_units_total', 0) for z in zones)
    plan_pct = (
        sum(z.get('plan_week_pct', 0.0) * z.get('plan_units_total', 0) for z in zones) / total_plan_units
        if total_plan_units else 0.0
    )
    deviation = round(level_pct - plan_pct, 1)
    inspected_zones = level_data.get('inspected_zones_this_session', 0)

    kpi_color = colors.HexColor('#059669') if deviation >= -5.0 else colors.HexColor('#DC2626')
    review_color = colors.HexColor('#059669') if inspected_zones else colors.HexColor('#D97706')

    kpi_data = [
        [
            Paragraph(f"<b>AVANCE PONDERADO</b><br/><font size='16' color='#0F172A'><b>{level_pct:.1f}%</b></font>", table_cell_bold),
            Paragraph(f"<b>PLAN DE LA SEMANA</b><br/><font size='16' color='#475569'><b>{plan_pct:.1f}%</b></font>", table_cell_bold),
            Paragraph(f"<b>DESVIACIÓN</b><br/><font size='16' color='{kpi_color.hexval()}'><b>{deviation:+.1f} pp</b></font>", table_cell_bold),
            Paragraph(f"<b>ZONAS INSPECCIONADAS</b><br/><font size='16' color='{review_color.hexval()}'><b>{inspected_zones}</b></font>", table_cell_bold)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94A3B8')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # 4. TABLA DE AVANCE POR ELEMENTO / ZONA
    story.append(Paragraph("1. Desglose de Avance Físico por Elemento / Zona", section_h2))
    
    zones_rows = [
        [
            Paragraph("<b>Elemento / Zona</b>", table_cell_bold),
            Paragraph("<b>Avance Real</b>", table_cell_bold),
            Paragraph("<b>Meta Plan</b>", table_cell_bold),
            Paragraph("<b>Desviación</b>", table_cell_bold),
            Paragraph("<b>Cobertura</b>", table_cell_bold),
            Paragraph("<b>Semáforo</b>", table_cell_bold)
        ]
    ]

    for z in zones:
        dev = z['deviation_pp']
        status = z['alert_status']
        zones_rows.append([
            Paragraph(f"<b>{z['name']}</b>", table_cell),
            Paragraph(f"{z['progress_pct']:.1f}%", table_cell_bold),
            Paragraph(f"{z['plan_week_pct']:.1f}%", table_cell),
            Paragraph(f"{dev:+.1f} pp", table_cell),
            Paragraph(f"{z['coverage']}", table_cell),
            Paragraph(f"<b>{status}</b>", table_cell_bold)
        ])

    zones_table = Table(zones_rows, colWidths=[110, 85, 85, 85, 85, 90])
    zones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(zones_table)
    story.append(Spacer(1, 10))

    # 5. DESGLOSE DE LA PRIMERA ZONA POR COMPONENTE
    detail_zone = zones[0] if zones else None
    if detail_zone is not None:
        story.append(Paragraph(f"2. Detalle de Ponderación por Componente ({detail_zone['name']})", section_h2))
    comp_rows = [
        [
            Paragraph("<b>Componente PCI</b>", table_cell_bold),
            Paragraph("<b>Peso w</b>", table_cell_bold),
            Paragraph("<b>Validado ÷ Plan</b>", table_cell_bold),
            Paragraph("<b>Ratio p(c,z)</b>", table_cell_bold),
            Paragraph("<b>Aporte w·p</b>", table_cell_bold)
        ]
    ]
    if detail_zone is not None:
        for component in detail_zone['components']:
            comp_rows.append([
                Paragraph(component['name'], table_cell),
                Paragraph(f"{component['weight']:.2f}", table_cell),
                Paragraph(f"{component['validated']} ÷ {component['plan']}", table_cell),
                Paragraph(f"{component['ratio_p']:.3f}", table_cell),
                Paragraph(f"{component['contribution']:.4f}", table_cell_bold)
            ])
        comp_rows.append([
            Paragraph(f"<b>TOTAL AVANCE {detail_zone['name']}</b>", table_cell_bold),
            Paragraph("<b>1.00</b>", table_cell_bold),
            Paragraph("-", table_cell_bold),
            Paragraph("-", table_cell),
            Paragraph(f"<b>{detail_zone['progress_pct']:.1f}%</b>", table_cell_bold)
        ])
        comp_table = Table(comp_rows, colWidths=[180, 70, 110, 80, 100])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FEF9C3')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 10))

    # 6. OBSERVACIONES Y ALERTAS
    story.append(Paragraph("3. Registro de Hallazgos y Alertas de Desviación", section_h2))
    alerts = [z for z in zones if z['alert_status'] in ('CRÍTICA', 'DESVIACIÓN')]
    alert_text = (
        "<br/>".join(
            f"• <b>{z['name']} · {z['alert_status']} ({z['deviation_pp']:+.1f} pp):</b> "
            f"avance {z['progress_pct']:.1f}% frente al plan {z['plan_week_pct']:.1f}%."
            for z in alerts
        )
        if alerts else "No hay desviaciones respecto a la meta semanal en los datos incluidos."
    )
    if level_data.get('uses_sample_data'):
        alert_text += "<br/><b>Nota:</b> Las zonas no inspeccionadas contienen datos de demostración."
    if notes:
        alert_text += f"<br/>• <b>Comentario del ITO:</b> {notes}"

    alert_box = Table([[Paragraph(alert_text, table_cell)]], colWidths=[540])
    alert_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(alert_box)
    story.append(Spacer(1, 14))

    # 7. REGISTRO DE AUDITORÍA Y RESPONSABLE
    story.append(Paragraph("4. Registro de auditoría", section_h2))
    if audit_logs:
        audit_rows = [[
            Paragraph("<b>Fecha</b>", table_cell_bold),
            Paragraph("<b>Usuario</b>", table_cell_bold),
            Paragraph("<b>Acción</b>", table_cell_bold),
            Paragraph("<b>Zona / componente</b>", table_cell_bold),
            Paragraph("<b>Valor</b>", table_cell_bold)
        ]]
        for entry in audit_logs:
            audit_rows.append([
                Paragraph(str(entry.get('timestamp', '')), table_cell),
                Paragraph(str(entry.get('user', '')), table_cell),
                Paragraph(str(entry.get('action', '')), table_cell),
                Paragraph(f"{entry.get('zone_id', '')} / {entry.get('component', '')}", table_cell),
                Paragraph(f"{entry.get('old_value', '')} -> {entry.get('new_value', '')}", table_cell)
            ])
        audit_table = Table(audit_rows, colWidths=[85, 100, 110, 140, 105], repeatRows=1)
        audit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]))
        story.append(audit_table)
    else:
        story.append(Paragraph("No hay acciones registradas en esta sesión.", table_cell))
    story.append(Spacer(1, 8))
    story.append(Paragraph("5. Responsable y estado de firma", section_h2))
    
    sign_data = [
        [
            Paragraph(f"<b>Responsable indicado</b><br/><b>{ito_name}</b><br/>La firma electrónica no está implementada.", table_cell),
            Paragraph("<b>VoBo de obra</b><br/>Pendiente de firma y aprobación externa.", table_cell)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[270, 270])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(KeepTogether([sign_table]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
