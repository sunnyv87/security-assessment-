'use client';

import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: boolean;
}

export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={cn('rounded-lg border border-gray-200 bg-white shadow-sm', padding && 'p-6', className)}>
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function CardHeader({ title, description, action, className }: CardHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between', className)}>
      <div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  colorClass?: string;
  onClick?: () => void;
}

export function StatCard({ label, value, colorClass = 'text-gray-900', onClick }: StatCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex flex-col items-center rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md',
        onClick && 'cursor-pointer',
      )}
    >
      <span className={cn('text-3xl font-bold', colorClass)}>{value}</span>
      <span className="mt-1 text-sm font-medium text-gray-500">{label}</span>
    </button>
  );
}
