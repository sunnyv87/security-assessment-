import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Severity } from '@/types/finding';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const severityColors: Record<Severity, string> = {
  critical: 'bg-severity-critical text-white',
  high: 'bg-severity-high text-white',
  medium: 'bg-severity-medium text-white',
  low: 'bg-severity-low text-white',
  info: 'bg-severity-info text-white',
};

export const severityOrder: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 1) + '\u2026';
}
