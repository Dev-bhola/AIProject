import React from 'react';

export default function LoadingState() {
  return (
    <div className="w-full max-w-3xl mx-auto mt-8 flex flex-col items-center justify-center animate-pulse">
      <div className="flex space-x-2">
        <div className="w-2.5 h-2.5 bg-zinc-400 rounded-full animate-bounce"></div>
        <div className="w-2.5 h-2.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
        <div className="w-2.5 h-2.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
      </div>
    </div>
  );
}
