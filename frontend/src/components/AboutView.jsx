import React from 'react';

const AboutView = () => {
  const metrics = [
    { value: '3,049', label: 'Chunks Indexed' },
    { value: 'Groq', label: 'LLM Engine' },
    { value: 'Hugging Face', label: 'Embeddings' },
    { value: 'Hybrid', label: 'Retrieval Engine' },
  ];

  const ArrowRight = () => (
    <svg className="w-5 h-5 text-zinc-600 mx-2 hidden md:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
    </svg>
  );

  const ArrowDown = () => (
    <svg className="w-5 h-5 text-zinc-600 my-2 block md:hidden mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 17l-4 4m0 0l-4-4m4 4V3" />
    </svg>
  );

  return (
    <div className="w-full flex flex-col gap-10 animate-in fade-in duration-300 pb-12">
      
      {/* Header Section */}
      <div>
        <h2 className="text-2xl font-semibold text-zinc-100 mb-2">
          About the System
        </h2>
        <p className="text-zinc-400 text-sm">
          A high-precision, AI-powered Retrieval-Augmented Generation (RAG) system tailored for US Tax & Legal research.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, i) => (
          <div key={i} className="bg-[#0a0a0a] rounded-lg border border-zinc-800 p-5">
            <div className="text-2xl font-bold text-zinc-100 mb-1">{metric.value}</div>
            <div className="text-xs font-medium text-zinc-500 uppercase tracking-wide">{metric.label}</div>
          </div>
        ))}
      </div>

      {/* Architecture Section */}
      <div className="bg-[#0a0a0a] rounded-xl border border-zinc-800 p-6 md:p-8">
        <h3 className="text-lg font-semibold text-zinc-100 mb-6 border-b border-zinc-800 pb-4">
          System Flowchart
        </h3>
        
        {/* Pipeline 1: Ingestion */}
        <div className="mb-10">
          <h4 className="text-sm font-medium text-zinc-300 mb-4">1. Document Ingestion Pipeline</h4>
          
          <div className="flex flex-col md:flex-row items-center justify-between bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
            {/* Step 1 */}
            <div className="flex-1 w-full bg-[#0a0a0a] p-3 rounded-md border border-zinc-700/50 text-center">
              <div className="font-semibold text-zinc-200 text-sm mb-1">Raw PDFs</div>
              <div className="text-[10px] text-zinc-500">Legal Acts, Tax Docs</div>
            </div>
            
            <ArrowRight /><ArrowDown />
            
            {/* Step 2 */}
            <div className="flex-1 w-full bg-[#0a0a0a] p-3 rounded-md border border-zinc-700/50 text-center">
              <div className="font-semibold text-zinc-200 text-sm mb-1">Parser & Chunker</div>
              <div className="text-[10px] text-zinc-500">900-char blocks</div>
            </div>
            
            <ArrowRight /><ArrowDown />
            
            {/* Step 3 (Split) */}
            <div className="flex-[1.5] w-full flex flex-col gap-2">
              <div className="bg-[#0a0a0a] p-2 rounded-md border border-zinc-700/50 text-center">
                <div className="font-semibold text-zinc-200 text-xs mb-0.5">Vector Indexing</div>
                <div className="text-[10px] text-zinc-500">Hugging Face → Qdrant</div>
              </div>
              <div className="bg-[#0a0a0a] p-2 rounded-md border border-zinc-700/50 text-center">
                <div className="font-semibold text-zinc-200 text-xs mb-0.5">Keyword Indexing</div>
                <div className="text-[10px] text-zinc-500">BM25 → Local Pickle</div>
              </div>
            </div>
          </div>
        </div>

        {/* Pipeline 2: Generation */}
        <div>
          <h4 className="text-sm font-medium text-zinc-300 mb-4">2. Real-Time Query Pipeline</h4>
          
          <div className="flex flex-col md:flex-row items-center justify-between bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
            {/* Step 1 */}
            <div className="flex-1 w-full bg-[#0a0a0a] p-3 rounded-md border border-zinc-700/50 text-center">
              <div className="font-semibold text-zinc-200 text-sm mb-1">User Query</div>
            </div>
            
            <ArrowRight /><ArrowDown />
            
            {/* Step 2 */}
            <div className="flex-[1.5] w-full bg-[#0a0a0a] p-3 rounded-md border border-zinc-700/50 text-center">
              <div className="font-semibold text-zinc-200 text-sm mb-2">Hybrid Retrieval</div>
              <div className="flex justify-center gap-1.5 text-[10px]">
                <span className="px-1.5 py-0.5 bg-zinc-800 text-zinc-300 rounded border border-zinc-700">Vector</span>
                <span className="px-1.5 py-0.5 bg-zinc-800 text-zinc-300 rounded border border-zinc-700">Keyword</span>
              </div>
            </div>
            
            <ArrowRight /><ArrowDown />
            
            {/* Step 3 */}
            <div className="flex-1 w-full bg-[#0a0a0a] p-3 rounded-md border border-zinc-700/50 text-center">
              <div className="font-semibold text-zinc-200 text-sm mb-1">Groq LLM</div>
            </div>

            <ArrowRight /><ArrowDown />
            
            {/* Step 4 */}
            <div className="flex-1 w-full bg-zinc-100 p-3 rounded-md border border-zinc-300 text-center">
              <div className="font-bold text-zinc-900 text-sm mb-1">Answer</div>
              <div className="text-[10px] text-zinc-600">With exact citations</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default AboutView;
