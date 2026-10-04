import React from 'react';
import { cn } from './Button';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || Math.random().toString(36).substring(7);

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block font-sans text-xs font-semibold uppercase tracking-wider text-charcoal/80 mb-1.5">
            {label}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded-2xl border border-sand bg-parchment/40 px-4 py-2.5 text-charcoal placeholder:text-muted focus:outline-none focus:border-brass focus:ring-2 focus:ring-brass/15 disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
            error && 'border-crimson/50 focus:ring-crimson/20',
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-xs font-mono text-crimson">{error}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';
