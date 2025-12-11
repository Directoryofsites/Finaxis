import json
import hmac
import hashlib
import sys
import os
from datetime import datetime

# Add project root to path to import config
sys.path.append(os.getcwd())
from app.core.config import settings

# =============================================================================
# DEFINICIÓN DEL PUC COMERCIAL (COLOMBIA) - VERSIÓN EXTENDIDA
# =============================================================================
CUENTAS_BASE = [
    # CLASE 1: ACTIVO
    ("1", "ACTIVO", 1),
    ("11", "DISPONIBLE", 2),
    ("1105", "CAJA", 3),
    ("110505", "CAJA GENERAL", 4),
    ("110510", "CAJAS MENORES", 4),
    ("110515", "MONEDA EXTRANJERA", 4),
    ("1110", "BANCOS", 3),
    ("111005", "MONEDA NACIONAL", 4),
    ("111010", "MONEDA EXTRANJERA", 4),
    ("1120", "CUENTAS DE AHORRO", 3),
    ("112005", "BANCOS", 4),
    ("112010", "CORPORACIONES DE AHORRO Y VIVIENDA", 4),
    ("12", "INVERSIONES", 2),
    ("1205", "ACCIONES", 3),
    ("120505", "AGRICULTURA, GANADERIA, CAZA Y SILVICULTURA", 4),
    ("120510", "PESCA", 4),
    ("120515", "EXPLOTACION DE MINAS Y CANTERAS", 4),
    ("120520", "INDUSTRIA MANUFACTURERA", 4),
    ("120525", "SUMINISTRO DE ELECTRICIDAD, GAS Y AGUA", 4),
    ("120530", "CONSTRUCCION", 4),
    ("120535", "COMERCIO AL POR MAYOR Y AL POR MENOR", 4),
    ("120540", "HOTELES Y RESTAURANTES", 4),
    ("120545", "TRANSPORTE, ALMACENAMIENTO Y COMUNICACIONES", 4),
    ("120550", "INTERMEDIACION FINANCIERA", 4),
    ("120555", "ACTIVIDADES INMOBILIARIAS", 4),
    ("120560", "ENSEÑANZA", 4),
    ("120565", "SERVICIOS SOCIALES Y DE SALUD", 4),
    ("120570", "OTRAS ACTIVIDADES DE SERVICIOS COMUNITARIOS", 4),
    ("13", "DEUDORES", 2),
    ("1305", "CLIENTES", 3),
    ("130505", "NACIONALES", 4),
    ("130510", "DEL EXTERIOR", 4),
    ("130515", "DEUDORES DEL SISTEMA", 4),
    ("1325", "CUENTAS POR COBRAR A SOCIOS Y ACCIONISTAS", 3),
    ("132505", "A SOCIOS", 4),
    ("132510", "A ACCIONISTAS", 4),
    ("1330", "ANTICIPOS Y AVANCES", 3),
    ("133005", "A PROVEEDORES", 4),
    ("133010", "A CONTRATISTAS", 4),
    ("133015", "A TRABAJADORES", 4),
    ("1355", "ANTICIPO DE IMPUESTOS Y CONTRIBUCIONES", 3),
    ("135505", "ANTICIPO DE IMPUESTO DE RENTA Y COMPLEMENTARIOS", 4),
    ("135510", "ANTICIPO DE IMPUESTO DE INDUSTRIA Y COMERCIO", 4),
    ("135515", "RETENCION EN LA FUENTE", 4),
    ("135517", "IMPUESTO A LAS VENTAS RETENIDO", 4),
    ("135518", "IMPUESTO DE INDUSTRIA Y COMERCIO RETENIDO", 4),
    ("1365", "CUENTAS POR COBRAR A TRABAJADORES", 3),
    ("136505", "VIVIENDA", 4),
    ("136510", "VEHICULOS", 4),
    ("136515", "EDUCACION", 4),
    ("136520", "MEDICOS, ODONTOLOGICOS Y SIMILARES", 4),
    ("136525", "CALAMIDAD DOMESTICA", 4),
    ("136530", "RESPONSABILIDADES", 4),
    ("136595", "OTROS", 4),
    ("1380", "DEUDORES VARIOS", 3),
    ("1390", "DEUDAS DE DIFICIL COBRO", 3),
    ("1399", "PROVISIONES", 3),
    ("139905", "CLIENTES", 4),
    ("14", "INVENTARIOS", 2),
    ("1405", "MATERIAS PRIMAS", 3),
    ("1410", "PRODUCTOS EN PROCESO", 3),
    ("1430", "PRODUCTOS TERMINADOS", 3),
    ("143005", "DE ORIGEN VEGETAL Y ANIMAL", 4),
    ("143010", "DE ORIGEN MINERAL", 4),
    ("143015", "PRODUCTOS MANUFACTURADOS", 4),
    ("1435", "MERCANCIAS NO FABRICADAS POR LA EMPRESA", 3),
    ("143501", "INVENTARIO GENERAL", 4),
    ("1455", "MATERIALES, REPUESTOS Y ACCESORIOS", 3),
    ("1460", "ENVASES Y EMPAQUES", 3),
    ("1465", "INVENTARIOS EN TRANSITO", 3),
    ("15", "PROPIEDAD PLANTA Y EQUIPO", 2),
    ("1504", "TERRENOS", 3),
    ("150405", "URBANOS", 4),
    ("150410", "RURALES", 4),
    ("1516", "CONSTRUCCIONES Y EDIFICACIONES", 3),
    ("151605", "EDIFICIOS", 4),
    ("151610", "OFICINAS", 4),
    ("151615", "ALMACENES", 4),
    ("1520", "MAQUINARIA Y EQUIPO", 3),
    ("1524", "EQUIPO DE OFICINA", 3),
    ("152405", "MUEBLES Y ENSERES", 4),
    ("152410", "EQUIPOS", 4),
    ("1528", "EQUIPO DE COMPUTACION Y COMUNICACION", 3),
    ("152805", "EQUIPOS DE PROCESAMIENTO DE DATOS", 4),
    ("152810", "EQUIPOS DE TELECOMUNICACIONES", 4),
    ("1540", "FLOTA Y EQUIPO DE TRANSPORTE", 3),
    ("154005", "AUTOS, CAMIONETAS Y CAMPEROS", 4),
    ("154008", "CAMIONES, VOLQUETAS Y FURGONES", 4),
    ("154030", "MOTOCICLETAS", 4),
    ("1592", "DEPRECIACION ACUMULADA", 3),
    ("159205", "CONSTRUCCIONES Y EDIFICACIONES", 4),
    ("159210", "MAQUINARIA Y EQUIPO", 4),
    ("159215", "EQUIPO DE OFICINA", 4),
    ("159220", "EQUIPO DE COMPUTACION Y COMUNICACION", 4),
    ("159235", "FLOTA Y EQUIPO DE TRANSPORTE", 4),
    ("16", "INTANGIBLES", 2),
    ("1605", "CREDITO MERCANTIL", 3),
    ("1610", "MARCAS", 3),
    ("1615", "PATENTES", 3),
    ("1635", "LICENCIAS", 3),
    ("17", "DIFERIDOS", 2),
    ("1705", "GASTOS PAGADOS POR ANTICIPADO", 3),
    ("170505", "INTERESES", 4),
    ("170510", "HONORARIOS", 4),
    ("170515", "COMISIONES", 4),
    ("170520", "SEGUROS Y FIANZAS", 4),
    ("170525", "ARRENDAMIENTOS", 4),
    ("1710", "CARGOS DIFERIDOS", 3),
    ("171004", "ORGANIZACION Y PREOPERATIVOS", 4),
    ("171008", "REMODELACIONES", 4),
    ("171012", "ESTUDIOS, INVESTIGACIONES Y PROYECTOS", 4),
    ("171016", "PROGRAMAS PARA COMPUTADOR (SOFTWARE)", 4),
    ("171020", "UTILES Y PAPELERIA", 4),

    # CLASE 2: PASIVO
    ("2", "PASIVO", 1),
    ("21", "OBLIGACIONES FINANCIERAS", 2),
    ("2105", "BANCOS NACIONALES", 3),
    ("210505", "SOBREGIROS", 4),
    ("210510", "PAGARES", 4),
    ("210515", "CARTAS DE CREDITO", 4),
    ("210520", "ACEPTACIONES BANCARIAS", 4),
    ("2120", "COMPAÑIAS DE FINANCIAMIENTO COMERCIAL", 3),
    ("22", "PROVEEDORES", 2),
    ("2205", "NACIONALES", 3),
    ("2210", "DEL EXTERIOR", 3),
    ("23", "CUENTAS POR PAGAR", 2),
    ("2305", "CUENTAS CORRIENTES COMERCIALES", 3),
    ("2335", "COSTOS Y GASTOS POR PAGAR", 3),
    ("233505", "FINANCIEROS", 4),
    ("233510", "GASTOS LEGALES", 4),
    ("233515", "LIBROS, SUSCRIPCIONES, PERIODICOS Y REVISTAS", 4),
    ("233520", "COMISIONES", 4),
    ("233525", "HONORARIOS", 4),
    ("233530", "SERVICIOS TECNICOS", 4),
    ("233535", "SERVICIOS DE MANTENIMIENTO", 4),
    ("233540", "ARRENDAMIENTOS", 4),
    ("233545", "TRANSPORTES, FLETES Y ACARREOS", 4),
    ("233550", "SERVICIOS PUBLICOS", 4),
    ("233555", "SEGUROS", 4),
    ("233595", "OTROS", 4),
    ("2355", "DEUDAS CON ACCIONISTAS O SOCIOS", 3),
    ("2365", "RETENCION EN LA FUENTE", 3),
    ("236505", "SALARIOS Y PAGOS LABORALES", 4),
    ("236510", "DIVIDENDOS Y PARTICIPACIONES", 4),
    ("236515", "HONORARIOS", 4),
    ("236520", "COMISIONES", 4),
    ("236525", "SERVICIOS", 4),
    ("236530", "ARRENDAMIENTOS", 4),
    ("236535", "RENDIMIENTOS FINANCIEROS", 4),
    ("236540", "COMPRAS", 4),
    ("2367", "IMPUESTO A LAS VENTAS RETENIDO", 3),
    ("2368", "IMPUESTO DE INDUSTRIA Y COMERCIO RETENIDO", 3),
    ("2370", "RETENCIONES Y APORTES DE NOMINA", 3),
    ("237005", "APORTES A ENTIDADES PROMOTORAS DE SALUD EPS", 4),
    ("237006", "APORTES A ADMINISTRADORAS DE RIESGOS PROFESIONALES ARP", 4),
    ("237010", "APORTES AL ICBF SENA Y CAJAS DE COMPENSACION", 4),
    ("2380", "ACREEDORES VARIOS", 3),
    ("24", "IMPUESTOS GRAVAMENES Y TASAS", 2),
    ("2404", "DE RENTA Y COMPLEMENTARIOS", 3),
    ("2408", "IMPUESTO SOBRE LAS VENTAS POR PAGAR", 3),
    ("240801", "IVA GENERADO", 4),
    ("240802", "IVA DESCONTABLE", 4),
    ("2412", "DE INDUSTRIA Y COMERCIO", 3),
    ("25", "OBLIGACIONES LABORALES", 2),
    ("2505", "SALARIOS POR PAGAR", 3),
    ("2510", "CESANTIAS CONSOLIDADAS", 3),
    ("2515", "INTERESES SOBRE CESANTIAS", 3),
    ("2520", "PRIMA DE SERVICIOS", 3),
    ("2525", "VACACIONES CONSOLIDADAS", 3),
    ("26", "PASIVOS ESTIMADOS Y PROVISIONES", 2),
    ("2610", "PARA OBLIGACIONES LABORALES", 3),
    ("261005", "CESANTIAS", 4),
    ("261010", "INTERESES SOBRE CESANTIAS", 4),
    ("261015", "VACACIONES", 4),
    ("261020", "PRIMA DE SERVICIOS", 4),

    # CLASE 3: PATRIMONIO
    ("3", "PATRIMONIO", 1),
    ("31", "CAPITAL SOCIAL", 2),
    ("3105", "CAPITAL SUSCRITO Y PAGADO", 3),
    ("3115", "APORTES SOCIALES", 3),
    ("32", "SUPERAVIT DE CAPITAL", 2),
    ("33", "RESERVAS", 2),
    ("3305", "RESERVAS OBLIGATORIAS", 3),
    ("3310", "RESERVAS ESTATUTARIAS", 3),
    ("36", "RESULTADOS DEL EJERCICIO", 2),
    ("3605", "UTILIDAD DEL EJERCICIO", 3),
    ("3610", "PERDIDA DEL EJERCICIO", 3),
    ("37", "RESULTADOS DE EJERCICIOS ANTERIORES", 2),
    ("3705", "UTILIDADES ACUMULADAS", 3),
    ("3710", "PERDIDAS ACUMULADAS", 3),

    # CLASE 4: INGRESOS
    ("4", "INGRESOS", 1),
    ("41", "OPERACIONALES", 2),
    ("4105", "AGRICULTURA, GANADERIA, CAZA Y SILVICULTURA", 3),
    ("4110", "PESCA", 3),
    ("4115", "EXPLOTACION DE MINAS Y CANTERAS", 3),
    ("4120", "INDUSTRIAS MANUFACTURERAS", 3),
    ("4125", "SUMINISTRO DE ELECTRICIDAD, GAS Y AGUA", 3),
    ("4130", "CONSTRUCCION", 3),
    ("4135", "COMERCIO AL POR MAYOR Y AL POR MENOR", 3),
    ("413501", "VENTAS GENERALES", 4),
    ("4140", "HOTELES Y RESTAURANTES", 3),
    ("4145", "TRANSPORTE, ALMACENAMIENTO Y COMUNICACIONES", 3),
    ("4150", "ACTIVIDAD FINANCIERA", 3),
    ("4155", "ACTIVIDADES INMOBILIARIAS, EMPRESARIALES Y DE ALQUILER", 3),
    ("4160", "ENSEÑANZA", 3),
    ("4165", "SERVICIOS SOCIALES Y DE SALUD", 3),
    ("4170", "OTRAS ACTIVIDADES DE SERVICIOS COMUNITARIOS", 3),
    ("4175", "DEVOLUCIONES EN VENTAS (DB)", 3),
    ("42", "NO OPERACIONALES", 2),
    ("4205", "OTRAS VENTAS", 3),
    ("4210", "FINANCIEROS", 3),
    ("421005", "INTERESES", 4),
    ("421040", "DESCUENTOS COMERCIALES CONDICIONADOS", 4),
    ("4220", "ARRENDAMIENTOS", 3),
    ("4225", "COMISIONES", 3),
    ("4230", "HONORARIOS", 3),
    ("4235", "SERVICIOS", 3),
    ("4240", "UTILIDAD EN VENTA DE INVERSIONES", 3),
    ("4245", "UTILIDAD EN VENTA DE PROPIEDAD PLANTA Y EQUIPO", 3),
    ("4250", "RECUPERACIONES", 3),
    ("4255", "INDEMNIZACIONES", 3),
    ("4295", "DIVERSOS", 3),

    # CLASE 5: GASTOS
    ("5", "GASTOS", 1),
    ("51", "OPERACIONALES DE ADMINISTRACION", 2),
    ("5105", "GASTOS DE PERSONAL", 3),
    ("510506", "SUELDOS", 4),
    ("510515", "HORAS EXTRAS Y RECARGOS", 4),
    ("510527", "AUXILIO DE TRANSPORTE", 4),
    ("510530", "CESANTIAS", 4),
    ("510533", "INTERESES SOBRE CESANTIAS", 4),
    ("510536", "PRIMA DE SERVICIOS", 4),
    ("510539", "VACACIONES", 4),
    ("510560", "INDEMNIZACIONES LABORALES", 4),
    ("510563", "CAPACITACION AL PERSONAL", 4),
    ("510566", "GASTOS DEPORTIVOS Y DE RECREACION", 4),
    ("510569", "APORTES A ADMINISTRADORAS DE RIESGOS PROFESIONALES ARP", 4),
    ("510570", "APORTES A FONDOS DE PENSIONES Y/O CESANTIAS", 4),
    ("510572", "APORTES CAJAS DE COMPENSACION FAMILIAR", 4),
    ("510575", "APORTES ICBF", 4),
    ("510578", "APORTES SENA", 4),
    ("510581", "APORTES SINDICALES", 4),
    ("510584", "GASTOS MEDICOS Y DROGAS", 4),
    ("5110", "HONORARIOS", 3),
    ("511005", "JUNTA DIRECTIVA", 4),
    ("511010", "REVISORIA FISCAL", 4),
    ("511015", "AUDITORIA EXTERNA", 4),
    ("511025", "ASESORIA JURIDICA", 4),
    ("511030", "ASESORIA FINANCIERA", 4),
    ("511035", "ASESORIA TECNICA", 4),
    ("5115", "IMPUESTOS", 3),
    ("511505", "INDUSTRIA Y COMERCIO", 4),
    ("511510", "DE TIMBRES", 4),
    ("511515", "A LA PROPIEDAD RAIZ", 4),
    ("511520", "DE REGISTRO", 4),
    ("511525", "DE VEHICULOS", 4),
    ("511540", "DE LICORES", 4),
    ("511545", "DE PORCINOS", 4),
    ("511550", "DE DEGUELLO", 4),
    ("511570", "IVA DESCONTABLE", 4),
    ("5120", "ARRENDAMIENTOS", 3),
    ("512005", "TERRENOS", 4),
    ("512010", "CONSTRUCCIONES Y EDIFICACIONES", 4),
    ("512015", "MAQUINARIA Y EQUIPO", 4),
    ("512020", "EQUIPO DE OFICINA", 4),
    ("512025", "EQUIPO DE COMPUTACION Y COMUNICACION", 4),
    ("512030", "EQUIPO MEDICO CIENTIFICO", 4),
    ("512035", "FLOTA Y EQUIPO DE TRANSPORTE", 4),
    ("5125", "CONTRIBUCIONES Y AFILIACIONES", 3),
    ("5130", "SEGUROS", 3),
    ("513005", "CUMPLIMIENTO", 4),
    ("513010", "CORRIENTE DEBIL", 4),
    ("513015", "RESPONSABILIDAD CIVIL", 4),
    ("513020", "INCENDIO", 4),
    ("513025", "SUSTRACCION Y HURTO", 4),
    ("513030", "LUCRO CESANTE", 4),
    ("513035", "TRANSPORTE", 4),
    ("513040", "FLOTA Y EQUIPO DE TRANSPORTE", 4),
    ("513060", "VIDA COLECTIVA", 4),
    ("5135", "SERVICIOS", 3),
    ("513505", "ASEO Y VIGILANCIA", 4),
    ("513510", "TEMPORALES", 4),
    ("513515", "ASISTENCIA TECNICA", 4),
    ("513520", "PROCESAMIENTO DE DATOS", 4),
    ("513525", "ACUEDUCTO Y ALCANTARILLADO", 4),
    ("513530", "ENERGIA ELECTRICA", 4),
    ("513535", "TELEFONO", 4),
    ("513540", "CORREO PORTES Y TELEGRAMAS", 4),
    ("513545", "FAX Y TELEX", 4),
    ("513550", "TRANSPORTE FLETES Y ACARREOS", 4),
    ("513555", "GAS", 4),
    ("513595", "OTROS", 4),
    ("5140", "GASTOS LEGALES", 3),
    ("514005", "NOTARIALES", 4),
    ("514010", "REGISTRO MERCANTIL", 4),
    ("514015", "TRAMITES Y LICENCIAS", 4),
    ("5145", "MANTENIMIENTO Y REPARACIONES", 3),
    ("514505", "TERRENOS", 4),
    ("514510", "CONSTRUCCIONES Y EDIFICACIONES", 4),
    ("514515", "MAQUINARIA Y EQUIPO", 4),
    ("514520", "EQUIPO DE OFICINA", 4),
    ("514525", "EQUIPO DE COMPUTACION Y COMUNICACION", 4),
    ("514540", "FLOTA Y EQUIPO DE TRANSPORTE", 4),
    ("5150", "ADECUACION E INSTALACION", 3),
    ("5155", "GASTOS DE VIAJE", 3),
    ("515505", "ALOJAMIENTO Y MANUTENCION", 4),
    ("515515", "PASAJES AEREOS", 4),
    ("515520", "PASAJES TERRESTRES", 4),
    ("5160", "DEPRECIACIONES", 3),
    ("516005", "CONSTRUCCIONES Y EDIFICACIONES", 4),
    ("516010", "MAQUINARIA Y EQUIPO", 4),
    ("516015", "EQUIPO DE OFICINA", 4),
    ("516020", "EQUIPO DE COMPUTACION Y COMUNICACION", 4),
    ("516035", "FLOTA Y EQUIPO DE TRANSPORTE", 4),
    ("5165", "AMORTIZACIONES", 3),
    ("5195", "DIVERSOS", 3),
    ("519505", "COMISIONES", 4),
    ("519510", "LIBROS, SUSCRIPCIONES, PERIODICOS Y REVISTAS", 4),
    ("519520", "GASTOS DE REPRESENTACION", 4),
    ("519525", "ELEMENTOS DE ASEO Y CAFETERIA", 4),
    ("519530", "UTILES PAPELERIA Y FOTOCOPIAS", 4),
    ("519535", "COMBUSTIBLES Y LUBRICANTES", 4),
    ("519540", "ENVASES Y EMPAQUES", 4),
    ("519545", "TAXIS Y BUSES", 4),
    ("519560", "CASINO Y RESTAURANTE", 4),
    ("519565", "PARQUEADEROS", 4),
    ("519595", "OTROS", 4),
    ("52", "OPERACIONALES DE VENTAS", 2),
    ("53", "NO OPERACIONALES", 2),
    ("5305", "FINANCIEROS", 3),
    ("530505", "GASTOS BANCARIOS", 4),
    ("530515", "COMISIONES", 4),
    ("530520", "INTERESES", 4),
    ("530525", "DIFFERENCIA EN CAMBIO", 4),
    ("530530", "GASTOS EN NEGOCIACION CERTIFICADOS DE CAMBIO", 4),
    ("530535", "DESCUENTOS COMERCIALES CONDICIONADOS", 4),
    ("530595", "OTROS", 4),
    ("5310", "PERDIDA EN VENTA Y RETIRO DE BIENES", 3),
    ("5315", "GASTOS EXTRAORDINARIOS", 3),
    ("5395", "GASTOS DIVERSOS", 3),

    # CLASE 6: COSTOS DE VENTAS
    ("6", "COSTOS DE VENTAS", 1),
    ("61", "COSTO DE VENTAS Y DE PRESTACION DE SERVICIOS", 2),
    ("6105", "AGRICULTURA, GANADERIA, CAZA Y SILVICULTURA", 3),
    ("6110", "PESCA", 3),
    ("6115", "EXPLOTACION DE MINAS Y CANTERAS", 3),
    ("6120", "INDUSTRIAS MANUFACTURERAS", 3),
    ("6125", "SUMINISTRO DE ELECTRICIDAD, GAS Y AGUA", 3),
    ("6130", "CONSTRUCCION", 3),
    ("6135", "COMERCIO AL POR MAYOR Y AL POR MENOR", 3),
    ("6140", "HOTELES Y RESTAURANTES", 3),
    ("6145", "TRANSPORTE, ALMACENAMIENTO Y COMUNICACIONES", 3),
    ("6150", "ACTIVIDAD FINANCIERA", 3),
    ("6155", "ACTIVIDADES INMOBILIARIAS, EMPRESARIALES Y DE ALQUILER", 3),
    ("6160", "ENSEÑANZA", 3),
    ("6165", "SERVICIOS SOCIALES Y DE SALUD", 3),
    ("6170", "OTRAS ACTIVIDADES DE SERVICIOS COMUNITARIOS", 3),
]

