'use client';

import { forwardRef } from 'react';

const Checkbox = forwardRef(({ className, checked, onChange, ...props }, ref) => {
  return (
    <input
      type="checkbox"
      className={`h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded ${className}`}
      ref={ref}
      checked={checked}
      onChange={onChange}
      {...props}
    />
  );
});

Checkbox.displayName = 'Checkbox';

export { Checkbox };