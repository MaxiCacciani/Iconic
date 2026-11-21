# Plan de desarrollo — Iconic

Cada fase es un corte vertical: se arma el backend, la pantalla que lo usa y se prueba de punta a punta antes de pasar a la siguiente. Al terminar cada fase tiene que haber algo que funcione en el navegador.

## Avance

Al cerrar una fase, marcala acá.

- [x] Fase 0 — Base del proyecto
- [x] Fase 1 — Login, sesión y usuarios
- [x] Fase 2 — TC del día y esqueleto de Resumen
- [ ] Fase 3 — Catálogos ← **siguiente**
- [ ] Fase 4 — Productos y stock
- [ ] Fase 5 — Clientes
- [ ] Fase 6 — Vendedores y packs
- [ ] Fase 7 — Ventas al contado y canje
- [ ] Fase 8 — Cuotas, cobros y agenda
- [ ] Fase 9 — Reservas
- [ ] Fase 10 — Garantías
- [ ] Fase 11 — Reclamos
- [ ] Fase 12 — Cierre

## Estado actual (21/11/2026)

**Verificado:** `uv run pytest` pasa 54 tests, `ruff` está limpio, y `npm run build`, `typecheck` y `oxlint` pasan sin errores ni avisos. `docker compose up` levanta todo y la app responde en `localhost:8080`.

**Fase 0:** completa. Además, `schema.sql` ya tiene las 26 tablas del DER y `catalogos.sql` carga los catálogos. Las clases SQLModel solo existen para `usuarios`: las demás se escriben en su fase.

**Fase 1:** completa y probada en el navegador con los dos roles.
- `POST /auth/login`, `GET /auth/me` con permisos por rol, `Logueado` y `SoloAdmin`, y el script `crear_admin`.
- ABM de usuarios: `GET`, `POST` y `PATCH /usuarios` (solo admin). El `PATCH` también activa o desactiva y blanquea la contraseña. El hash nunca sale en las respuestas y el email es único sin importar mayúsculas.
- Errores de validación en español y con el mismo formato por campo (`ErrorDeCampo` en `core/excepciones.py`) para que el front los muestre junto a cada input.
- Tests: login, token vencido, usuario desactivado, Vendedor con 403 y el ABM completo.
- En el front: login, guards, menú por permisos y la pantalla de Usuarios (tabla, alta y edición en un `Sheet`, activar o desactivar con confirmación).

**Fase 2:** completa y probada en el navegador con los dos roles.
- `GET /tipo-cambio/hoy` (todos) y `PUT /tipo-cambio/hoy` (solo admin, carga o corrige el de hoy). Sin TC devuelve `valor_ars: null`: no hay valor por defecto ni se arrastra el de ayer.
- "Hoy" es el día en Argentina (`ZONA_HORARIA`, por defecto `America/Argentina/Buenos_Aires`, en `core/reloj.py`), no el del servidor en UTC.
- El Value Object `Pesos` acepta el número JSON o el formato argentino (`1.180,50`).
- `GET /resumen` devuelve `fecha` y `avisos` (por ahora solo `tc_sin_cargar`). Cada fase suma lo suyo.
- En el front: feature `tipo-cambio` (aviso con carga para el admin, tarjeta con "Corregir" e indicador en el encabezado) y Resumen. Se refresca cada 2 minutos y al volver a la pestaña, así el cambio llega a las otras computadoras y a la medianoche vuelve a faltar.
- Token de color `warning` en `index.css` para avisos que no son errores.

**Decisiones confirmadas (21/11/2026):**
- Los usuarios se **desactivan, no se borran**, porque ventas y reservas guardan `usuario_id`.
- El admin no puede desactivarse ni quitarse el rol a sí mismo, y el sistema nunca queda sin un Administrador activo.

## Cómo se trabaja cada fase

1. **Modelo:** tablas en `schema.sql` y clases SQLModel de la fase.
2. **Lógica:** repository y service, más tests unitarios de dominio, estados y estrategias.
3. **API:** router, schemas por rol y tests de API con pytest y httpx.
4. **Tipos:** regenerar los tipos del front con openapi-typescript.
5. **Front:** `api.ts`, `queries.ts` y las pantallas de la feature.
6. **Prueba manual:** en el navegador, con los dos roles (Administrador y Vendedor).
7. **Commit** de la fase.

