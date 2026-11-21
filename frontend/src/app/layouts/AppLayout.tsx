import { Suspense } from "react"
import { Outlet } from "react-router"

import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/shared/ui/sidebar"
import { Skeleton } from "@/shared/ui/skeleton"

import { AppSidebar } from "./AppSidebar"

/** Layout de la app logueada. El menú sale de los permisos, así Admin y Vendedor ven cada uno lo suyo. */
export function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger className="-ml-1" />
          {/* Acá va el aviso del TC del día cuando exista `GET /tipo-cambio/hoy`. */}
        </header>
        <main className="flex flex-1 flex-col gap-6 p-4 md:p-6">
          <Suspense fallback={<CargandoPagina />}>
            <Outlet />
          </Suspense>
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}

function CargandoPagina() {
  return (
    <div className="flex flex-col gap-4" role="status" aria-label="Cargando">
      <Skeleton className="h-9 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}
