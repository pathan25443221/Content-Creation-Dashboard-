import React from 'react';
import GeneratorForm from './GeneratorForm';

export default function GenerateTab({ generatorProps }) {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Generate Shorts</h1>
        <p className="page-subtitle">Paste a YouTube URL or file path to produce vertical 9:16 short-form clips.</p>
      </header>

      <GeneratorForm {...generatorProps} />
    </div>
  );
}
