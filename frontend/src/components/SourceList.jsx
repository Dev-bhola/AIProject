import React from 'react';

export default function SourceList({ sources }) {
  if (!sources || sources.length === 0) return null;
  
  // Create a deduplicated list of unique source chunks to display
  // Using marker as the unique key, though sources should already be deduplicated by marker
  const uniqueSources = Array.from(new Map(sources.map(s => [s.marker, s])).values());
  
  return (
    <div className="w-full max-w-3xl mx-auto mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="bg-[#0a0a0a] border border-zinc-800 rounded-lg p-5 shadow-sm">
        <h3 className="text-xs font-bold text-zinc-400 tracking-wider uppercase mb-3 flex items-center gap-1.5 border-b border-zinc-800 pb-3">Sources Cited</h3>
        <div className="flex flex-col gap-2">
          {uniqueSources.map((source, index) => (
            <div 
              key={index} 
              className="bg-zinc-900/50 rounded-md p-3 border border-zinc-800 flex items-start gap-3 transition-colors hover:border-zinc-600"
            >
              <div className="flex-shrink-0 mt-0.5">
                <span className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-zinc-900 bg-zinc-300 rounded-full">
                  {source.marker}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-xs font-medium text-zinc-200 truncate" title={source.source_file}>
                    {source.source_file}
                  </h4>
                  <span className="px-1.5 py-0.5 text-[9px] font-medium bg-zinc-800 text-zinc-400 rounded border border-zinc-700">
                    Page {source.page || "?"}
                  </span>
                </div>
                {source.section && source.section !== "Unknown Section" && (
                  <p className="text-[10px] text-zinc-500 mb-1">
                    Section: {source.section}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
