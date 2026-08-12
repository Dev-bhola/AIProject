import React from 'react';
import architectureDiagram from '../assets/architecture-diagram.png';

const AboutView = () => {
  const metrics = [
    { value: '4,277', label: 'Chunks Indexed' },
    { value: '40', label: 'Documents (4 categories)' },
    { value: 'Groq', label: 'LLM Engine' },
    { value: 'Hybrid (BM25 + Vector)', label: 'Retrieval Engine' },
  ];

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
          System Architecture
        </h3>

        <img
          src={architectureDiagram}
          alt="Legal RAG architecture: document ingestion, question and answer, and summarization pipelines"
          className="w-full h-auto rounded-lg border border-zinc-800"
        />
      </div>
    </div>
  );
};

export default AboutView;
