from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/contapy_db')
with engine.begin() as conn:
    conn.execute(text('ALTER TABLE ph_configuracion ADD COLUMN cuenta_descuento_id INTEGER;'))
    conn.execute(text('ALTER TABLE ph_configuracion ADD CONSTRAINT fk_ph_config_cuenta_desc FOREIGN KEY (cuenta_descuento_id) REFERENCES plan_cuentas (id);'))
print('Done')
