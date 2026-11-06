import React, { useState } from 'react';

const BUDGET_PRESETS = [
  { label: '< ₹500', value: 'under 500' },
  { label: '₹500–₹1000', value: '500 to 1000' },
  { label: 'Under ₹800', value: 'under 800' },
  { label: '> ₹1000', value: '1500' },
];

export default function SearchForm({ cities = [], onSearch, isLoading = false }) {
  const [city, setCity] = useState('');
  const [price, setPrice] = useState('');
  const [preferences, setPreferences] = useState('');
  const [validationError, setValidationError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!city.trim() || !price.trim()) {
      setValidationError('Please enter both a city/locality and a budget.');
      return;
    }
    setValidationError('');
    onSearch({
      city: city.trim(),
      price: price.trim(),
      preferences: preferences.trim() || undefined,
    });
  };

  const handlePresetClick = (presetValue) => {
    setPrice(presetValue);
    setValidationError('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      data-testid="search-form"
      className="bg-white rounded-2xl shadow-md border border-gray-100 p-6 mb-8"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* City Input / Select */}
        <div>
          <label
            htmlFor="city-input"
            className="block text-sm font-semibold text-gray-700 mb-1.5"
          >
            City / Locality *
          </label>
          <input
            id="city-input"
            list="city-options"
            type="text"
            value={city}
            onChange={(e) => {
              setCity(e.target.value);
              setValidationError('');
            }}
            placeholder="e.g. Koramangala, BTM, Banashankari"
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-200 outline-none transition"
          />
          <datalist id="city-options">
            {cities.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </div>

        {/* Budget Input */}
        <div>
          <label
            htmlFor="price-input"
            className="block text-sm font-semibold text-gray-700 mb-1.5"
          >
            Budget for Two (INR) *
          </label>
          <input
            id="price-input"
            type="text"
            value={price}
            onChange={(e) => {
              setPrice(e.target.value);
              setValidationError('');
            }}
            placeholder="e.g. under 800, 600, budget"
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-200 outline-none transition"
          />
          <div className="flex flex-wrap gap-1.5 mt-2">
            {BUDGET_PRESETS.map((preset) => (
              <button
                key={preset.value}
                type="button"
                onClick={() => handlePresetClick(preset.value)}
                className={`text-xs px-2.5 py-1 rounded-full border transition ${
                  price === preset.value
                    ? 'bg-red-600 text-white border-red-600'
                    : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Preferences Input */}
        <div>
          <label
            htmlFor="preferences-input"
            className="block text-sm font-semibold text-gray-700 mb-1.5"
          >
            Food / Vibe Preferences (Optional)
          </label>
          <input
            id="preferences-input"
            type="text"
            value={preferences}
            onChange={(e) => setPreferences(e.target.value)}
            placeholder="e.g. Biryani, Vegetarian, Cafe"
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-200 outline-none transition"
          />
        </div>
      </div>

      {validationError && (
        <p
          role="alert"
          data-testid="validation-error"
          className="text-red-600 text-sm font-medium mt-3"
        >
          {validationError}
        </p>
      )}

      <div className="mt-5 flex justify-end">
        <button
          type="submit"
          disabled={isLoading}
          data-testid="search-button"
          className="bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-semibold px-6 py-2.5 rounded-lg shadow-sm transition"
        >
          {isLoading ? 'Searching...' : 'Find Restaurants'}
        </button>
      </div>
    </form>
  );
}

