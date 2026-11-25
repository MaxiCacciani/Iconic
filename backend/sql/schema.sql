-- Iconic · esquema PostgreSQL 16 (un solo negocio, montos en USD)
-- Fuente: DER-Iconic.pdf. Lo que se puede calcular no se guarda
-- (totales, ganancia, saldo, cuota vencida, vencimiento de garantía, categoría del producto).

BEGIN;

-- ─── ENUMs nativos (valores fijos de los que depende la lógica) ──────────────
CREATE TYPE rol             AS ENUM ('admin', 'vendedor');
CREATE TYPE condicion       AS ENUM ('nuevo', 'usado');
CREATE TYPE estado_producto AS ENUM ('disponible', 'reservado', 'vendido');
CREATE TYPE estado_reserva  AS ENUM ('activa', 'convertida', 'cancelada');
CREATE TYPE estado_cobro    AS ENUM ('pendiente', 'cobrada');   -- "vencida" se calcula al leer
CREATE TYPE modalidad       AS ENUM ('contado', 'cuotas');
CREATE TYPE tipo_archivo    AS ENUM ('pdf', 'jpg');

-- ─── Acceso y configuración ──────────────────────────────────────────────────
CREATE TABLE usuarios (
    id            serial PRIMARY KEY,
    nombre        text        NOT NULL,
    email         text        NOT NULL UNIQUE,
    password_hash text        NOT NULL,
    rol           rol         NOT NULL,
    activo        boolean     NOT NULL DEFAULT true,
    creado_en     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tipos_cambio (
    id         serial PRIMARY KEY,
    fecha      date          NOT NULL UNIQUE,
    valor_ars  numeric(12,2) NOT NULL CHECK (valor_ars > 0),
    usuario_id int           NOT NULL REFERENCES usuarios(id),
    creado_en  timestamptz   NOT NULL DEFAULT now()
);

CREATE TABLE vendedores (
    id     serial PRIMARY KEY,
    numero int  NOT NULL UNIQUE,
    nombre text NOT NULL
);

-- ─── Catálogos (el negocio los amplía desde la app) ──────────────────────────
CREATE TABLE localidades     (id serial PRIMARY KEY, nombre text NOT NULL UNIQUE);
CREATE TABLE diagnosticos    (id serial PRIMARY KEY, nombre text NOT NULL UNIQUE);
CREATE TABLE proveedores     (id serial PRIMARY KEY, nombre text NOT NULL UNIQUE);

CREATE TABLE estados_reclamo (
    id         serial PRIMARY KEY,
    nombre     text    NOT NULL UNIQUE,
    es_inicial boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX uq_estados_reclamo_inicial ON estados_reclamo (es_inicial) WHERE es_inicial;

CREATE TABLE metodos_pago (
    id             serial PRIMARY KEY,
    nombre         text    NOT NULL UNIQUE,
    predeterminado boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX uq_metodos_pago_predeterminado ON metodos_pago (predeterminado) WHERE predeterminado;

CREATE TABLE defectos (
    id          serial PRIMARY KEY,
    descripcion text    NOT NULL UNIQUE,
    es_comun    boolean NOT NULL DEFAULT false
);

CREATE TABLE tipos_categoria (
    id            serial PRIMARY KEY,
    nombre        text    NOT NULL UNIQUE,
    usa_imei      boolean NOT NULL DEFAULT false,
    usa_bateria   boolean NOT NULL DEFAULT false,
    usa_controles boolean NOT NULL DEFAULT false,
    por_cantidad  boolean NOT NULL DEFAULT false
);

CREATE TABLE categorias (
    id                serial PRIMARY KEY,
    nombre            text NOT NULL UNIQUE,
    tipo_categoria_id int  NOT NULL REFERENCES tipos_categoria(id)
);

CREATE TABLE modelos (
    id           serial PRIMARY KEY,
    categoria_id int  NOT NULL REFERENCES categorias(id),
    nombre       text NOT NULL,
    UNIQUE (categoria_id, nombre)
);

CREATE TABLE capacidades (
    id           serial PRIMARY KEY,
    categoria_id int  NOT NULL REFERENCES categorias(id),
    nombre       text NOT NULL,
    UNIQUE (categoria_id, nombre)
);

CREATE TABLE colores (
    id           serial PRIMARY KEY,
    categoria_id int  NOT NULL REFERENCES categorias(id),
    nombre       text NOT NULL,
    UNIQUE (categoria_id, nombre)
);

-- Qué colores y capacidades de su categoría tiene cada modelo. Un modelo sin filas acá
-- ofrece todos los de su categoría. Que sean de la misma categoría lo valida la API
-- (la categoría de un modelo, color o capacidad no se cambia).
CREATE TABLE modelo_colores (
    modelo_id int NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
    color_id  int NOT NULL REFERENCES colores(id) ON DELETE CASCADE,
    PRIMARY KEY (modelo_id, color_id)
);

CREATE TABLE modelo_capacidades (
    modelo_id    int NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
    capacidad_id int NOT NULL REFERENCES capacidades(id) ON DELETE CASCADE,
    PRIMARY KEY (modelo_id, capacidad_id)
);

-- ─── Clientes y reclamos ─────────────────────────────────────────────────────
CREATE TABLE clientes (
    id           serial PRIMARY KEY,
    nombre       text        NOT NULL,
    dni          varchar(8)  UNIQUE CHECK (dni ~ '^[0-9]{7,8}$'),
    telefono     varchar(15) CHECK (telefono ~ '^[0-9]{8,15}$'),
    localidad_id int         REFERENCES localidades(id),
    creado_en    timestamptz NOT NULL DEFAULT now()
);

-- ─── Stock y packs ───────────────────────────────────────────────────────────
CREATE TABLE productos (
    id           serial PRIMARY KEY,
    modelo_id    int             NOT NULL REFERENCES modelos(id),
    capacidad_id int             REFERENCES capacidades(id),
    color_id     int             REFERENCES colores(id),
    proveedor_id int             NOT NULL REFERENCES proveedores(id),
    condicion    condicion       NOT NULL,
    imei         char(15)        CHECK (imei ~ '^[0-9]{15}$'),
    bateria      smallint        CHECK (bateria BETWEEN 1 AND 100),
    controles    smallint        CHECK (controles BETWEEN 0 AND 4),
    extras       text,
    cantidad     int             NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
    precio_usd   numeric(12,2)   NOT NULL CHECK (precio_usd > 0),
    costo_usd    numeric(12,2)   CHECK (costo_usd >= 0 AND costo_usd <= precio_usd),
    estado       estado_producto NOT NULL DEFAULT 'disponible',
    creado_en    timestamptz     NOT NULL DEFAULT now()
);
-- El IMEI no se repite en el stock (lo no vendido). Uno vendido puede volver a entrar
-- por canje con el mismo IMEI: las ventas apuntan al producto_id, no al IMEI.
CREATE UNIQUE INDEX uq_productos_imei ON productos (imei)
    WHERE imei IS NOT NULL AND estado <> 'vendido';
CREATE INDEX ix_productos_estado ON productos (estado);
CREATE INDEX ix_productos_modelo ON productos (modelo_id);

CREATE TABLE producto_defectos (
    producto_id int NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    defecto_id  int NOT NULL REFERENCES defectos(id),
    PRIMARY KEY (producto_id, defecto_id)
);

CREATE TABLE packs (
    id          serial PRIMARY KEY,
    nombre      text NOT NULL,
    descripcion text
);

CREATE TABLE pack_items (
    id           serial PRIMARY KEY,
    pack_id      int     NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
    producto_id  int     REFERENCES productos(id) ON DELETE CASCADE,
    categoria_id int     REFERENCES categorias(id),
    cantidad     int     NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
    es_regalo    boolean NOT NULL DEFAULT false,
    CHECK (num_nonnulls(producto_id, categoria_id) = 1)   -- producto fijo o categoría, nunca los dos
);

-- ─── Reservas ────────────────────────────────────────────────────────────────
CREATE TABLE reservas (
    id         serial PRIMARY KEY,
    cliente_id int            NOT NULL REFERENCES clientes(id),
    usuario_id int            NOT NULL REFERENCES usuarios(id),
    fecha      timestamptz    NOT NULL DEFAULT now(),
    sena_usd   numeric(12,2)  NOT NULL CHECK (sena_usd >= 0),
    tc_ars     numeric(12,2)  NOT NULL CHECK (tc_ars > 0),
    estado     estado_reserva NOT NULL DEFAULT 'activa'
);
CREATE INDEX ix_reservas_activas ON reservas (cliente_id) WHERE estado = 'activa';

CREATE TABLE reserva_items (
    id          serial PRIMARY KEY,
    reserva_id  int NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
    producto_id int NOT NULL REFERENCES productos(id),
    cantidad    int NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
    UNIQUE (reserva_id, producto_id)
);

-- ─── Ventas y cobros ─────────────────────────────────────────────────────────
CREATE TABLE ventas (
    id                serial PRIMARY KEY,
    fecha             timestamptz   NOT NULL DEFAULT now(),
    cliente_id        int           NOT NULL REFERENCES clientes(id),
    usuario_id        int           NOT NULL REFERENCES usuarios(id),
    vendedor_id       int           REFERENCES vendedores(id),
    reserva_id        int           UNIQUE REFERENCES reservas(id) ON DELETE SET NULL,
    canje_producto_id int           UNIQUE REFERENCES productos(id) ON DELETE SET NULL,
    metodo_pago_id    int           NOT NULL REFERENCES metodos_pago(id),
    modalidad         modalidad     NOT NULL,
    cantidad_cuotas   smallint      CHECK (cantidad_cuotas BETWEEN 2 AND 60),
    tc_ars            numeric(12,2) NOT NULL CHECK (tc_ars > 0),
    anticipo_usd      numeric(12,2) NOT NULL DEFAULT 0 CHECK (anticipo_usd >= 0),
    canje_valor_usd   numeric(12,2) CHECK (canje_valor_usd >= 0),
    garantia_meses    smallint      NOT NULL DEFAULT 3 CHECK (garantia_meses >= 0),
    CHECK ((modalidad = 'cuotas') = (cantidad_cuotas IS NOT NULL)),
    CHECK ((canje_producto_id IS NULL) = (canje_valor_usd IS NULL))
);
CREATE INDEX ix_ventas_fecha ON ventas (fecha);
CREATE INDEX ix_ventas_cliente ON ventas (cliente_id);
CREATE INDEX ix_ventas_usuario ON ventas (usuario_id);

CREATE TABLE venta_items (
    id          serial PRIMARY KEY,
    venta_id    int           NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id int           NOT NULL REFERENCES productos(id),
    cantidad    int           NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
    precio_usd  numeric(12,2) NOT NULL CHECK (precio_usd >= 0),
    costo_usd   numeric(12,2) CHECK (costo_usd >= 0),
    es_regalo   boolean       NOT NULL DEFAULT false
);
CREATE INDEX ix_venta_items_venta ON venta_items (venta_id);

CREATE TABLE cobros (
    id                serial PRIMARY KEY,
    venta_id          int           NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    numero_cuota      smallint      NOT NULL CHECK (numero_cuota >= 1),
    fecha_vencimiento date          NOT NULL,
    monto_usd         numeric(12,2) NOT NULL CHECK (monto_usd >= 1),
    estado            estado_cobro  NOT NULL DEFAULT 'pendiente',
    UNIQUE (venta_id, numero_cuota)
);
CREATE INDEX ix_cobros_pendientes ON cobros (fecha_vencimiento) WHERE estado = 'pendiente';

CREATE TABLE garantia_archivos (
    id       serial PRIMARY KEY,
    venta_id int          NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    orden    smallint     NOT NULL CHECK (orden BETWEEN 1 AND 2),
    clave_r2 text         NOT NULL UNIQUE,
    tipo     tipo_archivo NOT NULL,
    UNIQUE (venta_id, orden)
);

-- ─── Reclamos (al final: referencia a productos) ─────────────────────────────
CREATE TABLE reclamos (
    id                serial PRIMARY KEY,
    cliente_id        int  NOT NULL REFERENCES clientes(id),
    producto_id       int  REFERENCES productos(id) ON DELETE SET NULL,
    diagnostico_id    int  NOT NULL REFERENCES diagnosticos(id),
    estado_reclamo_id int  NOT NULL REFERENCES estados_reclamo(id),
    descripcion       text NOT NULL,
    fecha             date NOT NULL DEFAULT current_date,
    resolucion        text
);

COMMIT;
