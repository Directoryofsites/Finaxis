import sys
import os

# Añadir el raíz del proyecto al sys.path para poder importar módulos de la app
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

import pdfplumber

def test_pdf_extraction(file_path):
    print(f"Probando la extracción del archivo PDF: {file_path}")
    if not os.path.exists(file_path):
        print("Error: El archivo no existe.")
        return

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"Total de páginas: {len(pdf.pages)}")
            
            for i, page in enumerate(pdf.pages):
                if i >= 2: # Solo mostrar primeras páginas por brevedad
                    print("...Más páginas omitidas...")
                    break
                    
                print(f"\n--- Página {i+1} ---")
                
                # Intentar extraer tablas
                tables = page.extract_tables()
                if tables:
                    print(f"Se encontraron {len(tables)} tabla(s).")
                    for t_idx, table in enumerate(tables):
                        print(f"  Tabla {t_idx+1}:")
                        # Mostrar las primeras 5 filas
                        for r_idx, row in enumerate(table[:5]):
                            # Limpiar Nones para visualización
                            cleaned_row = [str(cell).replace('\\n', ' ') if cell else "" for cell in row]
                            print(f"    Fila {r_idx+1}: {cleaned_row}")
                        if len(table) > 5:
                            print(f"    ... y {len(table) - 5} filas más.")
                else:
                    print("No se encontraron tablas estructuradas en esta página.")
                
                print("\nTexto plano de la página (primeros 300 caracteres):")
                text = page.extract_text()
                if text:
                    print(text[:300] + "...")
                else:
                    print("No se encontró texto extraíble.")

    except Exception as e:
        print(f"Ocurrió un error al procesar el PDF: {e}")

if __name__ == "__main__":
    if len(sys.path) > 1 and len(sys.argv) > 1:
        test_pdf_extraction(sys.argv[1])
    else:
        print("Uso: python test_pdf_extract.py <ruta_al_pdf>")
        print("\nEjemplo: python test_pdf_extract.py c:\\ContaPY2\\test_data\\mi_extracto.pdf")
