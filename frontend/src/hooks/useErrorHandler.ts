import { useCallback } from 'react';
import { toast } from 'react-toastify';

export interface ApiError extends Error {
  status?: number;
  details?: unknown;
}

export const useErrorHandler = () => {
  const handleError = useCallback((error: unknown, context?: string) => {
    console.error(context ? `Error in ${context}:` : 'Error:', error);
    
    let message = 'An unexpected error occurred';
    
    if (error instanceof Error) {
      message = error.message;
    } else if (typeof error === 'string') {
      message = error;
    }
    
    // Handle specific API errors
    if (error && typeof error === 'object' && 'status' in error) {
      const apiError = error as ApiError;
      switch (apiError.status) {
        case 401:
          message = 'You are not authorized. Please log in again.';
          // Could trigger logout here
          break;
        case 403:
          message = 'You do not have permission to perform this action.';
          break;
        case 404:
          message = 'The requested resource was not found.';
          break;
        case 500:
          message = 'Server error. Please try again later.';
          break;
        default:
          // Use the API error message if available
          if (apiError.message) {
            message = apiError.message;
          }
      }
    }
    
    toast.error(message);
    return message;
  }, []);

  const handleAsyncError = useCallback(async <T>(
    asyncFn: () => Promise<T>,
    context?: string,
    onError?: (error: unknown) => void
  ): Promise<T | null> => {
    try {
      return await asyncFn();
    } catch (error) {
      handleError(error, context);
      onError?.(error);
      return null;
    }
  }, [handleError]);

  return {
    handleError,
    handleAsyncError,
  };
};

export default useErrorHandler;