**Una fase está terminada cuando** pasan los tests, la pantalla funciona con datos reales y el Vendedor no ve nada que no debe (costos, ganancias, pantallas de admin).

---

## Fase 0 — Base del proyecto
- **Backend:**
  - estructura `backend/app/` con `core/` (config, sesión, excepciones, `UnidadDeTrabajo`), `common/` (`RepositorioBase`, paginación, Value Objects `USD`, `IMEI`, `DNI`, `Telefono`) y `GET /api/health`;
  - pytest configurado con SQLite en memoria.
- **Frontend:**
  - proyecto Vite en `web/` con router, `QueryClient` y cliente HTTP;
  - script para generar los tipos de la API;
  - componentes base de `shared/ui` y layout vacío.
- **Infra:** Docker Compose (`db`, `api`, `web`) y Nginx reenviando `/api`.
- **Listo cuando:** `docker compose up` muestra la app vacía y `/api/health` responde.

## Fase 1 — Login, sesión y usuarios
- **Backend:**
  - tabla `usuarios`, hash con Argon2, `POST /auth/login` (JWT de 60 minutos);
  - `GET /auth/me` con el rol y la lista de permisos;
  - dependencias `Logueado` y `SoloAdmin`;
  - un administrador inicial cargado por seed;
  - ABM de usuarios (solo admin).
- **Frontend:**
  - pantalla de login y `AuthContext`;
  - rutas protegidas con `<RequiereRol>`;
  - menú armado según el rol;
  - un 401 limpia la sesión y vuelve al login;
  - pantalla de usuarios.
- **Pruebas:** login correcto e incorrecto, token vencido, Vendedor sin acceso a usuarios.
- **Listo cuando:** se entra con los dos roles, cada uno ve su menú y el Vendedor no puede abrir las pantallas de admin, ni por la URL.

## Fase 2 — TC del día y esqueleto de Resumen
- **Backend:**
  - `tipos_cambio` con `PUT /tipo-cambio/hoy` (admin) y `GET /tipo-cambio/hoy`;
  - `GET /resumen` que por ahora devuelve solo el aviso de TC no cargado.
- **Frontend:** pantalla Resumen con el aviso y la carga del TC (solo Administrador).
- **Listo cuando:** cada día arranca sin TC, el aviso aparece, el admin lo carga y el aviso desaparece para todos.

> Desde acá, cada fase le suma a Resumen sus propios indicadores.

## Fase 3 — Catálogos
- **Backend:**
  - tablas `tipos_categoria`, `categorias`, `modelos`, `capacidades`, `colores`, `proveedores`, `defectos`, `localidades`, `diagnosticos`, `estados_reclamo` y `metodos_pago`;
  - seed con los valores de las reglas;
  - ABMC genérico.
- **Frontend:** una pantalla genérica de catálogos para el admin. Modelos, capacidades y colores se filtran por categoría.
- **Listo cuando:** se pueden ver, agregar y editar todos los catálogos, y la base trae precargadas las listas de las reglas.

## Fase 4 — Productos y stock
- **Backend:**
  - `productos` y `producto_defectos`;
  - `ProductoFactory`, que valida los datos según el tipo de categoría y que capacidad y color sean de la categoría del modelo;
  - State `EstadoProducto`;
  - IMEI con Luhn y sin duplicados, y las validaciones de precio y costo;
  - `bateria_nivel`;
  - DTOs `ProductoReadVendedor` y `ProductoReadAdmin`.
- **Frontend:**
  - listado de stock con filtros;
  - alta y edición con campos que cambian según la categoría;
  - defectos, que se eligen de la lista o se escriben a mano;
  - color de batería.
- **Resumen:** stock disponible y cuántas unidades son nuevas.
- **Listo cuando:** se cargan equipos con IMEI, consolas y accesorios, y el Vendedor ve el stock sin costos.

## Fase 5 — Clientes
- **Backend:** `clientes` con DNI único y teléfono validado, búsqueda por nombre y DNI, y ficha del cliente.
- **Frontend:** listado, alta y edición, y un buscador reutilizable que después usan venta y reserva. La ficha arranca con datos básicos y se completa en las fases siguientes.
- **Listo cuando:** se buscan, crean y editan clientes desde los dos roles.

## Fase 6 — Vendedores y packs
- **Backend:**
  - ABM de `vendedores`;
  - `packs` y `pack_items`, cada ítem con un producto fijo o una categoría;
  - `POST /packs/{id}/aplicar`.
