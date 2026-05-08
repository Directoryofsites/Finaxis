"""
test_pyarmor.py
Prueba que PyArmor puede ofuscar los archivos críticos de Finaxis.
Ejecutar: python instalador/test_pyarmor.py
"""
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
CORE = ROOT / "app" / "core"
OUT  = ROOT / "instalador" / "_test_pyarmor_out"

# Archivos a probar (los más críticos y pequeños)
ARCHIVOS_CRITICOS = [
    CORE / "licencia.py",
    CORE / "security.py",
    CORE / "database.py",
    CORE / "hashing.py",
    CORE / "config.py",
    CORE / "security_encryption.py",
    CORE / "constants.py",
]

print("=" * 55)
print("  TEST: PyArmor Trial — Archivos Críticos de Finaxis")
print("=" * 55)

resultados = []

for archivo in ARCHIVOS_CRITICOS:
    if not archivo.exists():
        resultados.append((archivo.name, "NO EXISTE", 0))
        continue

    kb = archivo.stat().st_size / 1024
    out_dir = OUT / archivo.stem

    resultado = subprocess.run(
        ["pyarmor", "gen", "--output", str(out_dir), str(archivo)],
        capture_output=True, text=True
    )

    if resultado.returncode == 0:
        status = "[OK] OFUSCADO"
    elif "big script" in resultado.stderr.lower() or "too large" in resultado.stderr.lower():
        status = "[--] MUY GRANDE (Trial)"
    else:
        status = "[!!] ERROR"

    resultados.append((archivo.name, status, kb))

# Limpiar directorio de prueba
import shutil
if OUT.exists():
    shutil.rmtree(OUT)

# Mostrar resultados
print(f"\n{'Archivo':<30} {'Tamaño':>8}   {'Resultado'}")
print("-" * 60)
for nombre, status, kb in resultados:
    print(f"  {nombre:<28} {kb:>6.1f}KB   {status}")

print()
aptos = [r for r in resultados if "OFUSCADO" in r[1]]
no_aptos = [r for r in resultados if "GRANDE" in r[1]]
errores = [r for r in resultados if "ERROR" in r[1]]

print(f"  Listos para PyArmor:    {len(aptos)}/{len(resultados)}")
print(f"  Muy grandes (Trial):    {len(no_aptos)}/{len(resultados)}")
if errores:
    print(f"  Con error:              {len(errores)}/{len(resultados)}")

print()
if aptos:
    print("[OK] Los archivos marcados se ofuscaran en el build del instalador.")
if no_aptos:
    print("[->] Los archivos 'MUY GRANDE' se protegen con bytecode .pyc + PyInstaller.")
print()
print("Para ofuscar TODOS los archivos, adquiere la licencia de PyArmor.")
print("  Precio: ~$50 USD | https://pyarmor.readthedocs.io/en/latest/licenses.html")
