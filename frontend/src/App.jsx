import React, { useState } from 'react';
import QAView from './components/QAView';
import SummaryView from './components/SummaryView';

function App() {
  const [mode, setMode] = useState('qa'); // 'qa' or 'summarize'

  return (
    <div className="min-h-screen bg-slate-900 text-slate-50 font-sans selection:bg-blue-500/30 flex flex-col">
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5 pointer-events-none"></div>
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-blue-900/20 to-transparent pointer-events-none"></div>
      
      <main className="relative z-10 container mx-auto px-4 pt-24 pb-12 flex-1 flex flex-col">
        <header className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300 mb-4">
            Legal Intelligence RAG
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            High-precision query engine tailored for the US Tax & Legal domain.
          </p>
        </header>

        <div className="w-full flex justify-center mb-10">
          <div className="inline-flex bg-slate-800/80 rounded-xl p-1.5 border border-slate-700/50 shadow-lg backdrop-blur-md">
            <button
              onClick={() => setMode('qa')}
              className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
                mode === 'qa' 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
              }`}
            >
              Ask a Question
            </button>
            <button
              onClick={() => setMode('summarize')}
              className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
                mode === 'summarize' 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
              }`}
            >
              Summarize Document
            </button>
          </div>
        </div>
        
        <div className="flex-1 w-full">
          {mode === 'qa' ? <QAView /> : <SummaryView />}
        </div>
        
      </main>
      
     
    </div>
  );
}

export default App;
