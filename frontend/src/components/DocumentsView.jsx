import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../apiConfig';

const DocumentsView = () => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/documents`);
      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      console.error(err);
      setError('Could not load documents. Please check the backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // Extract unique categories
  const categories = ['All', ...new Set(documents.map(doc => doc.category || 'Unknown'))];

  // Filter documents based on selected category
  const filteredDocuments = selectedCategory === 'All' 
    ? documents 
    : documents.filter(doc => doc.category === selectedCategory);

  const handleViewPdf = (docId) => {
    // Open the PDF in a new tab using the backend endpoint
    window.open(`${API_BASE_URL}/api/documents/${docId}/pdf`, '_blank');
  };

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-8 animate-in fade-in duration-500">
      
      {/* Filters Section */}
      <div className="bg-slate-800/60 backdrop-blur-md rounded-2xl border border-slate-700/50 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Document Library</h2>
          <p className="text-sm text-slate-400 mt-1">
            Browse and view all source materials indexed in the RAG system.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-300">Filter by POV:</span>
          <div className="flex flex-wrap gap-2">
            {categories.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-900/20'
                    : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-600/50'
                }`}
              >
                {category === 'Unknown' ? 'General' : category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content Section */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <svg className="animate-spin h-8 w-8 text-blue-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p>Loading documents...</p>
        </div>
      ) : error ? (
        <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-6 text-center text-red-200">
          <p>{error}</p>
          <button 
            onClick={fetchDocuments}
            className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg transition-colors text-sm font-semibold"
          >
            Try Again
          </button>
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="bg-slate-800/40 rounded-xl border border-slate-700/50 p-12 text-center text-slate-400">
          <p className="text-lg">No documents found for this category.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map(doc => (
            <div 
              key={doc.doc_id} 
              className="group bg-slate-800/40 hover:bg-slate-800/80 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6 flex flex-col justify-between transition-all duration-300 hover:shadow-lg hover:shadow-blue-900/10 hover:border-slate-600"
            >
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center border border-red-500/20">
                    <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-slate-200 break-all line-clamp-2" title={doc.source_file}>
                    {doc.source_file}
                  </h3>
                </div>
                
                <div className="mb-6">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-700 text-slate-300 border border-slate-600">
                    ID: {doc.doc_id}
                  </span>
                </div>
              </div>

              <button
                onClick={() => handleViewPdf(doc.doc_id)}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors text-sm shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                View PDF
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentsView;
