"use client"

import { Button } from "./button"
import { Loader2 } from "lucide-react"
import { useTransition } from 'react'

// if the loading button dont work, check the button component for the button props
interface LoadingButtonProps extends React.ComponentProps<typeof Button> {
  loading?: boolean
  loadingText?: string
  formAction?: (formData: FormData) => Promise<void> | void
}

export function LoadingButton({
  children,
  loading,
  loadingText,
  formAction,
  ...props
}: LoadingButtonProps) {
  const [isPending, startTransition] = useTransition()

  const handleFormAction = async (formData: FormData) => {
    if (!formAction) return
    
    startTransition(async () => {
      await formAction(formData)
    })
  }

  const isLoading = loading || isPending

  return (
    <Button 
      {...props} 
      disabled={isLoading} 
      formAction={formAction ? handleFormAction : undefined}
    >
      {isLoading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          {loadingText || children}
        </>
      ) : (
        children
      )}
    </Button>
  )
}