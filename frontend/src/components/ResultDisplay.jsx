import React from 'react';

export default function ResultDisplay({ answer, grounded, citations }) {
  if (!answer) return null;
  
  // Function to replace [N] with styled citation badges
  const renderFormattedAnswer = (text) => {
    if (!text) return null;
    
    // Split by [N] regex
    const parts = text.split(/(\[\d+\])/g);
    
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const markerNum = match[1];
        return (
          <span 
            key={index} 
            className="inline-flex items-center justify-center w-5 h-5 ml-1 mr-1 text-[10px] font-bold text-blue-100 bg-blue-600 rounded-full shadow-sm shadow-blue-900/50 cursor-pointer hover:bg-blue-500 transition-colors align-super"
            title={`Source ${markerNum}`}
          >
            {markerNum}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-slate-800/60 backdrop-blur-md border border-slate-700/50 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400"></div>
        
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-blue-400 tracking-wider uppercase flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            AI Response
          </h3>
          
          {grounded !== undefined && (
            <div className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-sm ${grounded ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
              {grounded ? (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Grounded
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  Unsupported Claims
                </>
              )}
            </div>
          )}
        </div>
        
        <p className="text-slate-200 leading-relaxed text-lg whitespace-pre-wrap">
          {renderFormattedAnswer(answer)}
        </p>
      </div>
    </div>
  );
}
