import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"

import { AuthProvider } from "@/features/auth"
import { ApiError } from "@/shared/api"
import { Toaster } from "@/shared/ui/sonner"
import { ThemeProvider } from "@/shared/ui/theme-provider"
import { TooltipProvider } from "@/shared/ui/tooltip"

// Reintentar solo errores de red o del servidor; un 4xx no se arregla reintentando.
function reintentar(intentos: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500)
    return false
  return intentos < 2
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: reintentar },
    mutations: { retry: false },
  },
})

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider>
            {children}
            <Toaster richColors position="top-right" />
          </TooltipProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  )
}
