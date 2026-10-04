import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser } from '../api/auth';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Eyebrow } from '../components/common/Eyebrow';

export const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await registerUser({ username, email, password });
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col lg:flex-row bg-ivory font-sans text-charcoal antialiased">
      {/* Left Panel: Editorial Showcase */}
      <div className="relative flex flex-col justify-between bg-charcoal text-ivory lg:w-2/5 p-8 sm:p-12 lg:p-16 overflow-hidden">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(201,164,108,0.15),transparent_70%)]"
        />
        <div className="relative z-10 flex items-center gap-2 mb-12">
          <img
            src="/logo.svg"
            alt="Legalyze Logo"
            className="h-8 w-auto object-contain"
            onError={(e) => {
              const target = e.currentTarget;
              if (!target.src.endsWith('/screen.png')) {
                target.src = '/screen.png';
              }
            }}
          />
          <span className="border-l border-border-hairline pl-2 font-mono text-[10px] font-medium uppercase tracking-[0.04em] text-sand/60">
            Intelligence
          </span>
        </div>

        <div className="relative z-10 flex-1 flex flex-col justify-center max-w-md">
          <Eyebrow light>Join Legalyze</Eyebrow>
          <h1 className="mb-8 font-display text-4xl leading-tight text-ivory">
            Built for people who read between the lines.
          </h1>
          
          <div className="space-y-4">
             <div className="flex items-center gap-3 rounded-full border border-sand/15 bg-surface/5 px-4 py-2 font-mono text-xs text-sand/80">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-olive opacity-75 motion-safe:animate-ping" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-olive" />
                </span>
                <span>Every clause connected</span>
             </div>
             <div className="flex items-center gap-3 rounded-full border border-sand/15 bg-surface/5 px-4 py-2 font-mono text-xs text-sand/80 w-max">
                 <span className="h-1.5 w-1.5 rounded-full bg-brass-soft" />
                 <span>Every risk cited</span>
             </div>
          </div>
        </div>
      </div>

      {/* Right Panel: Access Portal */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 sm:p-12 lg:p-16 bg-ivory">
        <div 
          className={`w-full max-w-sm transition-all duration-700 ease-out ${mounted ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}
        >
          <Eyebrow>Document intelligence</Eyebrow>
          <h2 className="mb-2 font-display text-3xl font-normal text-charcoal">
            Create your workspace.
          </h2>
          <p className="mb-8 text-sm text-stone-muted">
            Start reviewing contracts with clause-level precision.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-2xl border border-crimson/30 bg-crimson-soft p-3 text-center font-mono text-xs text-crimson">
                {error}
              </div>
            )}
            <Input
              label="Username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="johndoe"
            />
            <Input
              label="Email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
            />
            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
            <div className="pt-2">
              <Button type="submit" variant="charcoal" className="w-full" isLoading={isLoading}>
                Begin analysis
              </Button>
            </div>
            
            <div className="mt-4 flex justify-center">
               <span className="inline-flex items-center gap-1.5 rounded-full border border-sand bg-parchment/50 px-3 py-1 font-mono text-[10px] text-stone-muted">
                 🔒 No credit card required · Instant access
               </span>
            </div>

            <p className="text-center text-sm text-stone-muted pt-4">
              Already have access?{' '}
              <Link to="/login" className="font-medium text-brass-deep hover:text-brass transition-colors">
                Sign in
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};
