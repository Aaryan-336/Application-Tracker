"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { AlertCircle } from "lucide-react";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.login(email, password);
      try {
        localStorage.setItem("career_agent_token", data.access_token);
      } catch (e) {
        console.error("Storage access failed:", e);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Access Denied.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12 font-mono text-xs text-gray-400">
      <div className="w-full max-w-sm console-panel p-6 rounded space-y-6">
        <div className="space-y-1 pb-4 border-b border-border">
          <h2 className="text-sm font-bold text-white tracking-widest">// USER_SIGN_IN</h2>
          <p className="text-[10px] text-gray-500">Provide session access parameters</p>
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
              SESSION_PASSWORD
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

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center h-11 rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all font-semibold uppercase tracking-wider"
          >
            {loading ? "AUTHENTICATING..." : "> EXECUTE_LOGIN"}
          </button>
        </form>

        <p className="mt-8 text-center text-[10px] text-gray-500">
          No session configured?{" "}
          <Link href="/register" className="font-semibold text-accent hover:underline">
            Register_Space
          </Link>
        </p>
      </div>
    </div>
  );
}
