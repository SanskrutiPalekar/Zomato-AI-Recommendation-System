import React from 'react';
import RecommendationCard from './RecommendationCard';

export default function ResultsPanel({ data }) {
  if (!data) return null;

  const {
    query,
    recommendations = [],
    overall_ai_summary,
    model_name,
    latency_ms,
    is_mock,
  } = data;

  return (
    <div data-testid="results-panel" className="space-y-6">
      {/* AI Concierge Summary Banner */}
      <div className="bg-white rounded-2xl shadow-sm border border-red-100 p-5">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <h2 className="text-base font-bold text-gray-900">
            🤖 AI Concierge Overview —{' '}
            <span className="text-red-600">{query?.city}</span> (Up to ₹
            {query?.budget})
          </h2>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="px-2 py-0.5 rounded bg-gray-100 font-medium text-gray-700">
              {is_mock ? 'Offline Mock Engine' : `Groq (${model_name})`}
            </span>
            {latency_ms !== undefined && <span>⚡ {latency_ms} ms</span>}
          </div>
        </div>
        {overall_ai_summary && (
          <p className="text-sm text-gray-700 leading-relaxed">
            {overall_ai_summary}
          </p>
        )}
      </div>

      {/* Recommendation Cards Grid */}
      {recommendations.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center text-gray-600 border border-gray-200">
          No matching restaurants found within your budget.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={`${rec.rank}-${rec.restaurant_name}`}
              recommendation={rec}
            />
          ))}
        </div>
      )}
    </div>
  );
}

