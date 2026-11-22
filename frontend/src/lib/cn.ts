import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Compose conditional Tailwind classes, resolving conflicts in favour of the last one. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
