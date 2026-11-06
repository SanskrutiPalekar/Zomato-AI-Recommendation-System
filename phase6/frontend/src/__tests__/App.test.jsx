import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import SearchForm from '../components/SearchForm';
import RecommendationCard from '../components/RecommendationCard';
import ResultsPanel from '../components/ResultsPanel';
import * as apiClientModule from '../api/client';

vi.mock('../api/client', () => ({
  fetchCities: vi.fn(),
  fetchRecommendations: vi.fn(),
  checkHealth: vi.fn(),
}));

const MOCK_RECOMMENDATION_RESPONSE = {
  query: {
    city: 'Koramangala',
    budget: 800,
    preferences: 'Biryani',
  },
  recommendations: [
    {
      rank: 1,
      restaurant_name: 'Meghana Foods',
      location: 'Koramangala 1st Block',
      rating: 4.4,
      cost_for_two: 600,
      cuisines: 'Biryani, Andhra, South Indian',
      online_order: 'Yes',
      book_table: 'No',
      ai_rationale: 'Authentic spicy Andhra biryani well within your budget.',
      must_try_dishes: ['Chicken Boneless Biryani', 'Chilli Chicken'],
      budget_saving: 200,
      budget_verdict: 'Rs. 200 under your budget',
    },
  ],
  overall_ai_summary: 'Found 1 top biryani spot in Koramangala under Rs. 800.',
  model_name: 'openai/gpt-oss-120b',
  latency_ms: 420,
  candidate_count: 3,
  is_mock: false,
};

describe('Phase 6 React Frontend Unit & Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClientModule.fetchCities.mockResolvedValue({
      cities: ['Koramangala', 'Indiranagar', 'BTM'],
      total: 3,
    });
  });

  it('renders SearchForm and validates required inputs before submitting', () => {
    const onSearchMock = vi.fn();
    render(<SearchForm cities={['Koramangala']} onSearch={onSearchMock} />);

    const submitBtn = screen.getByTestId('search-button');
    fireEvent.click(submitBtn);

    expect(screen.getByTestId('validation-error')).toHaveTextContent(
      /Please enter both a city\/locality and a budget/i
    );
    expect(onSearchMock).not.toHaveBeenCalled();
  });

  it('allows selecting a budget preset chip and submits form payload', () => {
    const onSearchMock = vi.fn();
    render(<SearchForm cities={['Koramangala']} onSearch={onSearchMock} />);

    fireEvent.change(screen.getByLabelText(/City \/ Locality/i), {
      target: { value: 'Koramangala' },
    });
    fireEvent.click(screen.getByText('Under ₹800'));
    fireEvent.change(screen.getByLabelText(/Food \/ Vibe Preferences/i), {
      target: { value: 'Biryani' },
    });

    fireEvent.click(screen.getByTestId('search-button'));

    expect(onSearchMock).toHaveBeenCalledWith({
      city: 'Koramangala',
      price: 'under 800',
      preferences: 'Biryani',
    });
  });

  it('renders RecommendationCard with rating badge, savings chip, dishes, and rationale', () => {
    const rec = MOCK_RECOMMENDATION_RESPONSE.recommendations[0];
    render(<RecommendationCard recommendation={rec} />);

    expect(screen.getByText('Meghana Foods')).toBeInTheDocument();
    expect(screen.getByTestId('rating-badge')).toHaveTextContent('★ 4.4 / 5.0');
    expect(screen.getByTestId('budget-saving-chip')).toHaveTextContent(
      '₹200 below budget'
    );
    expect(
      screen.getByText(/Authentic spicy Andhra biryani/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Chicken Boneless Biryani/i)).toBeInTheDocument();
    expect(screen.getByText('✓ Online Delivery')).toBeInTheDocument();
  });

  it('renders ResultsPanel with AI summary and recommendation cards', () => {
    render(<ResultsPanel data={MOCK_RECOMMENDATION_RESPONSE} />);

    expect(screen.getByTestId('results-panel')).toBeInTheDocument();
    expect(
      screen.getByText(/Found 1 top biryani spot in Koramangala/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Meghana Foods')).toBeInTheDocument();
  });

  it('integrates App flow: idle -> loading -> displays backend recommendations', async () => {
    apiClientModule.fetchRecommendations.mockResolvedValue(
      MOCK_RECOMMENDATION_RESPONSE
    );

    render(<App />);

    expect(screen.getByTestId('welcome-banner')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/City \/ Locality/i), {
      target: { value: 'koramangala' },
    });
    fireEvent.change(screen.getByLabelText(/Budget for Two/i), {
      target: { value: 'under 800' },
    });
    fireEvent.click(screen.getByTestId('search-button'));

    await waitFor(() => {
      expect(screen.getByTestId('results-panel')).toBeInTheDocument();
    });

    expect(apiClientModule.fetchRecommendations).toHaveBeenCalledWith({
      city: 'koramangala',
      price: 'under 800',
      preferences: undefined,
    });
    expect(screen.getByText('Meghana Foods')).toBeInTheDocument();
  });

  it('displays error banner when backend API returns an error', async () => {
    apiClientModule.fetchRecommendations.mockRejectedValue({
      response: {
        data: { detail: "No restaurants found in 'Mars' within budget '100'." },
      },
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/City \/ Locality/i), {
      target: { value: 'Mars' },
    });
    fireEvent.change(screen.getByLabelText(/Budget for Two/i), {
      target: { value: '100' },
    });
    fireEvent.click(screen.getByTestId('search-button'));

    await waitFor(() => {
      expect(screen.getByTestId('error-banner')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/No restaurants found in 'Mars' within budget '100'/i)
    ).toBeInTheDocument();
  });
});

