import React from 'react';

function getRatingBadgeClass(rating) {
  if (rating >= 4.0) return 'bg-green-600 text-white';
  if (rating >= 3.5) return 'bg-yellow-500 text-white';
  return 'bg-red-500 text-white';
}

export default function RecommendationCard({ recommendation }) {
  const {
    rank,
    restaurant_name,
    location,
    rating,
    cost_for_two,
    cuisines,
    online_order,
    book_table,
    ai_rationale,
    must_try_dishes = [],
    budget_saving,
    budget_verdict,
  } = recommendation;

  const badgeClass = getRatingBadgeClass(rating);

  return (
    <div
      data-testid="recommendation-card"
      className="bg-white rounded-2xl shadow-sm hover:shadow-md transition border border-gray-100 p-6 flex flex-col justify-between"
    >
      <div>
        {/* Top Row: Rank, Name, Rating */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-600 text-white text-xs font-bold">
              #{rank}
            </span>
            <h3 className="text-lg font-bold text-gray-900">{restaurant_name}</h3>
          </div>
          <span
            data-testid="rating-badge"
            className={`px-2.5 py-1 rounded-lg text-xs font-bold shrink-0 ${badgeClass}`}
          >
            ★ {Number(rating).toFixed(1)} / 5.0
          </span>
        </div>

        {/* Locality & Cuisines */}
        <p className="text-sm text-gray-500 mb-3">
          📍 <span className="font-medium text-gray-700">{location}</span>
          {cuisines && (
            <>
              {' • '}
              <span>{cuisines}</span>
            </>
          )}
        </p>

        {/* Price Pill & Budget Saving */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className="inline-block bg-gray-100 text-gray-800 text-xs font-semibold px-3 py-1 rounded-full">
            ₹{cost_for_two} for two
          </span>
          {budget_saving !== null && budget_saving !== undefined && budget_saving >= 0 && (
            <span
              data-testid="budget-saving-chip"
              className="inline-block bg-green-50 text-green-700 border border-green-200 text-xs font-medium px-3 py-1 rounded-full"
            >
              {budget_saving > 0
                ? `₹${budget_saving} below budget`
                : budget_verdict || 'Within budget'}
            </span>
          )}
        </div>

        {/* AI Rationale */}
        {ai_rationale && (
          <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 mb-4">
            <p className="text-xs font-semibold text-amber-800 uppercase tracking-wider mb-1">
              AI Concierge Rationale
            </p>
            <p className="text-sm text-gray-700 leading-relaxed">{ai_rationale}</p>
          </div>
        )}

        {/* Must-Try Dishes */}
        {must_try_dishes && must_try_dishes.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">
              Must-Try Dishes
            </p>
            <div className="flex flex-wrap gap-1.5">
              {must_try_dishes.map((dish) => (
                <span
                  key={dish}
                  className="bg-red-50 text-red-700 border border-red-100 text-xs font-medium px-2.5 py-1 rounded-md"
                >
                  🍽 {dish}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Service Badges */}
      <div className="pt-3 border-t border-gray-100 flex items-center gap-3 text-xs">
        <span
          className={`px-2.5 py-0.5 rounded font-medium ${
            online_order === 'Yes'
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-gray-100 text-gray-500'
          }`}
        >
          {online_order === 'Yes' ? '✓ Online Delivery' : '✗ No Delivery'}
        </span>
        <span
          className={`px-2.5 py-0.5 rounded font-medium ${
            book_table === 'Yes'
              ? 'bg-blue-50 text-blue-700'
              : 'bg-gray-100 text-gray-500'
          }`}
        >
          {book_table === 'Yes' ? '✓ Table Booking' : '✗ No Table Booking'}
        </span>
      </div>
    </div>
  );
}

