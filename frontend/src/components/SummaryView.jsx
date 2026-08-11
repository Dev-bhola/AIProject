import React, { useState, useEffect } from 'react';
import LoadingState from './LoadingState';
import SummaryDisplay from './SummaryDisplay';
import { API_BASE_URL } from '../apiConfig';
import { pdfjs, Document, Page } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

export default function SummaryView() {
  const [documents, setDocuments] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [docsError, setDocsError] = useState(null);

  const [selectedDocId, setSelectedDocId] = useState('');
  const [numPages, setNumPages] = useState(null);
  
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [summaryResult, setSummaryResult] = useState(null);
  const [summaryError, setSummaryError] = useState(null);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  // Fetch available documents on mount
  useEffect(() => {
    const fetchDocuments = async () => {
      setIsLoadingDocs(true);
      setDocsError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/api/documents`);
        if (!res.ok) throw new Error('Failed to fetch documents');
        const data = await res.json();
        setDocuments(data);
      } catch (err) {
        console.error(err);
        setDocsError('Unable to load available documents.');
      } finally {
        setIsLoadingDocs(false);
      }
    };
    
    fetchDocuments();
  }, []);

  const handleSummarize = async () => {
    if (!selectedDocId) {
      setSummaryError('Please select a document to summarize.');
      return;
    }
    
    setIsSummarizing(true);
    setSummaryResult(null);
    setSummaryError(null);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/summarize/${encodeURIComponent(selectedDocId)}`);
      if (!res.ok) throw new Error('Failed to fetch summary from server');
      const data = await res.json();
      setSummaryResult(data);
    } catch (err) {
      console.error(err);
      setSummaryError('Unable to generate the summary. Please try again.');
    } finally {
      setIsSummarizing(false);
    }
  };

  const selectedDocument = documents.find(d => d.doc_id === selectedDocId);

  return (
    <div className="w-full flex flex-col items-center">
      <div className="w-full max-w-4xl mx-auto flex flex-col gap-6 items-center bg-slate-800/50 border border-slate-700/50 p-6 rounded-2xl shadow-lg backdrop-blur-sm">
        
        {/* Document Selector */}
        <div className="w-full relative">
          <select
            value={selectedDocId}
            onChange={(e) => {
              setSelectedDocId(e.target.value);
              setSummaryResult(null); // Clear summary when doc changes
              setSummaryError(null);
            }}
            disabled={isSummarizing || isLoadingDocs}
            className="block w-full pl-4 pr-10 py-3 bg-slate-900/80 border border-slate-600/50 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
          >
            <option value="" disabled>
              {isLoadingDocs ? 'Loading documents...' : 'Select a legal document'}
            </option>
            {documents.map(doc => (
              <option key={doc.doc_id} value={doc.doc_id}>
                {doc.source_file}
              </option>
            ))}
          </select>
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
        </div>

        {/* PDF Preview Area */}
        {selectedDocId ? (
          <div className="w-full flex flex-col border border-slate-600/50 rounded-xl overflow-hidden bg-slate-900/50">
            <div className="flex items-center justify-between px-4 py-3 bg-slate-800/80 border-b border-slate-700/50">
              <span className="text-sm text-slate-300 font-medium">Document: {selectedDocument?.source_file}</span>
              <a 
                href={`${API_BASE_URL}/api/documents/${encodeURIComponent(selectedDocId)}/pdf`}
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center transition-colors font-medium"
              >
                Open PDF in New Tab
                <svg className="w-3.5 h-3.5 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
            <div className="w-full h-[600px] overflow-y-auto bg-slate-900 flex flex-col items-center py-4">
              <Document
                file={`${API_BASE_URL}/api/documents/${encodeURIComponent(selectedDocId)}/pdf`}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={
                  <div className="flex flex-col items-center justify-center h-full text-slate-400 py-20">
                    <LoadingState />
                    <span className="mt-4">Loading PDF document...</span>
                  </div>
                }
                error={
                  <div className="flex flex-col items-center justify-center h-full text-red-400 py-20">
                    Unable to load PDF document.
                  </div>
                }
              >
                {Array.from(new Array(numPages || 0), (el, index) => (
                  <div key={`page_${index + 1}`} className="mb-6 shadow-xl border border-slate-700/50 bg-white">
                    <Page 
                      pageNumber={index + 1} 
                      renderTextLayer={false} 
                      renderAnnotationLayer={false}
                      className="max-w-full"
                    />
                    <div className="text-center py-2 text-xs text-slate-500 bg-slate-100 border-t border-slate-200">
                      Page {index + 1} of {numPages}
                    </div>
                  </div>
                ))}
              </Document>
            </div>
          </div>
        ) : (
          <div className="w-full py-16 flex flex-col items-center justify-center border-2 border-dashed border-slate-700/70 rounded-xl bg-slate-900/30 text-slate-400">
            <svg className="w-12 h-12 mb-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm font-medium">Select a document to preview it</p>
          </div>
        )}
        
        {/* Summarize Button */}
        <button
          onClick={handleSummarize}
          disabled={!selectedDocId || isSummarizing || isLoadingDocs}
          className="w-full py-3.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium text-lg rounded-xl transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer shadow-md"
        >
          {isSummarizing ? 'Analyzing Document...' : 'Summarize Document'}
        </button>
      </div>

      {docsError && (
        <div className="w-full max-w-4xl mx-auto mt-4 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-200 text-sm text-center">
          {docsError}
        </div>
      )}

      {summaryError && (
        <div className="w-full max-w-4xl mx-auto mt-4 p-4 bg-red-900/30 border border-red-500/30 rounded-xl text-red-200 text-sm text-center">
          {summaryError}
        </div>
      )}

      {isSummarizing && (
        <div className="mt-12">
          <LoadingState />
          <p className="text-center text-slate-400 mt-4 animate-pulse">Analyzing legal document...</p>
        </div>
      )}
      
      {!isSummarizing && summaryResult && (
        <SummaryDisplay 
          result={summaryResult} 
          documentName={selectedDocument ? selectedDocument.source_file : null} 
        />
      )}
    </div>
  );
}
