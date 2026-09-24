import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'brass' | 'stone';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-charcoal text-ivory hover:bg-charcoal-deep border border-charcoal dark:bg-sand dark:text-charcoal dark:hover:bg-ivory dark:border-sand shadow-subtle',
      secondary: 'bg-parchment text-charcoal hover:bg-sand border border-sand dark:bg-stone dark:text-ivory dark:border-stone-muted',
      outline: 'border border-border bg-transparent hover:bg-parchment text-charcoal dark:text-ivory dark:hover:bg-stone',
      ghost: 'bg-transparent hover:bg-parchment text-charcoal dark:text-ivory dark:hover:bg-stone',
      danger: 'bg-crimson text-white hover:bg-crimson-deep border border-crimson',
      brass: 'bg-brass text-white hover:bg-brass-deep border border-brass shadow-subtle',
      stone: 'bg-stone text-ivory hover:bg-stone-muted border border-stone',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs tracking-tight rounded',
      md: 'h-9 px-4 py-1.5 text-sm font-medium rounded',
      lg: 'h-11 px-5 text-base font-medium rounded',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center font-sans font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brass disabled:pointer-events-none disabled:opacity-40 cursor-pointer select-none',
          variants[variant as keyof typeof variants] || variants.primary,
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin text-current" />}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