def generate_puc_json():
    print("Construyendo PUC Maestro Extendido...")
    
    plan_cuentas = []
    
    # 1. Construir Diccionario de Mapeo (Codigo -> ID)
    code_to_id = {}
    current_id = 1
    
    # Primera pasada: Asignar IDs
    temp_list = []
    for codigo, nombre, nivel in CUENTAS_BASE:
        code_to_id[codigo] = current_id
        temp_list.append({
            "codigo": codigo,
            "nombre": nombre,
            "nivel": nivel,
            "id": current_id
        })
        current_id += 1
        
    # Segunda pasada: Construir Objetos Finales con Padres
    for item in temp_list:
        codigo = item["codigo"]
        nivel = item["nivel"]
        
        # Determinar Padre
        padre_id = None
        if nivel > 1:
            len_padre = 0
            if nivel == 2: len_padre = 1
            elif nivel == 3: len_padre = 2
            elif nivel == 4: len_padre = 4
            
            codigo_padre = codigo[:len_padre]
            padre_id = code_to_id.get(codigo_padre)

        # Determinar si permite movimiento (Solo nivel 4 o el mayor definido)
        permite_movimiento = (nivel >= 4)
        
        # Determinar Clase (Primer dígito)
        clase = int(codigo[0])

        # Determinar si es cuenta de ingresos (Clase 4)
        es_ingresos = (clase == 4)

        cuenta_obj = {
            "id": item["id"],
            "empresa_id": 0, # Genérico
            "codigo": codigo,
            "nombre": item["nombre"],
            "nivel": nivel,
            "clase": clase,
            "permite_movimiento": permite_movimiento,
            "cuenta_padre_id": padre_id,
            "es_cuenta_de_ingresos": es_ingresos,
            # Eliminados campos inválidos: naturaleza, tipo_cuenta, estado
        }
        plan_cuentas.append(cuenta_obj)

    # 2. Estructura Final (Formato B)
    backup_data = {
        "metadata": {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "version_sistema": "7.0",
            "empresa_id_origen": 0,
            "descripcion": "PLANTILLA MAESTRA PUC COMERCIANTES 2025 (EXTENDIDO)"
        },
        "empresa": {}, 
        "configuracion": {}, 
        "maestros": {
            "plan_cuentas": plan_cuentas
        }, 
        "inventario": {}, 
        "transacciones": []
    }
    
    # 3. Firmar
    print("Firmando archivo...")
    json_str = json.dumps(backup_data, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    signed_backup = {
        "data": backup_data,
        "signature": signature
    }
    
    # 4. Guardar
    output_path = r"c:\ContaPY2\Manual\maestros\PUC_Comerciantes_2025.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(signed_backup, f, indent=2, ensure_ascii=False)
        
    print(f"Archivo generado exitosamente en: {output_path}")

if __name__ == "__main__":
    generate_puc_json()
