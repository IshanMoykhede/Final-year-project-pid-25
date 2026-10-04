import React from 'react';
import { cn } from './Button';

interface EyebrowProps {
  children: React.ReactNode;
  className?: string;
  light?: boolean;
}

export const Eyebrow: React.FC<EyebrowProps> = ({ children, className, light }) => {
  return (
    <p className={cn(`mb-3 font-mono text-xs font-semibold tracking-wider uppercase ${light ? 'text-brass-soft' : 'text-brass-deep'}`, className)}>
      {children}
    </p>
  );
};
