"use client";

import { useState } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";

export default function PasswordRecoveryPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Placeholder: call backend when POST /api/auth/forgot-password exists
      await new Promise((r) => setTimeout(r, 800));
      setSent(true);
    } catch {
      setError("Request failed. Try again or contact support.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1218] flex flex-col items-center justify-center p-6">
      <Link href="/" className="mb-8" aria-label="Home">
        <Logo variant="headerLockup" active />
      </Link>
      <div className="w-full max-w-md rounded-xl border border-white/10 bg-white/5 p-8">
        <h1 className="text-2xl font-bold text-white mb-2">Password recovery</h1>
        <p className="text-white/70 text-sm mb-6">
          Enter your account email. If an account exists, you will receive instructions to reset your password.
        </p>
        {sent ? (
          <div className="rounded-lg border border-green-600/30 bg-green-600/10 text-green-400 px-4 py-3 text-sm mb-4">
            If an account exists for that email, we sent recovery instructions. Check your inbox and spam folder.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-red-600/30 bg-red-600/10 text-red-400 px-4 py-3 text-sm">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white/80 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-orange-500"
                placeholder="you@organization.com"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Sending…" : "Send recovery email"}
            </button>
          </form>
        )}
        <div className="mt-6 text-center">
          <Link href="/login" className="text-sm text-orange-400 hover:text-orange-300 transition-colors">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
