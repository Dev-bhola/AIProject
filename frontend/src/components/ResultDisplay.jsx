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
            className="inline-flex items-center justify-center w-4 h-4 ml-0.5 mr-0.5 text-[9px] font-bold text-zinc-900 bg-zinc-300 rounded-full cursor-pointer hover:bg-zinc-100 transition-colors align-super"
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
    <div className="w-full max-w-3xl mx-auto mt-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="bg-[#0a0a0a] border border-zinc-800 rounded-lg p-5 shadow-sm">
        
        <div className="flex justify-between items-center mb-4 border-b border-zinc-800 pb-3">
          <h3 className="text-xs font-bold text-zinc-400 tracking-wider uppercase flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            AI Response
          </h3>
          
          {grounded !== undefined && (
            <div className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 border ${grounded ? 'bg-zinc-900 text-zinc-300 border-zinc-700' : 'bg-red-950 text-red-400 border-red-900'}`}>
              {grounded ? (
                <>
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Grounded
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  Unsupported Claims
                </>
              )}
            </div>
          )}
        </div>
        
        <p className="text-zinc-200 leading-relaxed text-sm whitespace-pre-wrap">
           {renderFormattedAnswer(answer)}
        </p>
      </div>
    </div>
  );
}
