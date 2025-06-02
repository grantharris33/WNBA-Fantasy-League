import React from 'react';

interface ErrorMessageProps {
  message: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  if (!message) return null;

  return (
    <div className="card p-4 border-red-200 bg-red-50">
      <div className="flex items-center">
        <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
          <span className="text-red-600 text-lg">⚠️</span>
        </div>
        <div>
          <h3 className="font-medium text-red-800">Error</h3>
          <p className="text-sm text-red-700">{message}</p>
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;