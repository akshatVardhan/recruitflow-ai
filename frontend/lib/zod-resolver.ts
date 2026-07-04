import type { FieldErrors, Resolver } from "react-hook-form"
import { z } from "zod"

type Values<T extends z.ZodTypeAny> = z.infer<T>

/**
 * Minimal RHF resolver built on zod. Replicates the subset of
 * @hookform/resolvers/zod we need, without adding that dependency.
 * Produces nested FieldErrors keyed by the zod issue path.
 */
export function zodResolver<T extends z.ZodTypeAny>(schema: T): Resolver<Values<T>> {
  const resolver = async (values: Values<T>) => {
    const result = schema.safeParse(values)
    if (result.success) {
      return {
        values: result.data,
        errors: {} as FieldErrors<Values<T>>,
      }
    }
    const errors = {} as FieldErrors<Values<T>>
    for (const issue of result.error.issues) {
      setNested(
        errors as unknown as Record<string, unknown>,
        issue.path as Array<string | number>,
        { message: issue.message, type: issue.code }
      )
    }
    return {
      values: {} as Values<T>,
      errors,
    }
  }
  return resolver as Resolver<Values<T>>
}

function setNested(
  target: Record<string, unknown>,
  path: Array<string | number>,
  leaf: unknown
): void {
  let cursor: Record<string, unknown> = target
  for (let i = 0; i < path.length; i++) {
    const key = path[i]
    const isLast = i === path.length - 1
    if (isLast) {
      // First observed message wins (consistent with @hookform/resolvers).
      if (cursor[key] === undefined) {
        cursor[key] = leaf
      }
    } else {
      const nextKey = path[i + 1]
      const shouldBeArray = typeof nextKey === "number"
      if (cursor[key] === undefined) {
        cursor[key] = shouldBeArray ? [] : {}
      }
      cursor = cursor[key] as Record<string, unknown>
    }
  }
}
