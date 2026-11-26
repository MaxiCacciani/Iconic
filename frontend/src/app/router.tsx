import type { ComponentType } from "react"
import { createBrowserRouter } from "react-router"

import { LoginPage } from "@/features/auth"

import { RequierePermiso, RequiereSesion } from "./guards"
import { AppLayout } from "./layouts/AppLayout"
import { SECCIONES } from "./navegacion"
import { ErrorPage } from "./pages/ErrorPage"
import { NoEncontradoPage } from "./pages/NoEncontradoPage"

export const router = createBrowserRouter([
  { path: "/login", Component: LoginPage, ErrorBoundary: ErrorPage },
  {
    path: "/",
    element: (
      <RequiereSesion>
        <AppLayout />
      </RequiereSesion>
    ),
    // Si falla algo fuera de las secciones (el layout), la página entera muestra el error.
    ErrorBoundary: ErrorPage,
    children: [
      {
        // Los errores de una sección se muestran dentro del layout: el menú sigue a mano.
        ErrorBoundary: ErrorPage,
        children: [
          // Cada sección se carga recién cuando se abre (un chunk por feature).
          ...SECCIONES.flatMap(({ ruta, permiso, cargar, detalle }) => {
            const conPermiso =
              (cargarPagina: () => Promise<ComponentType>) => async () => {
                const Pagina = await cargarPagina()
                return {
                  Component: () => (
                    <RequierePermiso permiso={permiso}>
                      <Pagina />
                    </RequierePermiso>
                  ),
                }
              }
            return [
              {
                ...(ruta === "/" ? { index: true } : { path: ruta.slice(1) }),
                lazy: conPermiso(cargar),
              },
              ...(detalle
                ? [{ path: `${ruta.slice(1)}/:id`, lazy: conPermiso(detalle) }]
                : []),
            ]
          }),
          { path: "*", Component: NoEncontradoPage },
        ],
      },
    ],
  },
])
