from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/contapy_db')
with engine.begin() as conn:
    conn.execute(text('ALTER TABLE ph_configuracion ADD COLUMN descuento_pronto_pago_habilitado BOOLEAN DEFAULT TRUE;'))
    conn.execute(text('ALTER TABLE ph_unidades ADD COLUMN aplica_pronto_pago BOOLEAN DEFAULT TRUE;'))
print('Migrated flags successfully')
