import { createBrowserRouter } from "react-router"

import { LoginPage } from "@/features/auth"

import { RequierePermiso, RequiereSesion } from "./guards"
import { AppLayout } from "./layouts/AppLayout"
import { SECCIONES } from "./navegacion"
import { NoEncontradoPage } from "./pages/NoEncontradoPage"

export const router = createBrowserRouter([
  { path: "/login", Component: LoginPage },
  {
    path: "/",
    element: (
      <RequiereSesion>
        <AppLayout />
      </RequiereSesion>
    ),
    children: [
      // Cada sección se carga recién cuando se abre (un chunk por feature).
      ...SECCIONES.map(({ ruta, permiso, cargar }) => ({
        ...(ruta === "/" ? { index: true } : { path: ruta.slice(1) }),
        lazy: async () => {
          const Pagina = await cargar()
          return {
            Component: () => (
              <RequierePermiso permiso={permiso}>
                <Pagina />
              </RequierePermiso>
            ),
          }
        },
      })),
      { path: "*", Component: NoEncontradoPage },
    ],
  },
])
