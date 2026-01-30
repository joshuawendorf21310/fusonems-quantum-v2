'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, Clock, TrendingUp } from 'lucide-react';

interface SearchResult {
  module: string;
  id: string;
  title: string;
  subtitle: string;
  url: string;
}

interface GroupedResults {
  [module: string]: SearchResult[];
}

const moduleColors: { [key: string]: string } = {
  ePCR: 'bg-blue-500',
  CAD: 'bg-red-500',
  Fleet: 'bg-green-500',
  Patients: 'bg-purple-500',
  Bills: 'bg-yellow-500',
  Personnel: 'bg-indigo-500',
  Scheduling: 'bg-pink-500',
  Reports: 'bg-orange-500',
};

const filters = ['All', 'Patients', 'Bills', 'Units', 'Personnel', 'ePCR'];

const popularSearches = [
  'Active CAD Incidents',
  'Pending ePCRs',
  'Overdue Bills',
  'Expiring Certifications',
  'Available Units',
];

export default function GlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout>();

  // Load recent searches from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recentSearches');
    if (stored) {
      setRecentSearches(JSON.parse(stored));
    }
  }, []);

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K (Mac) or Ctrl+K (Windows)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      
      // ESC to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setQuery('');
        setResults([]);
        setSelectedIndex(0);
      }

      // Arrow navigation
      if (isOpen && results.length > 0) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex((prev) => Math.max(prev - 1, 0));
        }
        if (e.key === 'Enter') {
          e.preventDefault();
          handleSelectResult(results[selectedIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, results, selectedIndex]);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Debounced search
  const performSearch = useCallback(async (searchQuery: string, filter: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        q: searchQuery,
        ...(filter !== 'All' && { module: filter }),
      });

      const response = await fetch(`/api/search/global?${params}`);
      
      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setResults(data.slice(0, 50)); // Max 50 results
      setSelectedIndex(0);
    } catch (err) {
      setError('Failed to perform search');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (query) {
      debounceTimer.current = setTimeout(() => {
        performSearch(query, selectedFilter);
      }, 300);
    } else {
      setResults([]);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, selectedFilter, performSearch]);

  const handleSelectResult = (result: SearchResult) => {
    // Save to recent searches
    const updated = [query, ...recentSearches.filter((s) => s !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));

    // Navigate to result
    window.location.href = result.url;
    setIsOpen(false);
    setQuery('');
    setResults([]);
  };

  const handleRecentSearch = (search: string) => {
    setQuery(search);
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recentSearches');
  };

  const groupResultsByModule = (results: SearchResult[]): GroupedResults => {
    return results.reduce((acc, result) => {
      if (!acc[result.module]) {
        acc[result.module] = [];
      }
      acc[result.module].push(result);
      return acc;
    }, {} as GroupedResults);
  };

  const groupedResults = groupResultsByModule(results);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/50 backdrop-blur-sm"
      onClick={() => setIsOpen(false)}
    >
      <div
        className="w-full max-w-2xl bg-gray-900 rounded-lg shadow-2xl border border-gray-700 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Header */}
        <div className="border-b border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5 text-gray-400 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across all modules..."
              className="flex-1 bg-transparent text-white text-lg outline-none placeholder-gray-500"
            />
            {query && (
              <button
                onClick={() => {
                  setQuery('');
                  setResults([]);
                }}
                className="p-1 hover:bg-gray-800 rounded"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            )}
          </div>

          {/* Filters */}
          <div className="flex gap-2 mt-3 flex-wrap">
            {filters.map((filter) => (
              <button
                key={filter}
                onClick={() => setSelectedFilter(filter)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  selectedFilter === filter
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        {/* Results / Empty State */}
        <div className="max-h-[60vh] overflow-y-auto">
          {isLoading && (
            <div className="p-8 text-center text-gray-400">
              Searching...
            </div>
          )}

          {error && (
            <div className="p-8 text-center text-red-400">
              {error}
            </div>
          )}

          {!isLoading && !error && query && results.length === 0 && (
            <div className="p-8 text-center text-gray-400">
              No results found
            </div>
          )}

          {!query && !isLoading && (
            <div className="p-4 space-y-6">
              {/* Recent Searches */}
              {recentSearches.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-gray-400">Recent Searches</h3>
                    <button
                      onClick={clearRecentSearches}
                      className="text-xs text-gray-500 hover:text-gray-300"
                    >
                      Clear all
                    </button>
                  </div>
                  <div className="space-y-1">
                    {recentSearches.map((search, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleRecentSearch(search)}
                        className="w-full flex items-center gap-3 p-2 rounded hover:bg-gray-800 text-left transition-colors"
                      >
                        <Clock className="w-4 h-4 text-gray-500 flex-shrink-0" />
                        <span className="text-gray-300">{search}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Popular Searches */}
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-3">Popular Searches</h3>
                <div className="space-y-1">
                  {popularSearches.map((search, idx) => (
                    <button
                      key={idx}
                      onClick={() => setQuery(search)}
                      className="w-full flex items-center gap-3 p-2 rounded hover:bg-gray-800 text-left transition-colors"
                    >
                      <TrendingUp className="w-4 h-4 text-gray-500 flex-shrink-0" />
                      <span className="text-gray-300">{search}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Search Results */}
          {!isLoading && results.length > 0 && (
            <div className="p-2">
              {Object.entries(groupedResults).map(([module, moduleResults]) => (
                <div key={module} className="mb-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2">
                    {module}
                  </h3>
                  <div className="space-y-1">
                    {moduleResults.map((result, idx) => {
                      const globalIndex = results.indexOf(result);
                      return (
                        <button
                          key={result.id}
                          onClick={() => handleSelectResult(result)}
                          className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors ${
                            selectedIndex === globalIndex
                              ? 'bg-blue-600'
                              : 'hover:bg-gray-800'
                          }`}
                        >
                          <span
                            className={`${
                              moduleColors[result.module] || 'bg-gray-600'
                            } text-white text-xs font-medium px-2 py-1 rounded flex-shrink-0`}
                          >
                            {result.module}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="text-white font-medium truncate">
                              {result.title}
                            </div>
                            <div className="text-sm text-gray-400 truncate">
                              {result.subtitle}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer with keyboard shortcuts */}
        <div className="border-t border-gray-700 px-4 py-3 flex items-center justify-between bg-gray-800/50">
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <kbd className="px-2 py-1 bg-gray-700 rounded text-gray-300">↑↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-2 py-1 bg-gray-700 rounded text-gray-300">↵</kbd>
              Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-2 py-1 bg-gray-700 rounded text-gray-300">ESC</kbd>
              Close
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
