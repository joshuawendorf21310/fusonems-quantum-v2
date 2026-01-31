"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";
import { useRouter, useSearchParams } from "next/navigation";

function TwoFactorContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const returnTo = searchParams.get("returnTo") || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Placeholder: when backend supports 2FA verification, POST code and redirect
      await new Promise((r) => setTimeout(r, 600));
      router.push(returnTo);
    } catch {
      setError("Invalid or expired code. Try again.");
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
        <h1 className="text-2xl font-bold text-white mb-2">Two-factor authentication</h1>
        <p className="text-white/70 text-sm mb-6">
          Enter the 6-digit code from your authenticator app.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg border border-red-600/30 bg-red-600/10 text-red-400 px-4 py-3 text-sm">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="code" className="block text-sm font-medium text-white/80 mb-1">
              Verification code
            </label>
            <input
              id="code"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-center text-xl tracking-widest focus:outline-none focus:border-orange-500"
              placeholder="000000"
            />
          </div>
          <button
            type="submit"
            disabled={loading || code.length < 6}
            className="w-full py-2.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-medium transition-colors disabled:opacity-50"
          >
            {loading ? "Verifying…" : "Verify"}
          </button>
        </form>
        <div className="mt-6 text-center">
          <Link href="/login" className="text-sm text-orange-400 hover:text-orange-300 transition-colors">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function TwoFactorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0d1218] flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-md rounded-xl border border-white/10 bg-white/5 p-8 text-white/70 text-center">Loading…</div>
      </div>
    }>
      <TwoFactorContent />
    </Suspense>
  );
}
