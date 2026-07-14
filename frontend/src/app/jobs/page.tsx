"use client";

import { useEffect, useState, useRef } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { MapPin, ExternalLink, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Search, Sliders, Globe, Terminal, Play } from "lucide-react";

export default function Jobs() {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<any>(null);
  const [actionMsg, setActionMsg] = useState("");
  
  // Scraper control states
  const [showConfig, setShowConfig] = useState(false);
  const [query, setQuery] = useState("Software Engineer");
  const [location, setLocation] = useState("Remote");
  const [limit, setLimit] = useState(10);
  const [useMock, setUseMock] = useState(false);
  const [sources, setSources] = useState({
    remotive: true,
    themuse: true,
    jsearch: false,
    adzuna: false
  });
  
  // Scraping status states
  const [scraping, setScraping] = useState(false);
  const [scrapeLogs, setScrapeLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  async function loadMatches() {
    try {
      const data = await api.getMatches("discovered");
      setMatches(data);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMatches();
  }, []);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [scrapeLogs]);

  const addLog = (text: string) => {
    const time = new Date().toLocaleTimeString();
    setScrapeLogs((prev) => [...prev, `[${time}] ${text}`]);
  };

  const handleUpdateStatus = async (userJobId: string, status: string) => {
    try {
      await api.updateStatus(userJobId, status);
      setActionMsg(`SYSTEM: Match index shifted to status [${status.toUpperCase()}].`);
      setSelectedJob(null);
      await loadMatches();
      setTimeout(() => setActionMsg(""), 3000);
    } catch {
      // Handle error
    }
  };

  const handleRunScraper = async (e: React.FormEvent) => {
    e.preventDefault();
    setScraping(true);
    setScrapeLogs([]);
    
    // Build comma separated sources
    const activeSources = Object.entries(sources)
      .filter(([_, active]) => active)
      .map(([name]) => name)
      .join(",");
      
    addLog(`Initiating job discovery cycle for: "${query}" in "${location}"...`);
    await new Promise((r) => setTimeout(r, 600));
    
    if (useMock) {
      addLog("Mock parameter active. Injecting sandbox jobs...");
    } else {
      addLog(`Selected API sources: [${activeSources.toUpperCase()}]`);
      addLog("Querying job APIs for matching listings...");
      await new Promise((r) => setTimeout(r, 800));
      addLog("Fetching real listings with direct apply URLs...")
    }

    try {
      const response = await api.triggerDiscovery(query, location, limit, activeSources, useMock);
      addLog(`API fetch finished. Synced database matching structures.`);
      addLog(`Status: ${response.message}. Discovered ${response.new_jobs_discovered} new jobs.`);
      addLog("Starting AI matching algorithms with stored resumes...");
      await new Promise((r) => setTimeout(r, 700));
      addLog("Match scoring completed successfully.");
      
      setActionMsg(`SYSTEM: Discovery cycle completed. Found ${response.new_jobs_discovered} new postings.`);
      await loadMatches();
      setTimeout(() => setActionMsg(""), 4000);
    } catch (err: any) {
      addLog(`ERROR: Discovery engine failure: ${err.message}`);
    } finally {
      setScraping(false);
    }
  };

  const toggleSource = (source: string) => {
    setSources((prev: any) => ({
      ...prev,
      [source]: !prev[source]
    }));
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) {
      return (
        <span className="text-xs font-mono font-bold text-success">
          [FIT // {score}%]
        </span>
      );
    }
    if (score >= 60) {
      return (
        <span className="text-xs font-mono font-bold text-accent">
          [FIT // {score}%]
        </span>
      );
    }
    return (
      <span className="text-xs font-mono font-bold text-gray-500">
        [FIT // {score}%]
      </span>
    );
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex h-[50vh] items-center justify-center font-mono text-xs text-gray-500 uppercase tracking-widest">
          Parsing index feed...
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-6">
          <div>
            <h2 className="text-xl font-bold tracking-widest text-white font-mono">// DISCOVERED_FEED</h2>
            <p className="text-xs text-gray-500 font-mono mt-1 font-semibold">Direct listing feed matched against parsed resume structures</p>
          </div>
          
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-2 px-4 py-2 bg-[#09090b] border border-border hover:border-accent/40 font-mono text-xs font-semibold text-accent rounded transition-all self-start sm:self-center"
          >
            <Sliders className="h-4 w-4" />
            {showConfig ? "HIDE_DISCOVERY_DASHBOARD" : "SHOW_DISCOVERY_DASHBOARD"}
          </button>
        </div>

        {/* Discovery Configurations Box */}
        {showConfig && (
          <div className="console-panel p-6 rounded space-y-6 animate-fadeIn">
            <h3 className="text-xs font-bold text-white font-mono uppercase tracking-widest flex items-center gap-2">
              <Search className="h-4 w-4 text-accent" />
              Job Discovery Settings
            </h3>
            
            <form onSubmit={handleRunScraper} className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-gray-400 font-bold uppercase">Job Title / Keywords</label>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g. Frontend Engineer"
                    className="w-full bg-[#050505] border border-border focus:border-accent p-2.5 rounded text-white focus:outline-none"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-gray-400 font-bold uppercase">Location Target</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. Remote, San Francisco, Bangalore"
                    className="w-full bg-[#050505] border border-border focus:border-accent p-2.5 rounded text-white focus:outline-none"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-gray-400 font-bold uppercase">Listing Scrape Limit ({limit})</label>
                  <input
                    type="range"
                    min="1"
                    max="30"
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value))}
                    className="w-full accent-accent"
                  />
                </div>
              </div>

              <div className="space-y-4">
                  <div className="space-y-2">
                  <label className="text-gray-400 font-bold uppercase block mb-1">Target Sources</label>
                  <div className="grid grid-cols-2 gap-3 text-[11px]">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={sources.remotive}
                        onChange={() => toggleSource("remotive")}
                        className="accent-accent"
                      />
                      <span>Remotive <span className="text-success text-[9px]">(FREE)</span></span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={sources.themuse}
                        onChange={() => toggleSource("themuse")}
                        className="accent-accent"
                      />
                      <span>The Muse <span className="text-success text-[9px]">(FREE)</span></span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={sources.jsearch}
                        onChange={() => toggleSource("jsearch")}
                        className="accent-accent"
                      />
                      <span>JSearch <span className="text-gray-500 text-[9px]">(API Key)</span></span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={sources.adzuna}
                        onChange={() => toggleSource("adzuna")}
                        className="accent-accent"
                      />
                      <span>Adzuna <span className="text-gray-500 text-[9px]">(API Key)</span></span>
                    </label>
                  </div>
                  <span className="text-[9px] text-gray-500 block mt-1 leading-relaxed">
                    Remotive & The Muse are free and require no API key. JSearch & Adzuna require keys — configure them in your Profile.
                  </span>
                </div>

                <div className="pt-2">
                  <label className="flex items-center gap-2 cursor-pointer select-none font-bold text-gray-400 uppercase">
                    <input
                      type="checkbox"
                      checked={useMock}
                      onChange={() => setUseMock(!useMock)}
                      className="accent-accent"
                    />
                    [DEBUG] Use Mock Sandbox Data
                  </label>
                  <span className="text-[10px] text-gray-500 block mt-1 leading-relaxed">
                    Select sandbox mode to inject local developer listings and bypass real network scraping times.
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={scraping}
                  className="w-full bg-accent text-black hover:bg-accent/80 p-3 rounded font-bold font-mono transition-all flex items-center justify-center gap-2 text-xs"
                >
                  <Play className="h-3.5 w-3.5 fill-black" />
                  RUN_JOB_DISCOVERY_CYCLE
                </button>
              </div>
            </form>

            {/* Scraping logs output */}
            {scrapeLogs.length > 0 && (
              <div className="bg-[#050505] border border-border p-4 rounded h-40 overflow-y-auto font-mono text-[10px] text-success leading-relaxed flex flex-col space-y-1">
                {scrapeLogs.map((log, idx) => (
                  <div key={idx}>{log}</div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        )}

        {actionMsg && (
          <div className="border border-accent/20 bg-accent/5 p-4 rounded text-xs font-mono text-accent">
            {actionMsg}
          </div>
        )}

        {matches.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-border rounded font-mono text-xs text-gray-500">
            [FEED: EMPTY] &bull; Open the Discovery Dashboard above and run a search to aggregate match recommendations.
          </div>
        ) : (
          <div className="space-y-4">
            {matches.map((match) => {
              const isOpen = selectedJob?.id === match.id;
              
              // Formatting nice source descriptions
              let cleanSource = match.source;
              if (match.source === "Web Direct") {
                if (match.url.includes("greenhouse.io")) cleanSource = "Greenhouse.io";
                else if (match.url.includes("lever.co")) cleanSource = "Lever.co";
                else if (match.url.includes("ashbyhq.com")) cleanSource = "AshbyHQ";
                else cleanSource = "Direct Apply Web";
              }

              return (
                <div
                  key={match.id}
                  className="console-panel p-5 rounded hover:border-accent/30 transition-all duration-200"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1">
                      <span className="text-[10px] text-gray-500 font-mono tracking-wider block font-bold uppercase">
                        {match.company}
                      </span>
                      <h4 className="font-bold text-sm text-white">{match.title}</h4>
                      <div className="flex items-center gap-1.5 text-xs text-gray-400 font-mono">
                        <MapPin className="h-3.5 w-3.5 text-gray-500" />
                        {match.location}
                      </div>
                    </div>
                    <div className="shrink-0 flex items-center gap-2">
                      {getScoreBadge(match.match_score)}
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-5 pt-3 border-t border-border">
                    <span className="text-[9px] text-gray-500 font-mono uppercase flex items-center gap-1">
                      <Globe className="h-3 w-3 text-gray-500" />
                      SOURCE: {cleanSource}
                    </span>
                    <button
                      onClick={() => setSelectedJob(isOpen ? null : match)}
                      className="flex items-center gap-1.5 text-xs text-accent hover:underline font-mono font-semibold"
                    >
                      {isOpen ? (
                        <>
                          Collapse_Details
                          <ChevronUp className="h-3 w-3" />
                        </>
                      ) : (
                        <>
                          Expand_Details
                          <ChevronDown className="h-3 w-3" />
                        </>
                      )}
                    </button>
                  </div>

                  {/* Expanded Section */}
                  {isOpen && (
                    <div className="mt-5 pt-5 border-t border-border space-y-6 font-mono text-xs animate-fadeIn">
                      <div className="space-y-2">
                        <span className="text-[10px] font-bold text-accent uppercase block">// AI_RATIONALE</span>
                        <p className="text-xs text-gray-300 leading-relaxed bg-black/40 border border-border p-4 rounded">
                          &gt; {match.match_rationale || "No evaluation found."}
                        </p>
                      </div>

                      {/* Alignments list */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <span className="text-[10px] font-bold text-success uppercase block">// MATCHING_SKILLS</span>
                          <div className="flex flex-wrap gap-1">
                            {match.matching_skills?.map((skill: string, idx: number) => (
                              <span key={idx} className="bg-success/5 border border-success/20 text-success text-[10px] px-2 py-0.5 rounded font-semibold">
                                + {skill.toLowerCase()}
                              </span>
                            )) || <span className="text-gray-500">None</span>}
                          </div>
                        </div>

                        <div className="space-y-2">
                          <span className="text-[10px] font-bold text-accent uppercase block">// MISSING_SKILLS</span>
                          <div className="flex flex-wrap gap-1">
                            {match.missing_skills?.map((skill: string, idx: number) => (
                              <span key={idx} className="bg-accent/5 border border-accent/20 text-accent text-[10px] px-2 py-0.5 rounded font-semibold">
                                - {skill.toLowerCase()}
                              </span>
                            )) || <span className="text-gray-500">None</span>}
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <div className="space-y-2">
                        <span className="text-[10px] font-bold text-gray-500 uppercase block">// RAW_DESCRIPTION</span>
                        <p className="text-xs text-gray-400 line-clamp-4 leading-relaxed font-sans">
                          {match.description}
                        </p>
                      </div>

                      {/* Console Controls */}
                      <div className="flex flex-wrap items-center gap-2 pt-2 justify-end">
                        <button
                          onClick={() => handleUpdateStatus(match.id, "ignored")}
                          className="flex items-center gap-1.5 px-3 py-2 border border-border bg-[#09090b] text-gray-400 hover:text-red-400 hover:border-red-500/20 transition-all font-semibold"
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                          [IGNORE]
                        </button>
                        <button
                          onClick={() => handleUpdateStatus(match.id, "saved")}
                          className="flex items-center gap-1.5 px-3 py-2 border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all font-semibold"
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                          [SAVE_TRACK]
                        </button>
                        <a
                          href={match.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1.5 px-3 py-2 border border-success text-success bg-success/5 hover:bg-success hover:text-black transition-all font-semibold"
                        >
                          [APPLY_DIRECT]
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
