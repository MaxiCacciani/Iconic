# Frontend (frontend/)

## UI: siempre shadcn/ui

Toda la interfaz se arma con **shadcn/ui** (estilo `radix-nova`, primitivas de Radix, Tailwind CSS 4). Antes de escribir un componente visual a mano, buscalo en shadcn.

- **MCP `shadcn`** (configurado en `/.mcp.json`, apunta a `frontend/`): usalo para buscar componentes, ver ejemplos y obtener el comando de instalación (`search_items_in_registries`, `view_items_in_registries`, `get_item_examples_from_registries`, `get_add_command_for_items`). Al terminar una pantalla, corré `get_audit_checklist`.
- **Agregar componentes:** desde `frontend/`, `npx shadcn@latest add <componente>`. No copiar código de la web ni escribir a mano una primitiva que shadcn ya tiene (botón, input, select, dialog, sheet, table, form, toast/sonner, etc.).
- **Dónde quedan** (alias de `components.json`):
  - `@/shared/ui/*`: componentes de shadcn. Se pueden ajustar estilos, pero no meterles lógica de negocio ni llamadas a la API.
  - `@/shared/lib/utils`: `cn()` para combinar clases.
  - `@/shared/hooks`: hooks que traiga shadcn.
- Las pantallas y componentes de una feature (`features/<modulo>/components`) **componen** los de `@/shared/ui`; no reimplementan estilos base.
- **Íconos:** Phosphor (`@phosphor-icons/react`, por ejemplo `import { XIcon } from "@phosphor-icons/react"`). `components.json` tiene `iconLibrary: "phosphor"`, así que shadcn ya instala los componentes con Phosphor. No usar `lucide-react`.
- **Tema:** los colores, radios y fuentes son tokens CSS en `src/index.css` (`bg-background`, `text-muted-foreground`, `border-border`, etc.). No usar colores sueltos de Tailwind (`bg-blue-500`) ni hex. Modo claro/oscuro con `ThemeProvider` (`src/shared/ui/theme-provider.tsx`).
- **Fuentes:** Geist para el texto (`font-sans`, default) y Bodoni Moda para títulos (`font-heading`).

## Stack de diseño (skills)

Todo trabajo de UI usa estas skills, instaladas en `.claude/skills/` (versionadas en el repo, con `skills-lock.json`). Cada una tiene un rol; no se reemplazan entre sí.

| # | Skill | Rol | Cuándo |
|---|---|---|---|
| 1 | `ui-ux-pro-max` | Sistema de diseño: estilo, paleta, tipografías, tokens | Al definir o cambiar el look del sistema o de una pantalla nueva |
| 2 | `frontend-design` | Dirección visual con identidad propia, sin aspecto de plantilla | Al diseñar una pantalla o rediseñar una existente |
| 3 | `ux-ui-skills` (índice) y sus 10 sub-skills | Flujos, estados e interacciones desde el usuario; anclar todo al sistema real | Antes de construir (flujo y estados) y durante (jerarquía, interacción, copy) |
| 4 | `web-design-guidelines` | Auditoría contra las Web Interface Guidelines de Vercel | Al terminar una pantalla, antes de commitear |
| 5 | `shadcn` + MCP `shadcn` | Implementación con componentes reales de shadcn/ui | Siempre que se escriba UI |

Sub-skills de `ux-ui-skills` (invocables por nombre):
- Base: `bootstrapping-design-context`, `grounding-before-designing`, `design-judgment-references`.
- Diseño: `flow-doc-first`, `designing-states-not-screens`, `visual-hierarchy-and-type`, `interaction-craft`, `precision-copy-and-formatting`.
- Auditoría: `grilling-ui`, `anti-slop-audit`.

### Flujo para una pantalla nueva

1. **Flujo y estados** (`flow-doc-first`, `designing-states-not-screens`): qué hace el usuario y cómo se ve en carga, vacío, error y sin permisos. Los estados salen de lo que devuelve la API (401, 403, 422, listas vacías), no se inventan reglas.
2. **Diseño visual** (`ui-ux-pro-max`, `frontend-design`, `visual-hierarchy-and-type`): siempre dentro de los tokens de `src/index.css`. Si hace falta un token nuevo, se agrega ahí, no como valor suelto.
3. **Implementación** (`shadcn` + MCP): componer con `@/shared/ui`; `interaction-craft` y `precision-copy-and-formatting` para feedback, foco, montos (`US$ 1.250`) y fechas (`dd/mm/aaaa`).
4. **Auditoría** (`web-design-guidelines`, `anti-slop-audit`, `get_audit_checklist` del MCP): corregir lo que salga antes de dar la pantalla por terminada.

### Reglas que ganan sobre las skills

Las skills son genéricas; si chocan con el proyecto, manda el proyecto:
- Stack fijo: shadcn/ui + Tailwind 4, íconos **Phosphor**, fuentes **Geist / Bodoni Moda**, animaciones con **Motion**. No sumar otras librerías de UI, íconos, fuentes ni animación (por ejemplo GSAP) aunque una skill lo sugiera.
- El front no decide nada (ver `stack.md`): ningún diseño puede requerir cálculos o validaciones en el cliente.
- Los scripts de `ui-ux-pro-max` son de consulta; no generan archivos dentro de `frontend/`.
- La skill `shadcn` lee el proyecto con `--cwd frontend` (ajuste local en `.claude/skills/shadcn/SKILL.md`, línea 17). Si se actualizan las skills con `npx skills update -p`, volver a aplicarlo.

## Comandos

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # tsc -b + vite build
npm run typecheck
npm run lint       # oxlint (config en .oxlintrc.json; no usamos ESLint porque no soporta TS 7)
npm run format     # prettier + orden de clases de Tailwind
npm run gen:api    # tipos de la API desde el OpenAPI (con el backend corriendo en :8000)
```

## Esqueleto

- **Menú y rutas:** `src/app/navegacion.ts`. Cada sección declara su `permiso` (de `GET /auth/me`); el sidebar y el router se arman desde esa lista. Una pantalla nueva se agrega ahí.
- **Sesión:** `features/auth` (`AuthProvider`, `useAuth().puede(permiso)`). Un 401 con token limpia la sesión y vuelve al login.
- **API:** `shared/api` (`pedir()`, `ApiError` con `campos` para los 422). Los tipos salen de `schema.d.ts` (generado, no editar).
- **Formato:** `shared/lib/formato.ts` (`formatearUSD`, `formatearARS`, `formatearFecha`).
- **Docker:** `frontend/Dockerfile` (build + Nginx) y `frontend/nginx.conf` (`/api/*` → `api:8000`). En dev, el proxy de `vite.config.ts` hace lo mismo.

La estructura de carpetas (`app/`, `features/<modulo>/`, `shared/`) y las reglas de capas están en `stack.md` (importado desde el `CLAUDE.md` raíz).
