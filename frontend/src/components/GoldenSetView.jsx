import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../apiConfig';
import LoadingState from './LoadingState';
import ResultDisplay from './ResultDisplay';
import SourceList from './SourceList';

export default function GoldenSetView() {
  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  
  // State for the currently running/expanded question
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState(null);

  useEffect(() => {
    const fetchGoldenSet = async () => {
      try {
        const response = await fetch('/api/golden-set');
        if (!response.ok) {
          const text = await response.text();
          throw new Error(`HTTP ${response.status}: ${text}`);
        }
        const data = await response.json();
        setQuestions(data);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Failed to load golden set questions.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchGoldenSet();
  }, []);

  const handleDownloadCSV = () => {
    const headers = ['sample_query', 'ground_truth_answer', 'source_document', 'category', 'page_reference'];
    const rows = questions.map(q => {
      return headers.map(header => {
        const val = (q[header] || '').toString().replace(/"/g, '""');
        return `"${val}"`;
      }).join(',');
    });
    
    const csvContent = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'golden_set.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const categories = ['All', ...new Set(questions.map(q => q.category).filter(Boolean))];
  const filteredQuestions = selectedCategory === 'All' 
    ? questions 
    : questions.filter(q => q.category === selectedCategory);

  const handleRunQuery = async (queryText, index) => {
    if (activeQuestion === index) {
      // Toggle off if already active
      setActiveQuestion(null);
      return;
    }
    
    setActiveQuestion(index);
    setQueryLoading(true);
    setQueryResult(null);
    setQueryError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: queryText }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch response from server');
      }
      
      const data = await response.json();
      setQueryResult(data);
    } catch (err) {
      console.error(err);
      setQueryError("An error occurred while fetching the legal analysis.");
    } finally {
      setQueryLoading(false);
    }
  };

  if (isLoading) return <LoadingState />;

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto mt-8 p-4 bg-red-950/50 border border-red-900/50 rounded-lg text-red-200 text-sm text-center">
        {error}
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <p className="text-zinc-400 text-sm">
          Every question belongs to the hand-authored ground truth Golden Set. Run any one to confirm it live against the system.
        </p>
        <button 
          onClick={handleDownloadCSV}
          className="flex-shrink-0 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold uppercase rounded transition-colors"
        >
          Download CSV
        </button>
      </div>

      {questions.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs font-bold uppercase rounded-full transition-colors ${
                selectedCategory === cat
                  ? 'bg-zinc-100 text-zinc-900'
                  : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      )}
      
      <div className="flex flex-col gap-4">
        {filteredQuestions.map((q, idx) => (
          <div key={idx} className="bg-[#0a0a0a] border border-zinc-800 rounded-lg overflow-hidden shadow-sm">
            <div className="p-5">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-500 text-xs font-mono">#{idx + 1}</span>
                    {q.category && (
                      <span className="px-2 py-0.5 bg-zinc-900 text-zinc-400 border border-zinc-800 text-[10px] font-bold uppercase rounded">
                        {q.category.replace('_', ' ')}
                      </span>
                    )}
                    {q.page_reference && (
                      <span className="px-2 py-0.5 bg-zinc-900 text-zinc-500 border border-zinc-800 text-[10px] font-bold uppercase rounded">
                        Page {q.page_reference}
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-medium text-zinc-100 mt-1">
                    {q.sample_query}
                  </h3>
                  
                  <div className="mt-2 bg-zinc-900/50 border border-zinc-800 rounded p-3 text-xs flex gap-2">
                    <span className="font-bold text-zinc-500 uppercase flex-shrink-0">Ground Truth:</span>
                    <span className="text-zinc-300">{q.ground_truth_answer}</span>
                  </div>
                </div>
                
                <button 
                  onClick={() => handleRunQuery(q.sample_query, idx)}
                  className={`flex-shrink-0 px-4 py-2 text-xs font-bold uppercase rounded transition-colors ${
                    activeQuestion === idx 
                      ? 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700' 
                      : 'bg-zinc-100 text-zinc-900 hover:bg-white'
                  }`}
                >
                  {activeQuestion === idx ? 'Close' : 'Run'}
                </button>
              </div>
            </div>
            
            {/* Inline Query Result */}
            {activeQuestion === idx && (
              <div className="border-t border-zinc-800 bg-zinc-950 p-5">
                {queryLoading && <LoadingState />}
                
                {queryError && (
                  <div className="p-3 bg-red-950/30 border border-red-900/30 rounded text-red-300 text-xs text-center">
                    {queryError}
                  </div>
                )}
                
                {queryResult && (
                  <div className="-mt-4">
                    <ResultDisplay answer={queryResult.answer} grounded={queryResult.grounded} citations={queryResult.citations} />
                    <SourceList sources={queryResult.sources} />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
