import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { FileText, Shield, Zap, ChevronRight, MessageSquare, ScanSearch } from 'lucide-react';

export const Landing: React.FC = () => {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-slate-950 px-4 py-24 text-center text-white sm:py-32">
        <div className="mx-auto max-w-4xl">
        <p className="mb-5 text-sm font-semibold uppercase tracking-[0.22em] text-sky-300">Contract intelligence, made practical</p>
        <h1 className="mb-6 text-5xl font-extrabold tracking-tight sm:text-6xl">
          AI-Powered <span className="text-accent">Legal Document</span> Analysis
        </h1>
        <p className="mx-auto mb-10 max-w-2xl text-xl leading-8 text-slate-300">
          Upload your contracts and legal documents to get structured document insights powered by advanced AI.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link to="/register">
            <Button size="lg" className="w-full sm:w-auto">
              Get Started <ChevronRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="outline" size="lg" className="w-full sm:w-auto">
              Sign In
            </Button>
          </Link>
        </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="services" className="bg-gray-50 px-4 py-20 scroll-mt-20">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 max-w-2xl"><p className="mb-3 text-sm font-semibold uppercase tracking-widest text-accent">What we provide</p><h2 className="text-3xl font-bold text-gray-950 sm:text-4xl">A clearer way to work through legal documents.</h2></div>
          <div className="grid gap-5 md:grid-cols-3">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
              <div className="bg-accent/10 p-4 rounded-full mb-4 text-accent">
                <FileText className="h-8 w-8" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">01. Upload</h3>
              <p className="text-gray-600">Securely upload your PDF or DOCX legal documents to our platform.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
              <div className="bg-accent/10 p-4 rounded-full mb-4 text-accent">
                <Zap className="h-8 w-8" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">02. Understand</h3>
              <p className="text-gray-600">Our AI instantly parses and analyzes the document structure and content.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
              <div className="bg-accent/10 p-4 rounded-full mb-4 text-accent">
                <Shield className="h-8 w-8" />
              </div>
              <h3 className="mb-2 text-xl font-semibold">03. Review</h3>
              <p className="text-gray-600">Review the generated markdown and extracted insights with ease.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="about" className="scroll-mt-20 bg-white px-4 py-20">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
          <div><p className="mb-3 text-sm font-semibold uppercase tracking-widest text-accent">About Legalze</p><h2 className="text-3xl font-bold text-gray-950 sm:text-4xl">Built to make the first read less intimidating.</h2></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="border-l-2 border-sky-400 pl-5"><MessageSquare className="mb-3 h-6 w-6 text-accent" /><h3 className="font-semibold text-gray-900">Ask in plain language</h3><p className="mt-2 text-sm leading-6 text-gray-600">Use document chat to explore specific clauses without losing the surrounding context.</p></div>
            <div className="border-l-2 border-amber-400 pl-5"><ScanSearch className="mb-3 h-6 w-6 text-amber-500" /><h3 className="font-semibold text-gray-900">Review with focus</h3><p className="mt-2 text-sm leading-6 text-gray-600">See document structure, clause priorities, and risk signals in one organized workspace.</p></div>
          </div>
        </div>
      </section>
    </div>
  );
};
