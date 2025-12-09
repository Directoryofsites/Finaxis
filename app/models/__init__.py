# app/models/__init__.py (Versión con Nueva Arquitectura Inventario)

# --- Orden Arquitectónico ---
from .permiso import Rol, Permiso, UsuarioPermisoExcepcion, usuario_roles, rol_permisos
# --- Fin Orden ---

from .usuario_favorito import UsuarioFavorito # <--- ¡EL ESLABÓN PERDIDO!

from .usuario import Usuario



from .empresa import Empresa
from .tercero import Tercero
from .plan_cuenta import PlanCuenta
from .tipo_documento import TipoDocumento
from .centro_costo import CentroCosto
from .plantilla_maestra import PlantillaMaestra
from .plantilla_detalle import PlantillaDetalle
from .concepto_favorito import ConceptoFavorito
from .documento import Documento, DocumentoEliminado
from .movimiento_contable import MovimientoContable, MovimientoEliminado
from .log_operacion import LogOperacion
from .periodo_contable_cerrado import PeriodoContableCerrado
from .formato_impresion import FormatoImpresion
from .aplicacion_pago import AplicacionPago
from .bodega import Bodega
# --- INICIO NUEVAS IMPORTACIONES (ORDENADAS) ---
from .lista_precio import ListaPrecio # Listas globales
from .grupo_inventario import GrupoInventario # Grupos dependen de Cuentas, Impuestos
from .impuesto import TasaImpuesto
from .caracteristica_definicion import CaracteristicaDefinicion # Definición depende de Grupo
from .regla_precio_grupo import ReglaPrecioGrupo # Regla depende de Grupo y ListaPrecio
from .producto import Producto, StockBodega, MovimientoInventario # Producto depende de Grupo, Impuesto
from .caracteristica_valor_producto import CaracteristicaValorProducto # Valor depende de Producto y Definición
# --- FIN NUEVAS IMPORTACIONES ---

# --- CAMBIO: Eliminada importación ---
# from .precio_producto import PrecioProducto

from .cupo_adicional import CupoAdicional
from .remision import Remision, RemisionDetalle
# --- COTIZACIONES (Nuevo Modulo) ---
from .cotizacion import Cotizacion, CotizacionDetalle

# --- ACTIVOS FIJOS (Nuevo Modulo) ---
from .activo_categoria import ActivoCategoria
from .activo_fijo import ActivoFijo
from .activo_novedad import ActivoNovedad

from .configuracion_reporte import ConfiguracionReporte

# --- PROPIEDAD HORIZONTAL (Nuevo Módulo) ---
from .propiedad_horizontal import PHTorre, PHUnidad, PHVehiculo, PHMascota
