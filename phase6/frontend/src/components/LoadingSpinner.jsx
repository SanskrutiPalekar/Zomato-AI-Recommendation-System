import React from 'react';

export default function LoadingSpinner() {
  return (
    <div
      data-testid="loading-spinner"
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      <div className="w-12 h-12 border-4 border-red-200 border-t-red-600 rounded-full animate-spin mb-4" />
      <p className="text-lg font-semibold text-gray-800">
        Finding the best restaurants for you...
      </p>
      <p className="text-sm text-gray-500 mt-1">
        Consulting Zomato AI Concierge (Groq LLM)
      </p>
    </div>
  );
}

