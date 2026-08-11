import React from 'react';

export default function CitationBadge({ sourceFile, pageNumber, pageNumbers }) {
  if (!sourceFile) return null;
  
  let pageDisplay = null;
  if (pageNumbers && Array.isArray(pageNumbers) && pageNumbers.length > 0) {
    pageDisplay = `Pages ${pageNumbers.join(', ')}`;
  } else if (pageNumber !== undefined && pageNumber !== null && pageNumber !== 0 && pageNumber !== "?") {
    pageDisplay = `Page ${pageNumber}`;
  }
  
  return (
    <span className="inline-flex items-center mt-2 mr-2 px-2 py-1 rounded text-[10px] font-medium bg-[#0a0a0a] text-zinc-300 border border-zinc-800 hover:bg-zinc-900 transition-colors cursor-default select-none shadow-sm">
      <svg className="w-3 h-3 mr-1.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      {sourceFile}
      {pageDisplay && (
        <span className="ml-1.5 pl-1.5 border-l border-zinc-700 text-zinc-500">
          {pageDisplay}
        </span>
      )}
    </span>
  );
}
