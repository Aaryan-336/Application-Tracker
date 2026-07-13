"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export default function Register() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("SYSTEM_WARNING: Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("SYSTEM_WARNING: Password length must be >= 6 characters.");
      return;
    }

    setLoading(true);

    try {
      await api.register(email, password);
      setSuccess(true);
      
      setTimeout(async () => {
        try {
          const authData = await api.login(email, password);
          localStorage.setItem("career_agent_token", authData.access_token);
          router.push("/profile?onboarding=true");
        } catch {
          router.push("/login");
        }
      }, 1200);

    } catch (err: any) {
      setError(err.message || "SYSTEM_ERROR: Failed to allocate session index. Email may be taken.");
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12 font-mono text-xs text-gray-400">
      <div className="w-full max-w-sm console-panel p-6 rounded space-y-6">
        {success ? (
          <div className="text-center py-6 space-y-3">
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded bg-success/10 border border-success/20">
              <CheckCircle2 className="h-6 w-6 text-success animate-pulse" />
            </div>
            <h2 className="text-sm font-bold text-white tracking-widest">// REGISTRATION_GRANTED</h2>
            <p className="text-[10px] text-gray-500">Auto routing to onboarding profiles...</p>
          </div>
        ) : (
          <>
            <div className="space-y-1 pb-4 border-b border-border">
              <h2 className="text-sm font-bold text-white tracking-widest">// ALLOCATE_SESSION</h2>
              <p className="text-[10px] text-gray-500">Create private secure database node</p>
            </div>

            {error && (
              <div className="flex items-start gap-2.5 border border-danger/20 bg-danger/5 p-4 rounded text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0 text-danger" />
                <p>{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  EMAIL_ADDRESS
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  DEFINE_PASSWORD
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  VERIFY_PASSWORD
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center h-11 rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all font-semibold uppercase tracking-wider"
              >
                {loading ? "COMMITTING_DATA..." : "> EXECUTE_REGISTER"}
              </button>
            </form>

            <p className="mt-8 text-center text-[10px] text-gray-500">
              Already have a session?{" "}
              <Link href="/login" className="font-semibold text-accent hover:underline">
                Sign_In
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
