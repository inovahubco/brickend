"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { login, signup } from '../actions/actions'
import { 
  LoginCredentialsSchema, 
  SignUpFormSchema,
  type LoginCredentials,
  type SignUpForm
} from '../schema/auth-schemas'
import { LoadingButton } from "@repo/ui/loading-button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@repo/ui/card"
import { Input } from "@repo/ui/input"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@repo/ui/form"

type AuthFormProps = {
  mode: 'login' | 'signup'
}

export function AuthForm({ mode }: AuthFormProps) {
  const isLogin = mode === 'login'
  const searchParams = useSearchParams()
  
  const schema = isLogin ? LoginCredentialsSchema : SignUpFormSchema
  const defaultValues = isLogin ? {
    email: searchParams.get('email') || '',
    password: '',
  } : {
    email: searchParams.get('email') || '',
    password: '',
    confirmPassword: '',
  }

  const form = useForm<LoginCredentials | SignUpForm>({
    resolver: zodResolver(schema),
    defaultValues,
  })

  async function onSubmit(values: LoginCredentials | SignUpForm) {
    const formData = new FormData()
    formData.append('email', values.email)
    formData.append('password', values.password)
    
    if (!isLogin) {
      formData.append('flow', searchParams.get('flow') || 'direct')
    }

    try {
      if (isLogin) {
        await login(formData)
      } else {
        await signup(formData)
      }
    } catch (error) {
      // Error handling is done in the server actions
      console.error('Auth error:', error)
    }
  }
  
  return (
    <Card className="w-full sm:w-[400px] min-h-[500px] mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">{isLogin ? 'Iniciar sesión' : 'Registrarse'}</CardTitle>
        <CardDescription>
          {isLogin 
            ? 'Ingresa tu correo electrónico para iniciar sesión'
            : 'Crea una cuenta para comenzar'
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Correo electrónico</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="m@ejemplo.com"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center">
                    <FormLabel>Contraseña</FormLabel>
                    {isLogin && (
                      <Link 
                        href="/forgot-password" 
                        className="ml-auto inline-block text-sm underline"
                      >
                        ¿Olvidaste tu contraseña?
                      </Link>
                    )}
                  </div>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder={isLogin ? "Ingresa tu contraseña" : "Crea una contraseña"}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!isLogin && (
              <FormField
                control={form.control}
                name="confirmPassword"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirmar contraseña</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Confirma tu contraseña"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <LoadingButton 
              type="submit" 
              className="w-full" 
              disabled={form.formState.isSubmitting}
              loading={form.formState.isSubmitting}
              loadingText={isLogin ? "Iniciando sesión..." : "Registrando..."}
            >
              {isLogin ? 'Iniciar sesión' : 'Registrarse'}
            </LoadingButton>
            
            <div className="mt-4 text-center text-sm">
              {isLogin ? (
                <>
                  ¿No tienes una cuenta?{" "}
                  <Link href="/signup" className="underline">
                    Regístrate
                  </Link>
                </>
              ) : (
                <>
                  ¿Ya tienes una cuenta?{" "}
                  <Link href="/login" className="underline">
                    Inicia sesión
                  </Link>
                </>
              )}
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}