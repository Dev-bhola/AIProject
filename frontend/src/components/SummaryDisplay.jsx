import React from 'react';
import CitationBadge from './CitationBadge';

const TRUNCATION_MESSAGES = {
  representative_sample: 'This is a representative sampled summary. Selected sections from across the document were processed due to API/token constraints.',
  budget_limit: 'Only a portion of the document could be processed within the current API rate limits.',
  batch_failure: 'Some sections of the document failed to process and were excluded from this summary.',
  consolidation_limit: 'Some extracted facts were dropped while condensing the document to fit summarization limits.',
};

function getTruncationMessage(reasons) {
  if (!reasons || reasons.length === 0) {
    return 'This is a representative sampled summary of a large document. Selected sections from across the document were processed due to API/token constraints.';
  }
  return reasons.map(r => TRUNCATION_MESSAGES[r] || r).join(' ');
}

export default function SummaryDisplay({ result, documentName }) {
  if (!result) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mt-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="bg-[#0a0a0a] border border-zinc-800 rounded-lg p-6 shadow-sm">
        <header className="mb-6 border-b border-zinc-800 pb-4">
          <h3 className="text-xs font-bold text-zinc-400 tracking-wider uppercase flex items-center gap-1.5 mb-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Document Summary
          </h3>
          <h2 className="text-lg font-bold text-zinc-100">{documentName || result.doc_id}</h2>
          {result.truncated && (
             <div className="mt-2 inline-flex items-center px-2 py-1 bg-yellow-950/50 text-yellow-500 text-[10px] font-medium rounded border border-yellow-900/50">
               <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
               </svg>
               {getTruncationMessage(result.truncation_reasons)}
             </div>
          )}
        </header>
        
        <div className="space-y-8">
          <section>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">Overall Summary</h4>
            <p className="text-zinc-200 leading-relaxed text-sm whitespace-pre-wrap">
              {result.overall_summary.text}
            </p>
            {result.overall_summary.citations && result.overall_summary.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.overall_summary.citations.map((cit, idx) => (
                  <CitationBadge key={idx} sourceFile={cit.source_file} pageNumbers={cit.page_numbers} />
                ))}
              </div>
            )}
          </section>
          
          {result.summary_points && result.summary_points.length > 0 && (
            <section>
              <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-4">Key Points</h4>
              <ul className="space-y-3">
                {result.summary_points.map((pt, idx) => (
                  <li key={idx} className="bg-zinc-900/50 p-4 rounded-md border border-zinc-800">
                    <p className="text-zinc-200 leading-relaxed text-sm mb-2">
                      <strong className="text-zinc-500 font-medium mr-2">{idx + 1}.</strong> 
                      {pt.point}
                    </p>
                    <div className="flex">
                      <CitationBadge sourceFile={pt.source_file} pageNumber={pt.page_number} />
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
