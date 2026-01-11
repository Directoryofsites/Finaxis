# app/schemas/__init__.py (Versión Corregida: Eliminar el import conflictivo)

# Importaciones de módulos existentes (reconstrucción de la estructura de ContaPY)
from . import aplicacion_pago
from . import auditoria
from . import bodega
from . import cartera
from . import centro_costo
from . import compras
# REMOVIDA: from . import concepto_favorito <--- ¡ESTA LÍNEA DEBE SER ELIMINADA!
from . import diagnostico
from . import documento
from . import empresa
from . import facturacion
from . import formato_impresion
from . import gestion_ventas
from . import inventario
from . import migracion
from . import papelera
from . import periodo
from . import plan_cuenta
from . import plantilla
from . import recodificacion
from . import reporte_balance_prueba
from . import reporte_rentabilidad
from . import reportes_facturacion
from . import reportes_inventario
from . import rol
from . import soporte
from . import tercero
from . import tipo_documento
from . import token
from . import usuario
from . import traslado_inventario
from . import conciliacion_bancaria

# --- RESOLUCIÓN DE REFERENCIAS CIRCULARES (PYDANTIC V2) ---
# Es necesario reconstruir los modelos que tienen referencias cruzadas (Lazy Imports)
# para que Pydantic pueda resolver los tipos correctamente en tiempo de ejecución.
# Pasamos _types_namespace porque al usar TYPE_CHECKING, los tipos no están en el global del módulo.
usuario.User.model_rebuild(_types_namespace={'EmpresaBase': empresa.EmpresaBase})
# NOTA: EmpresaConUsuarios ahora usa 'UserBasic', no 'User'. 'UserBasic' no tiene referencia circular a 'Empresa'.
# Sin embargo, si 'User' hereda de 'UserBasic', el string 'UserBasic' debe estar disponible.
# Como ambos están en el mismo archivo 'usuario.py' y se importan, suele funcionar,
# pero para estar seguros pasamos el namespace correcto.
empresa.EmpresaConUsuarios.model_rebuild(_types_namespace={'UserBasic': usuario.UserBasic})
