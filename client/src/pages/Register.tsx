import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser } from '../api/auth';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/common/Card';
import { Scale } from 'lucide-react';

export const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <div className="bg-primary/5 p-3 rounded-full mb-4">
            <Scale className="h-8 w-8 text-accent" />
          </div>
          <CardTitle className="text-2xl">Create an account</CardTitle>
          <CardDescription>Get started with Legalze</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-500 p-3 rounded-md text-sm text-center">
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
            <Button type="submit" className="w-full" isLoading={isLoading}>
              Sign up
            </Button>
            <p className="text-center text-sm text-gray-500 mt-4">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-accent hover:text-accent/80">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
