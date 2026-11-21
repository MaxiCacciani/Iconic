import {
  CaretUpDownIcon,
  DesktopIcon,
  MoonIcon,
  SignOutIcon,
  SunIcon,
} from "@phosphor-icons/react"
import { NavLink, useLocation } from "react-router"

import { useAuth } from "@/features/auth"
import { Avatar, AvatarFallback } from "@/shared/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/shared/ui/sidebar"
import { useTheme } from "@/shared/ui/theme-provider"

import { SECCIONES, type Seccion } from "../navegacion"

const ROLES: Record<string, string> = {
  admin: "Administrador",
  vendedor: "Vendedor",
}

export function AppSidebar() {
  const { puede } = useAuth()
  const { pathname } = useLocation()
  const visibles = SECCIONES.filter((seccion) => puede(seccion.permiso))
  const grupos = new Map<Seccion["grupo"], Seccion[]>()
  for (const seccion of visibles)
    grupos.set(seccion.grupo, [...(grupos.get(seccion.grupo) ?? []), seccion])

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex h-10 items-center px-2 font-heading text-2xl group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0">
          <span className="group-data-[collapsible=icon]:hidden">Iconic</span>
          <span className="hidden group-data-[collapsible=icon]:inline">I</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {[...grupos].map(([grupo, secciones]) => (
          <SidebarGroup key={grupo}>
            <SidebarGroupLabel>{grupo}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {secciones.map(({ ruta, titulo, icono: Icono }) => {
                  const activa =
                    ruta === "/" ? pathname === "/" : pathname.startsWith(ruta)
                  return (
                    <SidebarMenuItem key={ruta}>
                      <SidebarMenuButton
                        asChild
                        isActive={activa}
                        tooltip={titulo}
                      >
                        <NavLink to={ruta} end={ruta === "/"}>
                          <Icono />
                          <span>{titulo}</span>
                        </NavLink>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>
        <MenuUsuario />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

function MenuUsuario() {
  const { sesion, cerrarSesion } = useAuth()
  const { theme, setTheme } = useTheme()
  if (!sesion) return null

  const iniciales = sesion.nombre
    .split(" ")
    .slice(0, 2)
    .map((parte) => parte[0]?.toUpperCase())
    .join("")

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent"
            >
              <Avatar className="size-8 rounded-lg">
                <AvatarFallback className="rounded-lg">
                  {iniciales}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{sesion.nombre}</span>
                <span className="truncate text-xs text-muted-foreground">
                  {ROLES[sesion.rol] ?? sesion.rol}
                </span>
              </div>
              <CaretUpDownIcon className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="min-w-56">
            <DropdownMenuLabel className="font-normal">
              <span className="block truncate text-xs text-muted-foreground">
                {sesion.email}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Tema
            </DropdownMenuLabel>
            <DropdownMenuRadioGroup
              value={theme}
              onValueChange={(valor) => setTheme(valor as typeof theme)}
            >
              <DropdownMenuRadioItem value="light">
                <SunIcon /> Claro
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="dark">
                <MoonIcon /> Oscuro
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="system">
                <DesktopIcon /> Sistema
              </DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={cerrarSesion}>
              <SignOutIcon /> Cerrar sesión
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
