# app/core/constants.py

class FuncionEspecial:
    """
    Define los identificadores únicos y estandarizados para las funciones especiales
    de los tipos de documento. Elimina el uso de 'magic strings' en el código.
    """
    # Módulo de Cartera (Cuentas por Cobrar)
    CARTERA_CLIENTE = 'cartera_cliente'  # Para Facturas de Venta
    RC_CLIENTE = 'rc_cliente'          # Para Recibos de Caja

    # Módulo de Proveedores (Cuentas por Pagar)
    CXP_PROVEEDOR = 'cxp_proveedor'    # Para Facturas de Compra
    PAGO_PROVEEDOR = 'pago_proveedor'  # Para Comprobantes de Egreso