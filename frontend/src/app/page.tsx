"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      let isMounted = true;
      const timeoutId = setTimeout(() => {
        if (isMounted) {
          console.warn("Auth check routing fallback triggered.");
          setCheckingAuth(false);
        }
      }, 3000);

      try {
        const token = localStorage.getItem("career_agent_token");
        if (token) {
          router.push("/dashboard");
        } else {
          setCheckingAuth(false);
          clearTimeout(timeoutId);
        }
      } catch (e) {
        console.error("Storage access failed:", e);
        setCheckingAuth(false);
        clearTimeout(timeoutId);
      }

      return () => {
        isMounted = false;
        clearTimeout(timeoutId);
      };
    }
  }, [router]);

  if (checkingAuth) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#050505] text-[#e2e8f0]">
        <div className="flex flex-col items-center gap-3 data-mono text-xs text-gray-500 uppercase tracking-widest">
          <Loader2 className="h-5 w-5 animate-spin text-accent" />
          BOOTING_SYSTEM...
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col justify-between px-6 py-12 md:py-24 font-mono text-xs text-gray-400 select-none">
      {/* Hero Header */}
      <main className="mx-auto flex max-w-sm flex-1 flex-col items-center justify-center text-center space-y-8">
        <div className="space-y-2">
          <div className="inline-block px-4 py-2 border border-accent bg-accent/5 rounded text-accent font-bold tracking-widest text-sm">
            AGENT // CONSOLE
          </div>
          <p className="text-[10px] text-gray-600 uppercase tracking-widest pt-1">Private AI Recruiter Session</p>
        </div>

        <p className="text-[11px] text-gray-400 leading-relaxed max-w-xs mx-auto">
          Automated CV parameter parsing, match telemetry scores, and pipeline management interfaces.
        </p>

        {/* Feature nodes */}
        <div className="w-full text-left bg-[#09090b] border border-border p-4.5 rounded space-y-3.5">
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block border-b border-border pb-1.5">// SYSTEM_INDEX</span>
          <div className="space-y-2 text-[11px]">
            <div>+ [01] CV_PARSER // AUTO_EXTRACT</div>
            <div>+ [02] SCRAPER // LIVE_PLAYWRIGHT</div>
            <div>+ [03] COMPATIBILITY // AI_SCORE</div>
            <div>+ [04] PIPELINE // STATE_PROGRESS</div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex w-full flex-col gap-2.5">
          <Link
            href="/login"
            className="flex h-11 items-center justify-center rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all font-semibold uppercase tracking-wider"
          >
            &gt; SIGN_IN
          </Link>
          <Link
            href="/register"
            className="flex h-11 items-center justify-center rounded border border-border bg-[#09090b] text-gray-400 hover:text-white transition-all font-semibold uppercase tracking-wider"
          >
            &gt; CREATE_ACCOUNT
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 text-center text-[10px] text-gray-600 tracking-wider">
        CORE // POWERED_BY_GROQ
      </footer>
    </div>
  );
}
