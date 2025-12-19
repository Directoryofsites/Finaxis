#!/usr/bin/env python3
"""
Script para actualizar los permisos en las rutas de conciliación bancaria
"""

import re

def update_permissions():
    """Actualiza los permisos en el archivo de rutas"""
    
    # Leer el archivo
    with open("app/api/conciliacion_bancaria/routes.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Definir los reemplazos de permisos
    permission_mappings = [
        # Configuraciones - requieren permiso de configurar
        (r'(async def create_import_config.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar"))'),
        (r'(async def update_import_config.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar"))'),
        (r'(async def delete_import_config.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar"))'),
        (r'(async def save_configuration.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar"))'),
        (r'(async def create_accounting_configuration.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar"))'),
        (r'(async def delete_accounting_configuration.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar"))'),
        
        # Importación - requieren permiso de importar
        (r'(async def validate_file.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:importar"))'),
        (r'(async def import_file.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:importar"))'),
        (r'(async def confirm_import.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:importar"))'),
        
        # Conciliación - requieren permiso de conciliar
        (r'(async def create_manual_reconciliation.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:conciliar"))'),
        (r'(async def reverse_reconciliation.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:conciliar"))'),
        (r'(async def create_reconciliation.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:conciliar"))'),
        
        # Ajustes - requieren permiso de ajustar
        (r'(async def generate_adjustments.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:ajustar"))'),
        (r'(async def apply_adjustments.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:ajustar"))'),
        (r'(async def preview_single_adjustment.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:ajustar"))'),
        
        # Reportes - requieren permiso de ver reportes
        (r'(async def get_reconciliation_report.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:reportes"))'),
        (r'(async def export_reconciliation_report.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:reportes"))'),
        
        # Auditoría - requieren permiso de auditoría
        (r'(async def get_audit_trail.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria"))'),
        (r'(async def get_reconciliation_audit_trail.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria"))'),
        (r'(async def report_suspicious_activity.*?)current_user: Usuario = Depends\(get_current_user\)', 
         r'\1current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria"))'),
    ]
    
    # Aplicar los reemplazos
    for pattern, replacement in permission_mappings:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Escribir el archivo actualizado
    with open("app/api/conciliacion_bancaria/routes.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Permisos actualizados en las rutas de conciliación bancaria")

if __name__ == "__main__":
    update_permissions()