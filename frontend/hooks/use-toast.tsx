"use client"

// Lightweight toast state manager (shadcn-style, adapted to radix-toast).
// A single module-level emitter so any component can call `toast()` without
// pulling in a provider or context, while the <Toaster /> subscribes to
// render the active stack.

import * as React from "react"
import type { ToastProps } from "@/components/ui/toast"

export type Tone = "default" | "success" | "destructive" | "info"

export interface ToastOptions {
  title?: React.ReactNode
  description?: React.ReactNode
  variant?: NonNullable<ToastProps["variant"]>
  duration?: number
}

export interface ToastRecord extends Required<Omit<ToastOptions, "variant">> {
  id: string
  variant: NonNullable<ToastProps["variant"]>
}

type Listener = (toasts: ToastRecord[]) => void

let toasts: ToastRecord[] = []
const listeners = new Set<Listener>()

function emit() {
  for (const l of listeners) l(toasts)
}

function addToast(opts: ToastOptions): string {
  const id =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `t-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const record: ToastRecord = {
    id,
    title: opts.title ?? null,
    description: opts.description ?? null,
    variant: opts.variant ?? "default",
    duration: opts.duration ?? 4000,
  }
  toasts = [...toasts, record]
  emit()
  if (record.duration > 0) {
    setTimeout(() => dismissToast(id), record.duration)
  }
  return id
}

export function dismissToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id)
  emit()
}

/** Fire a toast from anywhere (event handlers, async flows, tests). */
export function toast(opts: ToastOptions): string {
  return addToast(opts)
}

/** Subscribe a component (the <Toaster />) to the active toast stack. */
export function useToast() {
  const [state, setState] = React.useState<ToastRecord[]>(toasts)
  React.useEffect(() => {
    const cb = (next: ToastRecord[]) => setState(next)
    listeners.add(cb)
    return () => {
      listeners.delete(cb)
    }
  }, [])
  return { toasts: state, dismiss: dismissToast }
}
