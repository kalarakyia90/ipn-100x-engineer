'use client';

import { useState } from 'react';
import SearchForm from '@/components/SearchForm';
import RestaurantCard from '@/components/RestaurantCard';
import { Restaurant } from '@/types/restaurant';

export default function Home() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (location: string) => {
    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await fetch(`/api/restaurants?address=${encodeURIComponent(location)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch restaurants');
      }

      setRestaurants(data.restaurants);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setRestaurants([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">🍽️ Restaurant Finder</h1>
          <p className="mt-1 text-sm text-gray-500">
            Find the best restaurants near you
          </p>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Search Section */}
        <section className="mb-8">
          <SearchForm onSearch={handleSearch} isLoading={loading} />
        </section>

        {/* Results Section */}
        <section>
          {loading && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
              <span className="ml-3 text-gray-600">Finding restaurants...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {!loading && hasSearched && restaurants.length === 0 && !error && (
            <div className="text-center py-12">
              <p className="text-gray-500">No restaurants found. Try a different location.</p>
            </div>
          )}

          {!loading && restaurants.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Found {restaurants.length} restaurants near you
              </h2>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {restaurants.map((restaurant) => (
                  <RestaurantCard key={restaurant.id} restaurant={restaurant} />
                ))}
              </div>
            </div>
          )}

          {!hasSearched && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-gray-500 text-lg">
                Enter your location to find nearby restaurants
              </p>
              <p className="mt-3 text-sm text-gray-500">
  💡 Tip: Try searching for &quot;San Francisco&quot;, &quot;Downtown&quot;, or a zip code like &quot;94102&quot;
            </p>
            </div>
          )}
        </section>
      </div>

      {/* Footer */}
      <footer className="bg-gray-50 border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            Restaurant Finder - AI Workshop Demo Application
          </p>
        </div>
      </footer>
    </main>
  );
}