- **Frontend:** ABM de vendedores y de packs (solo admin).
- **Listo cuando:** aplicar un pack devuelve los productos correctos sin repetir equipos.

## Fase 7 — Ventas al contado y canje
- **Backend:**
  - `ventas` y `venta_items`;
  - Strategy `ModalidadPago` con `Contado`;
  - `POST /ventas/cotizar`, que devuelve total, saldo y la advertencia de "bajo costo" solo para el admin;
  - `POST /ventas` dentro de la Unit of Work, con TC congelado, stock vía State, regalos, canje vía `ProductoFactory.desde_canje` y garantía en meses;
  - historial con DTOs por rol;
  - `DELETE /ventas/{id}`, que devuelve el stock.
- **Frontend:**
  - wizard de 5 pasos (equipos → cliente → modalidad → pago y canje → vendedor) con el carrito en `useReducer`;
  - cotización en cada cambio;
  - historial de ventas.
- **Pruebas:** atomicidad (si falla un paso no queda nada grabado), stock después de vender y de borrar, y el Vendedor sin costos.
- **Resumen:** ventas de hoy y de los últimos 7 días.
- **Decisión pendiente antes de esta fase:** si no hay TC cargado, ¿la venta se bloquea?

## Fase 8 — Cuotas, cobros y agenda
- **Backend:**
  - Strategy `EnCuotas` (de 2 a 60, redondeo con ajuste en la última, fin de mes, primera cuota hoy);
  - funciones puras en `ventas.dominio` con tests de casos borde;
  - `cobros` con State `EstadoCobro` (Vencida se calcula, no se guarda);
  - saldo del cliente y si está "en mora";
  - comprobante en PDF con ReportLab.
- **Frontend:**
  - modalidad en cuotas dentro del wizard;
  - agenda mensual donde se marcan las cuotas como cobradas;
  - plan de cuotas en la ficha del cliente;
  - descarga del comprobante.
- **Resumen:** cobros del mes y alertas de cuotas vencidas.
- **Listo cuando:** el ejemplo de las reglas (US$ 1.000 en 6 cuotas = 5 × 167 + 165) se genera bien y se puede cobrar desde la agenda.

## Fase 9 — Reservas
- **Backend:**
  - `reservas` y `reserva_items` con State `EstadoReserva`;
  - seña con TC congelado;
  - crear, convertir en venta (reutiliza `ModalidadPago`, con la seña como anticipo), cancelar y eliminar, todo con Unit of Work.
- **Frontend:**
  - reservar el carrito desde el wizard;
  - listado de reservas;
  - convertir (reutiliza los pasos de modalidad y pago), cancelar y eliminar;
  - reservas en la ficha del cliente.
- **Resumen:** reservas activas.
- **Listo cuando:** reservar bloquea los productos, cancelar los libera y convertir genera la venta y sus cuotas.

## Fase 10 — Garantías
- **Backend:**
  - Adapter `AlmacenArchivos`, con `AlmacenR2` en producción y `AlmacenEnMemoria` en los tests;
  - subida de 1 PDF o hasta 2 JPG;
  - URL firmada para ver el archivo;
  - vencimientos de garantía.
- **Frontend:** adjuntar y ver el comprobante desde el historial (el Vendedor solo en sus ventas) y vencimientos en la agenda.
- **Resumen:** garantías que vencen en los próximos 30 días.
- **Listo cuando:** se sube un comprobante a R2, se ve con link temporal y aparece la alerta de vencimiento.

## Fase 11 — Reclamos
- **Backend:** `reclamos` con diagnóstico y estado de catálogo, más la resolución.
- **Frontend:** carga y seguimiento desde la ficha del cliente.
- **Listo cuando:** la ficha del cliente muestra compras, cuotas, reservas y reclamos.

## Fase 12 — Cierre
- Servicio `datos` con datos de demo (`--profile demo`).
- Recorrido completo con los dos roles.
- Revisión de permisos endpoint por endpoint.
- Puesta en producción.

---

## Decisiones pendientes
1. **Migraciones:** el README ya usa `schema.sql` y `docker compose down -v` cuando cambia el esquema, así que todo indica que se descartó Alembic. Falta confirmarlo.
2. **TC sin cargar en una venta:** se necesita la respuesta antes de la Fase 7.
