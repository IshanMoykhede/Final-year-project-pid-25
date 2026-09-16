import React from 'react';
import { Link } from 'react-router-dom';
import { Scale } from 'lucide-react';

export const Footer: React.FC = () => (
  <footer className="border-t border-gray-200 bg-gray-950 text-gray-300">
    <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
      <div>
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-white">
          <Scale className="h-5 w-5 text-sky-400" />
          Legal<span className="text-sky-400">ze</span>
        </Link>
        <p className="mt-3 max-w-sm text-sm leading-6 text-gray-400">
          A focused workspace for understanding contracts, finding important clauses, and asking better questions.
        </p>
      </div>
      <div>
        <p className="text-sm font-semibold text-white">Explore</p>
        <div className="mt-4 flex flex-col gap-3 text-sm">
          <a href="/#services" className="transition hover:text-white">Services</a>
          <a href="/#about" className="transition hover:text-white">About us</a>
          <Link to="/login" className="transition hover:text-white">Sign in</Link>
        </div>
      </div>
      <div>
        <p className="text-sm font-semibold text-white">Workspace</p>
        <p className="mt-4 text-sm leading-6 text-gray-400">Upload PDF and DOCX documents to start a structured review.</p>
      </div>
    </div>
    <div className="border-t border-white/10">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-5 text-xs text-gray-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <span>© {new Date().getFullYear()} Legalze</span>
        <span>Built for clearer document decisions.</span>
      </div>
    </div>
  </footer>
);