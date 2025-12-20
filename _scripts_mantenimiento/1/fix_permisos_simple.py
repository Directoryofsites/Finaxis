#!/usr/bin/env python3
"""
Script simple para crear permisos de conciliación bancaria
"""

import os
import sys

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Leer configuración de base de datos desde .env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Construir URL de base de datos
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'contapy_db')
    
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print("🔧 CREANDO PERMISOS DE CONCILIACIÓN BANCARIA")
    print("=" * 50)
    
    # Crear conexión
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # SQL para crear permisos
    permisos_sql = """
    INSERT INTO permisos (nombre, descripcion) VALUES 
    ('conciliacion_bancaria:ver', 'Ver el módulo de conciliación bancaria y sus datos.'),
    ('conciliacion_bancaria:configurar', 'Configurar importaciones y cuentas contables para conciliación.'),
    ('conciliacion_bancaria:importar', 'Importar extractos bancarios y validar archivos.'),
    ('conciliacion_bancaria:conciliar', 'Realizar conciliaciones manuales y automáticas.'),
    ('conciliacion_bancaria:ajustar', 'Generar y aplicar ajustes automáticos.'),
    ('conciliacion_bancaria:reportes', 'Ver y exportar reportes de conciliación.'),
    ('conciliacion_bancaria:auditoria', 'Ver auditoría y actividad sospechosa en conciliaciones.')
    ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);
    """
    
    # Ejecutar creación de permisos
    session.execute(text(permisos_sql))
    session.commit()
    print("✅ Permisos creados/actualizados")
    
    # Verificar permisos creados
    result = session.execute(text("SELECT COUNT(*) as total FROM permisos WHERE nombre LIKE 'conciliacion_bancaria:%'"))
    total_permisos = result.fetchone()[0]
    print(f"📊 Total permisos de conciliación: {total_permisos}")
    
    # Asignar permisos al rol Administrador
    asignar_sql = """
    INSERT INTO rol_permisos (rol_id, permiso_id)
    SELECT r.id, p.id 
    FROM roles r, permisos p 
    WHERE r.nombre = 'Administrador' 
    AND p.nombre LIKE 'conciliacion_bancaria:%'
    AND NOT EXISTS (
        SELECT 1 FROM rol_permisos rp 
        WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
    );
    """
    
    session.execute(text(asignar_sql))
    session.commit()
    print("✅ Permisos asignados al rol Administrador")
    
    # Verificar asignación
    result = session.execute(text("""
        SELECT COUNT(*) as total
        FROM rol_permisos rp
        JOIN roles r ON rp.rol_id = r.id
        JOIN permisos p ON rp.permiso_id = p.id
        WHERE r.nombre = 'Administrador'
        AND p.nombre LIKE 'conciliacion_bancaria:%'
    """))
    total_asignados = result.fetchone()[0]
    print(f"📊 Permisos asignados al Administrador: {total_asignados}")
    
    # Verificar usuarios con rol Administrador
    result = session.execute(text("""
        SELECT u.nombre, u.email
        FROM usuarios u
        JOIN usuario_roles ur ON u.id = ur.usuario_id
        JOIN roles r ON ur.rol_id = r.id
        WHERE r.nombre = 'Administrador'
    """))
    usuarios_admin = result.fetchall()
    
    print(f"\n👥 Usuarios con rol Administrador: {len(usuarios_admin)}")
    for usuario in usuarios_admin:
        print(f"   • {usuario[0]} ({usuario[1]})")
    
    session.close()
    
    print("\n" + "=" * 50)
    print("🎉 ¡PERMISOS CONFIGURADOS EXITOSAMENTE!")
    print("=" * 50)
    print("🚀 Próximos pasos:")
    print("   1. Recargar la página del módulo")
    print("   2. Verificar que desaparece el error 403")
    print("   3. Probar ajustes automáticos")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Instala las dependencias: pip install sqlalchemy pymysql python-dotenv")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()