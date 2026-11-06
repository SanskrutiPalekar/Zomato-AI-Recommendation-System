import React from 'react';
import SearchForm from './components/SearchForm';
import ResultsPanel from './components/ResultsPanel';
import LoadingSpinner from './components/LoadingSpinner';
import { useRecommendations } from './hooks/useRecommendations';

export default function App() {
  const { cities, status, data, error, search } = useRecommendations();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-red-600 text-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight">
              Zomato AI Restaurant Concierge
            </h1>
            <p className="text-sm text-red-100">
              Personalized Bangalore dining picks powered by RAG & Groq LLM
            </p>
          </div>
          <span className="text-xs bg-red-700/80 px-3 py-1 rounded-full font-medium self-start sm:self-auto">
            Step 6 • Web UI
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <SearchForm
          cities={cities}
          onSearch={search}
          isLoading={status === 'loading'}
        />

        {status === 'idle' && (
          <div
            data-testid="welcome-banner"
            className="bg-white rounded-2xl border border-gray-200 p-10 text-center text-gray-600"
          >
            <p className="text-lg font-semibold text-gray-800 mb-1">
              Ready to discover your next meal?
            </p>
            <p className="text-sm text-gray-500">
              Select a Bangalore locality, enter your budget for two, and let our AI Concierge curate the top spots.
            </p>
          </div>
        )}

        {status === 'loading' && <LoadingSpinner />}

        {status === 'error' && (
          <div
            role="alert"
            data-testid="error-banner"
            className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center"
          >
            <p className="text-red-700 font-semibold mb-1">
              Could not fetch recommendations
            </p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {status === 'success' && <ResultsPanel data={data} />}
      </main>
    </div>
  );
}

