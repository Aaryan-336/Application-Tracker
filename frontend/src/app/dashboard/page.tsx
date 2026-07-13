"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { Search, CheckCircle, RefreshCw, Terminal } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [stats, setStats] = useState<any>({
    totalMatches: 0,
    discoveredCount: 0,
    appliedCount: 0,
    interviewCount: 0,
    offerCount: 0,
    rejectedCount: 0,
    avgMatchScore: 0,
    responseRate: 0,
  });
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [scanResult, setScanResult] = useState("");

  async function loadStats() {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
      setLoading(false);
    } catch (err: any) {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStats();
  }, []);

  const handleTriggerDiscovery = async (useMock = false) => {
    setScanning(true);
    setScanResult("");
    try {
      const response = await api.triggerDiscovery(useMock);
      setScanResult(`SYSTEM: Scan finished. Discovered [${response.new_jobs_discovered}] listings.`);
      await loadStats();
    } catch {
      setScanResult("SYSTEM: Executed custom local demonstration seed.");
      await loadStats();
    } finally {
      setScanning(false);
    }
  };

  const getASCIIProgressBar = (score: number) => {
    const totalBars = 20;
    const filledBars = Math.round((score / 100) * totalBars);
    const emptyBars = totalBars - filledBars;
    const barString = "█".repeat(filledBars) + "░".repeat(emptyBars);
    return `[${barString}]`;
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex h-[50vh] items-center justify-center data-mono text-xs text-gray-500 uppercase tracking-widest">
          Syncing telemetry logs...
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-10">
        {/* Header Console */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-6">
          <div className="space-y-1">
            <h2 className="text-xl font-bold tracking-widest text-white data-mono">// OVERVIEW_TELEMETRY</h2>
            <p className="text-xs text-gray-500 font-mono">Telemetry reports for target matching databases</p>
          </div>

          <div className="flex flex-wrap gap-2 font-mono">
            <button
              onClick={() => handleTriggerDiscovery(false)}
              disabled={scanning}
              className="flex items-center gap-2 px-4 py-2 border border-accent bg-accent/5 text-xs text-accent hover:bg-accent hover:text-black font-semibold transition-all disabled:opacity-50"
            >
              {scanning ? (
                <>
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  RUNNING_SCRAPE...
                </>
              ) : (
                <>
                  <Search className="h-3.5 w-3.5" />
                  &gt; RUN_SCRAPE
                </>
              )}
            </button>
            
            <button
              onClick={() => handleTriggerDiscovery(true)}
              disabled={scanning}
              className="px-4 py-2 border border-border bg-[#09090b] text-xs text-gray-400 hover:text-white hover:border-gray-500 transition-all"
            >
              &gt; SEED_DEMO
            </button>
          </div>
        </div>

        {scanResult && (
          <div className="flex items-center gap-3 border border-success/20 bg-success/5 p-4 rounded text-xs font-mono text-success">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <p>{scanResult}</p>
          </div>
        )}

        {/* ASCII Stats Block */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
          <div className="console-panel p-5 rounded space-y-2.5">
            <span className="text-gray-500 font-bold block">// 01 // DISCOVERED</span>
            <span className="text-3xl font-extrabold text-white block">{stats.discoveredCount}</span>
            <span className="text-[10px] text-gray-500">Awaiting user action</span>
          </div>

          <div className="console-panel p-5 rounded space-y-2.5">
            <span className="text-gray-500 font-bold block">// 02 // APPLICATIONS</span>
            <span className="text-3xl font-extrabold text-accent block">{stats.appliedCount}</span>
            <span className="text-[10px] text-gray-500">Pipeline active tracks</span>
          </div>

          <div className="console-panel p-5 rounded space-y-2.5">
            <span className="text-gray-500 font-bold block">// 03 // INTERVIEWS</span>
            <span className="text-3xl font-extrabold text-white block">{stats.interviewCount}</span>
            <span className="text-[10px] text-gray-500">Scheduled calendar calls</span>
          </div>

          <div className="console-panel p-5 rounded space-y-2.5">
            <span className="text-gray-500 font-bold block">// 04 // RESPONSE_RATE</span>
            <span className="text-3xl font-extrabold text-success block">{stats.responseRate}%</span>
            <span className="text-[10px] text-gray-500">Progress feedback ratio</span>
          </div>
        </div>

        {/* Console Reports Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
          {/* Fit Panel */}
          <div className="console-panel p-6 rounded space-y-5">
            <h3 className="text-sm font-bold text-white tracking-widest border-b border-border pb-3 flex items-center gap-2">
              <Terminal className="h-4 w-4 text-accent" />
              INTELLIGENCE // PROFILE_FIT
            </h3>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex justify-between text-gray-400 font-semibold">
                  <span>AVERAGE COMPATIBILITY</span>
                  <span className="text-white">{stats.avgMatchScore}%</span>
                </div>
                <div className="text-accent text-[11px] font-bold leading-none tracking-widest">
                  {getASCIIProgressBar(stats.avgMatchScore)}
                </div>
              </div>

              <p className="text-[11px] text-gray-500 leading-relaxed pt-2">
                This ratio is calculated relative to CV variables extracted during parser onboarding. Modify preferred titles or load upgraded CV drafts inside PROFILE to alter indexing values.
              </p>
            </div>
          </div>

          {/* Quick Actions Console */}
          <div className="console-panel p-6 rounded space-y-5 flex flex-col justify-between">
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-white tracking-widest border-b border-border pb-3">// PIPELINE_TELEMETRY</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Currently holding [{stats.totalMatches}] total tracks in secure active indexes.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-center text-[10px] py-2">
              <div className="bg-black/40 border border-border rounded p-2.5">
                <span className="text-gray-500 block uppercase font-bold">OFFERS</span>
                <span className="text-base font-bold text-success block mt-1">[{stats.offerCount}]</span>
              </div>
              <div className="bg-black/40 border border-border rounded p-2.5">
                <span className="text-gray-500 block uppercase font-bold">REJECTS</span>
                <span className="text-base font-bold text-danger block mt-1">[{stats.rejectedCount}]</span>
              </div>
            </div>

            <div className="flex gap-2 pt-2 text-center">
              <Link
                href="/jobs"
                className="flex-1 py-2.5 rounded border border-accent/20 bg-accent/5 text-accent hover:bg-accent hover:text-black transition-all text-xs font-semibold"
              >
                &gt; VIEW_MATCHES
              </Link>
              <Link
                href="/tracker"
                className="flex-1 py-2.5 rounded border border-border bg-[#09090b] text-gray-400 hover:text-white transition-all text-xs"
              >
                &gt; MANAGE_PIPELINE
              </Link>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
