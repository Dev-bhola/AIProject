import React, { useState, useMemo, useRef, useEffect } from 'react';

const CATEGORY_LABELS = {
  act: 'Act',
  judgment: 'Judgment',
  pov: 'POV',
  tax_doc: 'Tax Doc',
};

const LOWERCASE_WORDS = new Set(['al', 'ex', 'of', 'and', 'the']);
const KNOWN_ACRONYMS = new Set(['aarp', 'irs', 'cfr', 'uscode', 'eitc']);

function titleCaseWords(text) {
  return text
    .split(' ')
    .map((word, i) => {
      const lower = word.toLowerCase();
      if (KNOWN_ACRONYMS.has(lower)) return lower.toUpperCase();
      if (i > 0 && LOWERCASE_WORDS.has(lower)) return lower;
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}

function cleanDisplayName(sourceFile) {
  const noExt = sourceFile.replace(/\.pdf$/i, '');
  const looksLikeId = /^[0-9]{4}-[0-9]{2}-[0-9]{2}_[A-Za-z0-9]+_[a-f0-9]{20,}$/i.test(noExt);
  if (looksLikeId) {
    const reportMatch = noExt.match(/_([A-Za-z]?\d+)_/);
    const dateMatch = noExt.match(/^(\d{4}-\d{2}-\d{2})/);
    const report = reportMatch ? reportMatch[1] : noExt.slice(0, 12);
    const date = dateMatch ? dateMatch[1] : '';
    return `Report ${report}${date ? ` (${date})` : ''}`;
  }

  const isCaseName = /_v_/i.test(noExt);
  const withoutSpacedLetters = noExt.replace(/^[a-z](?:_[a-z])+(?=_)/i, (m) => m.replace(/_/g, ''));
  const spaced = withoutSpacedLetters.replace(/[_-]/g, ' ').replace(/\s+/g, ' ').trim();

  if (isCaseName) {
    return titleCaseWords(spaced)
      .replace(/\bEt Al\b/gi, 'et al.')
      .replace(/\bEx Rel\b/gi, 'ex rel.')
      .replace(/\s+V\s+/gi, ' v. ');
  }

  return titleCaseWords(spaced);
}

export default function DocumentPicker({ documents, selectedDocId, onSelect, isLoading, disabled }) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const enriched = useMemo(
    () => documents.map((doc) => ({ ...doc, displayName: cleanDisplayName(doc.source_file) })),
    [documents]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return enriched;
    return enriched.filter(
      (doc) =>
        doc.displayName.toLowerCase().includes(q) ||
        doc.source_file.toLowerCase().includes(q) ||
        (CATEGORY_LABELS[doc.category] || doc.category || '').toLowerCase().includes(q)
    );
  }, [enriched, query]);

  const grouped = useMemo(() => {
    const groups = {};
    for (const doc of filtered) {
      const key = doc.category || 'other';
      if (!groups[key]) groups[key] = [];
      groups[key].push(doc);
    }
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [filtered]);

  const selectedDoc = enriched.find((d) => d.doc_id === selectedDocId);

  const handleSelect = (docId) => {
    onSelect(docId);
    setIsOpen(false);
    setQuery('');
  };

  return (
    <div className="w-full relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => !disabled && !isLoading && setIsOpen((o) => !o)}
        disabled={disabled || isLoading}
        className="w-full flex items-center justify-between pl-4 pr-3 py-3 bg-[#0a0a0a] border border-zinc-800 rounded-lg text-left text-zinc-100 focus:outline-none focus:border-zinc-600 transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
      >
        <span className={selectedDoc ? 'text-zinc-100' : 'text-zinc-500'}>
          {isLoading
            ? 'Loading documents...'
            : selectedDoc
            ? selectedDoc.displayName
            : 'Select a legal document'}
        </span>
        <span className="flex items-center gap-2 flex-shrink-0 ml-2">
          {selectedDoc && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
              {CATEGORY_LABELS[selectedDoc.category] || selectedDoc.category}
            </span>
          )}
          <svg className={`w-5 h-5 text-zinc-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-20 mt-1 w-full bg-[#0a0a0a] border border-zinc-700 rounded-lg shadow-xl overflow-hidden">
          <div className="p-2 border-b border-zinc-800">
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name or category..."
              className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-md text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
            />
          </div>

          <div className="max-h-72 overflow-y-auto">
            {grouped.length === 0 && (
              <div className="px-4 py-6 text-sm text-zinc-500 text-center">No documents match your search.</div>
            )}
            {grouped.map(([category, docs]) => (
              <div key={category}>
                <div className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-500 sticky top-0 bg-[#0a0a0a]">
                  {CATEGORY_LABELS[category] || category} · {docs.length}
                </div>
                {docs.map((doc) => (
                  <button
                    key={doc.doc_id}
                    type="button"
                    onClick={() => handleSelect(doc.doc_id)}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-zinc-800 transition-colors ${
                      doc.doc_id === selectedDocId ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-300'
                    }`}
                  >
                    {doc.displayName}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
