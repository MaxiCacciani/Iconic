import { Navigate, useLocation } from "react-router"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card"

import { useAuth } from "../AuthProvider"
import { LoginForm } from "../components/LoginForm"

export function LoginPage() {
  const { estado } = useAuth()
  const location = useLocation()
  const destino = (location.state as { desde?: string } | null)?.desde ?? "/"

  if (estado === "activa") return <Navigate to={destino} replace />

  return (
    <main className="flex min-h-svh items-center justify-center bg-muted p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="font-heading text-3xl">Iconic</CardTitle>
          <CardDescription>Ingresá con tu email y contraseña.</CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </main>
  )
}
