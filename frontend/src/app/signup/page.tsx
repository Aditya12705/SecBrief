"use client";

import { useState } from "react";
import Link from "next/link";
import { SecBriefLogo } from "@/components/SecBriefLogo";
import { authSignup } from "@/lib/api";

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <button
      onClick={handleCopy}
      className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors"
    >
      {copied ? "Copied!" : label}
    </button>
  );
}

export default function Signup() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{
    email: string;
    api_key: string;
    plan: string;
    install_snippet: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    try {
      const data = await authSignup(email);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <main className="min-h-screen gradient-hero flex flex-col">
        <header className="border-b border-slate-800/80 glass sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-3">
                <SecBriefLogo size="md" showText />
              </Link>
            </div>
          </div>
        </header>

        <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 py-12 flex-1">
          <div className="glass rounded-2xl p-8">
            <div className="text-center mb-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-2xl shadow-lg shadow-emerald-500/20">
                🎉
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">You're all set!</h2>
              <p className="text-slate-400">Here's your API key and setup instructions.</p>
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-slate-300">Your API Key</label>
                  <CopyButton text={result.api_key} label="Copy" />
                </div>
                <pre className="bg-slate-900/50 rounded-xl p-4 text-sm font-mono text-emerald-400 overflow-x-auto">
                  {result.api_key}
                </pre>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-slate-300">GitHub Actions Workflow</label>
                  <CopyButton text={result.install_snippet} label="Copy" />
                </div>
                <pre className="bg-slate-900/50 rounded-xl p-4 text-sm font-mono text-slate-300 overflow-x-auto whitespace-pre">
                  {result.install_snippet}
                </pre>
              </div>

              <div className="bg-slate-800/50 rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-200">Setup Instructions</h3>
                <ol className="list-decimal list-inside space-y-3 text-sm text-slate-300">
                  <li>
                    Copy the workflow above into <code className="text-amber-400">.github/workflows/secbrief.yml</code>
                  </li>
                  <li>Go to your repo → Settings → Secrets and variables → Actions → New repository secret</li>
                  <li>Name it <code className="text-amber-400">SECBRIEF_API_KEY</code> and paste your API key</li>
                  <li>Open a Pull Request — SecBrief will scan it automatically!</li>
                </ol>
              </div>

              <div className="flex justify-center">
                <Link
                  href="/"
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-emerald-500 text-white font-semibold hover:opacity-90 transition-opacity"
                >
                  Back to SecBrief
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen gradient-hero flex flex-col">
      <header className="border-b border-slate-800/80 glass sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <SecBriefLogo size="md" showText />
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-xl mx-auto w-full px-4 sm:px-6 py-12 flex-1">
        <div className="glass rounded-2xl p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Get your API key</h2>
            <p className="text-slate-400">Start scanning your Pull Requests automatically.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500"
                required
              />
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-red-900/30 border border-red-800 text-red-200 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-emerald-500 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Generating..." : "Get API Key"}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
