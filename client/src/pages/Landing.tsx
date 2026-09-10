import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { FileText, Shield, Zap, ChevronRight } from 'lucide-react';

export const Landing: React.FC = () => {
  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 py-20">
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-primary max-w-4xl mb-6">
          AI-Powered <span className="text-accent">Legal Document</span> Analysis
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mb-10">
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
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">How it works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
              <div className="bg-accent/10 p-4 rounded-full mb-4 text-accent">
                <FileText className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-2">1. Upload</h3>
              <p className="text-gray-600">Securely upload your PDF or DOCX legal documents to our platform.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
              <div className="bg-accent/10 p-4 rounded-full mb-4 text-accent">
                <Zap className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-2">2. Analyze</h3>
              <p className="text-gray-600">Our AI instantly parses and analyzes the document structure and content.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
              <div className="bg-accent/10 p-4 rounded-full mb-4 text-accent">
                <Shield className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold mb-2">3. Review</h3>
              <p className="text-gray-600">Review the generated markdown and extracted insights with ease.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
