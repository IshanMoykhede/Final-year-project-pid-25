import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser } from '../api/auth';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Eyebrow } from '../components/common/Eyebrow';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await loginUser({ email, password });
      login();
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
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
          <Eyebrow light>Secure document workspace</Eyebrow>
          <h1 className="mb-8 font-display text-4xl leading-tight text-ivory">
            Your agreements, finally readable.
          </h1>
          
          <div className="space-y-4">
             <div className="flex items-center gap-3 rounded-full border border-sand/15 bg-surface/5 px-4 py-2 font-mono text-xs text-sand/80">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-olive opacity-75 motion-safe:animate-ping" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-olive" />
                </span>
                <span>Deterministically indexed</span>
             </div>
             <div className="flex items-center gap-3 rounded-full border border-sand/15 bg-surface/5 px-4 py-2 font-mono text-xs text-sand/80 w-max">
                 <span className="h-1.5 w-1.5 rounded-full bg-brass-soft" />
                 <span>0% training exposure</span>
             </div>
          </div>
        </div>

        <div className="relative z-10 mt-12 flex items-center gap-4 text-xs font-medium text-sand/50">
          <span>AES-256</span>
          <span>·</span>
          <span>Tenant-isolated</span>
        </div>
      </div>

      {/* Right Panel: Access Portal */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 sm:p-12 lg:p-16 bg-ivory">
        <div 
          className={`w-full max-w-sm transition-all duration-700 ease-out ${mounted ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}
        >
          <Eyebrow>Document intelligence</Eyebrow>
          <h2 className="mb-2 font-display text-3xl font-normal text-charcoal">
            Welcome back.
          </h2>
          <p className="mb-8 text-sm text-stone-muted">
            Sign in to access your review workspace.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-2xl border border-crimson/30 bg-crimson-soft p-3 text-center font-mono text-xs text-crimson">
                {error}
              </div>
            )}
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
            <Button type="submit" variant="charcoal" className="w-full mt-2" isLoading={isLoading}>
              Sign in
            </Button>
            
            <p className="text-center text-sm text-stone-muted pt-4">
              No account?{' '}
              <Link to="/register" className="font-medium text-brass-deep hover:text-brass transition-colors">
                Get started free
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};
