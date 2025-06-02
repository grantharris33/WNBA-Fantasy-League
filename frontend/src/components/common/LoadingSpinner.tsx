import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'md'
}) => {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  };

  return (
    <div className="flex flex-col justify-center items-center py-8">
      <div className={`loading-spinner ${sizeClasses[size]} mb-3`}></div>
      <p className="text-sm text-gray-600 font-medium">{message}</p>
    </div>
  );
};

export default LoadingSpinner;