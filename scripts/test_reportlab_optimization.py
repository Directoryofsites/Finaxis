import time
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import random
from datetime import datetime

def generate_large_report_poc(filename="test_reportlab_500pag.pdf", num_records=10000):
    print(f"--- Iniciando Generación PDF con ReportLab ({num_records} registros) ---")
    start_time = time.time()

    doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    # Título
    elements.append(Paragraph(f"Super Informe de Inventario - Test de Carga ({num_records} items)", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    # Datos Simulados
    data = [['Fecha', 'Documento', 'Referencia', 'Tercero', 'Bodega', 'Producto', 'Cant.', 'Costo Unit.', 'Total']]
    
    print(f"Generando {num_records} registros simulados...")
    for i in range(num_records):
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            f"FV-{i}",
            f"REF-{random.randint(1000, 9999)}",
            f"Cliente Simulado {random.randint(1, 100)}",
            "Bodega Principal",
            f"Producto de Prueba {i}",
            f"{random.randint(1, 100)}",
            f"${random.randint(1000, 50000):,}",
            f"${random.randint(50000, 500000):,}"
        ]
        data.append(row)

    print("Construyendo tabla...")
    # Table config
    col_widths = [1*inch, 1*inch, 1*inch, 2*inch, 1.5*inch, 2.5*inch, 0.8*inch, 1*inch, 1.2*inch]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(t)

    print("Renderizando PDF...")
    doc.build(elements)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"--- FIN: PDF Generado en {duration:.2f} segundos ---")
    print(f"Archivo: {filename}")

if __name__ == "__main__":
    # Simulamos 5000 registros (aprox 150-200 páginas)
    generate_large_report_poc(num_records=5000)
