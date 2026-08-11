import React, { useState } from 'react';
import SearchBar from './SearchBar';
import ResultDisplay from './ResultDisplay';
import SourceList from './SourceList';
import LoadingState from './LoadingState';
import { API_BASE_URL } from '../apiConfig';

export default function QAView() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (query) => {
    setIsLoading(true);
    setResult(null);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch response from server');
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("An error occurred while fetching the legal analysis. Ensure the backend is running.");
    } finally {
      setIsLoading(false);
    }
  };

  const examples = [
    "What is the Additional Medicare Tax rate?",
    "What did the Court decide about reasonable accommodation?",
    "What is required for a reverse QTIP election?",
  ];

  return (
    <div className="w-full flex flex-col items-center">
      <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      
      {/* Example Chips */}
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2 max-w-3xl">
        <span className="text-xs font-medium text-zinc-500 mr-1">Try an example:</span>
        {examples.map((ex, idx) => (
          <button
            key={idx}
            onClick={() => handleSearch(ex)}
            disabled={isLoading}
            className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 border border-zinc-800 hover:border-zinc-700 rounded-md text-xs transition-colors"
          >
            {ex}
          </button>
        ))}
      </div>
      
      {error && (
        <div className="w-full max-w-3xl mx-auto mt-8 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-200 text-sm text-center">
          {error}
        </div>
      )}
      
      {isLoading && <LoadingState />}
      
      {!isLoading && result && (
        <>
          <ResultDisplay answer={result.answer} grounded={result.grounded} citations={result.citations} />
          <SourceList sources={result.sources} />
        </>
      )}
    </div>
  );
}
