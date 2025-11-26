import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Brain, Loader2 } from 'lucide-react';

export const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register.mutateAsync({ email, password, display_name: displayName });
      navigate('/dashboard');
    } catch (error) {
      console.error('Registration failed', error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand-500/10 mb-4">
            <Brain className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
          <p className="text-slate-400">Start simulating global idea spread</p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all"
                placeholder="Agent Zero"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all"
                placeholder="name@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all"
                placeholder="At least 8 characters"
                minLength={8}
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                Must contain 1 uppercase, 1 lowercase, and 1 number.
              </p>
            </div>

            {register.isError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                Registration failed. Email may already be in use.
              </div>
            )}

            <button
              type="submit"
              disabled={register.isPending}
              className="w-full bg-brand-600 hover:bg-brand-500 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {register.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

