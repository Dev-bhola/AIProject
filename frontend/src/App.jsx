import React, { useState } from 'react';
import QAView from './components/QAView';
import SummaryView from './components/SummaryView';
import DocumentsView from './components/DocumentsView';
import AboutView from './components/AboutView';
import GoldenSetView from './components/GoldenSetView';

function App() {
  const [mode, setMode] = useState('qa'); // 'qa', 'summarize', 'documents', 'golden_set', 'about'

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-zinc-100 font-sans selection:bg-zinc-700">
      
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#0a0a0a] border-r border-zinc-800 flex flex-col hidden md:flex">
        <div className="p-6">
          <h1 className="text-xl font-bold tracking-tight text-zinc-100 mb-1">
            US Tax & Legal
          </h1>
          <p className="text-xs text-zinc-500 font-medium">Research Assistant</p>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1">
          <button
            onClick={() => setMode('qa')}
            className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
              mode === 'qa' 
                ? 'bg-zinc-800 text-zinc-100 font-medium' 
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Ask a Question
          </button>
          
          <button
            onClick={() => setMode('summarize')}
            className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
              mode === 'summarize' 
                ? 'bg-zinc-800 text-zinc-100 font-medium' 
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Summarize Document
          </button>
          
          <button
            onClick={() => setMode('documents')}
            className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
              mode === 'documents' 
                ? 'bg-zinc-800 text-zinc-100 font-medium' 
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Browse Documents
          </button>

          <button
            onClick={() => setMode('golden_set')}
            className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
              mode === 'golden_set' 
                ? 'bg-zinc-800 text-zinc-100 font-medium' 
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Golden Set
          </button>
        </nav>

        <div className="p-4 border-t border-zinc-800">
          <button
            onClick={() => setMode('about')}
            className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
              mode === 'about' 
                ? 'bg-zinc-800 text-zinc-100 font-medium' 
                : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
            }`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            About System
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto bg-[#0a0a0a]">
        
        {/* Mobile Header (Hidden on Desktop) */}
        <header className="md:hidden flex items-center justify-between p-4 border-b border-zinc-800 bg-[#0a0a0a]">
          <h1 className="text-lg font-bold text-zinc-100">US Tax & Legal</h1>
          <select 
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm rounded-md px-2 py-1 outline-none"
          >
            <option value="qa">Ask a Question</option>
            <option value="summarize">Summarize</option>
            <option value="documents">Documents</option>
            <option value="golden_set">Golden Set</option>
            <option value="about">About</option>
          </select>
        </header>

        <div className="flex-1 w-full max-w-5xl mx-auto p-4 md:p-10 lg:p-12">
          {mode === 'qa' && <QAView />}
          {mode === 'summarize' && <SummaryView />}
          {mode === 'documents' && <DocumentsView />}
          {mode === 'golden_set' && <GoldenSetView />}
          {mode === 'about' && <AboutView />}
        </div>
      </main>
      
    </div>
  );
}

export default App;
