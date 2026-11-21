-- Iconic · catálogos iniciales (reglas de negocio, secciones 2, 3 y 4).
-- Se ejecuta después de schema.sql. El negocio puede ampliarlos desde la app.

BEGIN;

INSERT INTO tipos_categoria (nombre, usa_imei, usa_bateria, usa_controles, por_cantidad) VALUES
    ('Equipo con IMEI', true,  true,  false, false),
    ('Equipo sin IMEI', false, false, false, false),
    ('Consola',         false, false, true,  false),
    ('Accesorio',       false, false, false, true);

INSERT INTO categorias (nombre, tipo_categoria_id)
SELECT c.nombre, t.id
FROM (VALUES
    ('iPhone', 'Equipo con IMEI'), ('iPad', 'Equipo con IMEI'), ('Mac', 'Equipo con IMEI'),
    ('Apple Watch', 'Equipo sin IMEI'), ('AirPods', 'Equipo sin IMEI'),
    ('Xbox', 'Consola'), ('PlayStation', 'Consola'), ('Nintendo', 'Consola'),
    ('Vidrio templado', 'Accesorio'), ('Cargador', 'Accesorio'), ('Cable', 'Accesorio'),
    ('Funda/Case', 'Accesorio'), ('Otro accesorio', 'Accesorio')
) AS c(nombre, tipo)
JOIN tipos_categoria t ON t.nombre = c.tipo;

INSERT INTO proveedores (nombre) VALUES
    ('Plan canje'), ('Importación personal'), ('Mariano Camara'), ('Lucas Bertorello');

INSERT INTO metodos_pago (nombre, predeterminado) VALUES
    ('Transferencia', true), ('Débito', false), ('Crédito', false), ('Efectivo', false);

INSERT INTO diagnosticos (nombre) VALUES
    ('Pantalla'), ('Batería'), ('Cámara'), ('Botones'), ('Señal'), ('No enciende'), ('Audio'),
    ('Carga'), ('Humedad'), ('Face ID / Touch ID'), ('Reinicios'), ('Sobrecalentamiento'), ('Otro');

INSERT INTO estados_reclamo (nombre, es_inicial) VALUES ('En gestión', true);

INSERT INTO defectos (descripcion, es_comun) VALUES
    ('Pantalla con micro-rayones', true), ('Marco desgastado', true), ('Puerto de carga flojo', true);

COMMIT;
