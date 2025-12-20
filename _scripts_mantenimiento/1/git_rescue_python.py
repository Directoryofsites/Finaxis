#!/usr/bin/env python3
"""
Script de rescate para subir el módulo de Conciliación Bancaria a GitHub
Evita problemas con el paginador de Git
"""

import subprocess
import os
import sys

def run_git_command(command, check_output=False):
    """Ejecuta un comando git sin paginador"""
    env = os.environ.copy()
    env['GIT_PAGER'] = ''
    env['LESS'] = ''
    
    try:
        if check_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            result = subprocess.run(command, shell=True, env=env)
            return result.returncode
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        return None

def main():
    print("=== PROTOCOLO DE RESCATE KIRO - PYTHON ===")
    
    # 1. Configurar Git sin paginador
    print("1. Configurando Git sin paginador...")
    run_git_command('git config --local core.pager ""')
    
    # 2. Verificar rama actual
    print("2. Verificando rama actual...")
    stdout, stderr, code = run_git_command('git branch --show-current', check_output=True)
    if code == 0:
        print(f"   Rama actual: {stdout}")
    else:
        print(f"   Error: {stderr}")
    
    # 3. Cambiar a kiro-rama
    print("3. Cambiando a kiro-rama...")
    code = run_git_command('git checkout kiro-rama')
    if code == 0:
        print("   ✓ Cambiado a kiro-rama")
    else:
        print("   ✗ Error cambiando de rama")
        return
    
    # 4. Verificar estado
    print("4. Verificando estado de archivos...")
    stdout, stderr, code = run_git_command('git status --porcelain', check_output=True)
    if code == 0:
        lines = stdout.split('\n') if stdout else []
        print(f"   Archivos modificados: {len([l for l in lines if l.strip()])}")
        if len(lines) > 0:
            print("   Primeros archivos:")
            for line in lines[:5]:
                if line.strip():
                    print(f"     {line}")
    
    # 5. Agregar archivos (excluyendo .env)
    print("5. Agregando archivos...")
    run_git_command('git add .')
    run_git_command('git reset HEAD .env')
    print("   ✓ Archivos agregados (excluyendo .env)")
    
    # 6. Verificar cambios preparados
    print("6. Verificando cambios preparados...")
    stdout, stderr, code = run_git_command('git status --porcelain --cached', check_output=True)
    if code == 0:
        lines = stdout.split('\n') if stdout else []
        print(f"   Archivos preparados para commit: {len([l for l in lines if l.strip()])}")
    
    # 7. Hacer commit
    print("7. Haciendo commit...")
    code = run_git_command('git commit -m "feat(conciliacion): Modulo completo y optimizaciones (Rescate version Kiro)"')
    if code == 0:
        print("   ✓ Commit realizado exitosamente")
    else:
        print("   ⚠ Posible commit ya existente o sin cambios")
    
    # 8. Subir a GitHub
    print("8. Subiendo a GitHub...")
    stdout, stderr, code = run_git_command('git push origin kiro-rama', check_output=True)
    if code == 0:
        print("   ✓ Push exitoso!")
        print(f"   Salida: {stdout}")
    else:
        print(f"   ✗ Error en push: {stderr}")
        return
    
    print("\n=== RESCATE COMPLETADO EXITOSAMENTE ===")
    print("El módulo de Conciliación Bancaria ha sido subido a GitHub en la rama kiro-rama")

if __name__ == "__main__":
    main()