import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'small' | 'medium' | 'large';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, className, variant = 'primary', size = 'medium', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`button ${variant} ${size} ${className || ''}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button'; 