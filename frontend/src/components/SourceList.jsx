import React from 'react';

export default function SourceList({ sources }) {
  if (!sources || sources.length === 0) return null;
  
  // Create a deduplicated list of unique source chunks to display
  // Using marker as the unique key, though sources should already be deduplicated by marker
  const uniqueSources = Array.from(new Map(sources.map(s => [s.marker, s])).values());
  
  return (
    <div className="w-full max-w-3xl mx-auto mt-6 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-150">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Sources Cited</h4>
      <div className="grid gap-3 sm:grid-cols-2">
        {uniqueSources.map((source) => (
          <div 
            key={source.marker} 
            className="group flex flex-col p-4 bg-slate-800/40 rounded-xl border border-slate-700/60 hover:bg-slate-800/80 hover:border-blue-500/50 transition-all duration-300"
          >
            <div className="flex items-start gap-3 mb-2">
              <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold ring-1 ring-blue-500/30 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                {source.marker}
              </span>
              <div className="flex-1 min-w-0">
                <h5 className="text-sm font-semibold text-slate-200 truncate" title={source.source_file}>
                  {source.source_file}
                </h5>
                <p className="text-xs text-slate-400 truncate mt-0.5">
                  Page {source.page || "?"} • {source.section !== "Unknown Section" ? source.section : "Tax Document"}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
