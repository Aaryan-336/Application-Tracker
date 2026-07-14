"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { Upload, FileText, CheckCircle2, User, Briefcase, Plus, X } from "lucide-react";

export default function Profile() {
  const [profile, setProfile] = useState<any>({
    full_name: "",
    preferred_roles: [],
    preferred_locations: [],
    salary_expectation: 0,
    experience_level: "",
    apify_api_token: "",
    jsearch_api_key: "",
    adzuna_app_id: "",
    adzuna_app_key: "",
  });
  const [resume, setResume] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  
  // Tag states
  const [roleInput, setRoleInput] = useState("");
  const [locInput, setLocInput] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const u = await api.getMe();
        setProfile({
          full_name: u.full_name || "",
          preferred_roles: u.preferred_roles || [],
          preferred_locations: u.preferred_locations || [],
          salary_expectation: u.salary_expectation || 0,
          experience_level: u.experience_level || "",
          apify_api_token: u.apify_api_token || "",
          jsearch_api_key: u.jsearch_api_key || "",
          adzuna_app_id: u.adzuna_app_id || "",
          adzuna_app_key: u.adzuna_app_key || "",
        });

        try {
          const r = await api.getResume();
          setResume(r);
        } catch {
          // No resume uploaded yet
        }
      } catch {
        setError("SYSTEM_ERROR: Failed to fetch profile details.");
      }
    }
    loadData();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("SYSTEM_WARNING: Supported CV structures must be in PDF format.");
      return;
    }

    setError("");
    setUploading(true);
    setSuccessMsg("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const parsedResume = await api.uploadResume(formData);
      setResume(parsedResume);
      setSuccessMsg("SYSTEM: File processed. AI agent parsed variables successfully.");
      
      if (profile.preferred_roles.length === 0 && parsedResume.preferred_roles.length > 0) {
        setProfile((prev: any) => ({
          ...prev,
          preferred_roles: parsedResume.preferred_roles,
        }));
      }
    } catch (err: any) {
      setError(err.message || "SYSTEM_ERROR: Failed to index file contents.");
    } finally {
      setUploading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setSavingProfile(true);

    try {
      const updated = await api.updateProfile(profile);
      setProfile({
        full_name: updated.full_name || "",
        preferred_roles: updated.preferred_roles || [],
        preferred_locations: updated.preferred_locations || [],
        salary_expectation: updated.salary_expectation || 0,
        experience_level: updated.experience_level || "",
        apify_api_token: updated.apify_api_token || "",
        jsearch_api_key: updated.jsearch_api_key || "",
        adzuna_app_id: updated.adzuna_app_id || "",
        adzuna_app_key: updated.adzuna_app_key || "",
      });
      setSuccessMsg("SYSTEM: Profile preference structures updated.");
    } catch (err: any) {
      setError(err.message || "SYSTEM_ERROR: Failed to commit updates.");
    } finally {
      setSavingProfile(false);
    }
  };

  const addRole = () => {
    if (roleInput.trim() && !profile.preferred_roles.includes(roleInput.trim())) {
      setProfile((prev: any) => ({
        ...prev,
        preferred_roles: [...prev.preferred_roles, roleInput.trim()],
      }));
      setRoleInput("");
    }
  };

  const removeRole = (indexToRemove: number) => {
    setProfile((prev: any) => ({
      ...prev,
      preferred_roles: prev.preferred_roles.filter((_: any, idx: number) => idx !== indexToRemove),
    }));
  };

  const addLoc = () => {
    if (locInput.trim() && !profile.preferred_locations.includes(locInput.trim())) {
      setProfile((prev: any) => ({
        ...prev,
        preferred_locations: [...prev.preferred_locations, locInput.trim()],
      }));
      setLocInput("");
    }
  };

  const removeLoc = (indexToRemove: number) => {
    setProfile((prev: any) => ({
      ...prev,
      preferred_locations: prev.preferred_locations.filter((_: any, idx: number) => idx !== indexToRemove),
    }));
  };

  return (
    <AppLayout>
      <div className="space-y-8 font-mono text-xs">
        <div className="border-b border-border pb-6">
          <h2 className="text-xl font-bold tracking-widest text-white font-mono">// PROFILE_MANAGER</h2>
          <p className="text-xs text-gray-500 font-mono mt-1">Configure profile data indices and upload search assets</p>
        </div>

        {error && (
          <div className="border border-danger/20 bg-danger/5 p-4 rounded text-red-300">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="flex items-center gap-3 border border-success/20 bg-success/5 p-4 rounded text-success">
            <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
            <p>{successMsg}</p>
          </div>
        )}

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Form */}
          <div className="console-panel p-6 rounded space-y-6">
            <div className="flex items-center gap-2.5 pb-4 border-b border-border">
              <User className="h-4 w-4 text-accent" />
              <h3 className="text-sm font-bold text-white tracking-widest">// PREFERENCE_INDEX</h3>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-5">
              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  FULL_NAME
                </label>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                  placeholder="e.g. Aaryan Khanna"
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  TARGET_ROLES
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={roleInput}
                    onChange={(e) => setRoleInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRole())}
                    placeholder="e.g. Backend Engineer"
                    className="flex-1 rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={addRole}
                    className="flex h-10 w-10 items-center justify-center rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all shrink-0"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {profile.preferred_roles.map((role: string, idx: number) => (
                    <span key={idx} className="inline-flex items-center gap-1.5 bg-accent/5 border border-accent/25 text-accent px-2 py-0.5 rounded font-semibold text-[10px]">
                      {role.toLowerCase()}
                      <button type="button" onClick={() => removeRole(idx)} className="hover:text-red-400 font-bold"><X className="h-3 w-3" /></button>
                    </span>
                  ))}
                  {profile.preferred_roles.length === 0 && <span className="text-[10px] text-gray-600 font-bold uppercase">[EMPTY]</span>}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  TARGET_LOCATIONS
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={locInput}
                    onChange={(e) => setLocInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addLoc())}
                    placeholder="e.g. Remote"
                    className="flex-1 rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={addLoc}
                    className="flex h-10 w-10 items-center justify-center rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all shrink-0"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {profile.preferred_locations.map((loc: string, idx: number) => (
                    <span key={idx} className="inline-flex items-center gap-1.5 bg-success/5 border border-success/20 text-success px-2 py-0.5 rounded font-semibold text-[10px]">
                      {loc.toLowerCase()}
                      <button type="button" onClick={() => removeLoc(idx)} className="hover:text-red-400 font-bold"><X className="h-3 w-3" /></button>
                    </span>
                  ))}
                  {profile.preferred_locations.length === 0 && <span className="text-[10px] text-gray-600 font-bold uppercase">[EMPTY]</span>}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  SALARY_EXPECTATION ($ / YEAR)
                </label>
                <input
                  type="number"
                  value={profile.salary_expectation || ""}
                  onChange={(e) => setProfile({ ...profile, salary_expectation: Number(e.target.value) })}
                  placeholder="e.g. 120000"
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
              </div>

              <div className="space-y-1.5 font-mono">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  EXPERIENCE_LEVEL
                </label>
                <select
                  value={profile.experience_level || ""}
                  onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })}
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500 font-mono"
                >
                  <option value="">[SELECT EXPERIENCE LEVEL]</option>
                  <option value="entry">Entry Level (0 - 2 years)</option>
                  <option value="mid">Mid Level (2 - 5 years)</option>
                  <option value="senior">Senior Level (5 - 8 years)</option>
                  <option value="lead">Lead / Principal (8+ years)</option>
                  <option value="executive">Executive (10+ years)</option>
                </select>
              </div>

              <div className="space-y-1.5 font-mono">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  APIFY_API_TOKEN
                </label>
                <input
                  type="password"
                  value={profile.apify_api_token || ""}
                  onChange={(e) => setProfile({ ...profile, apify_api_token: e.target.value })}
                  placeholder="e.g. apify_api_xxxxxxxxxxxxxxxxxxxx"
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
                <span className="text-[10px] text-gray-500 block leading-relaxed mt-1">
                  Optional: Supply your personal token to enable deep LinkedIn and Google job scrapers. Get your token under **Integrations** in your <a href="https://console.apify.com/account#/integrations" target="_blank" rel="noreferrer" className="text-accent underline font-semibold">Apify Console</a>.
                </span>
              </div>

              <div className="space-y-1.5 font-mono">
                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  JSEARCH_API_KEY <span className="text-accent">(RAPIDAPI)</span>
                </label>
                <input
                  type="password"
                  value={profile.jsearch_api_key || ""}
                  onChange={(e) => setProfile({ ...profile, jsearch_api_key: e.target.value })}
                  placeholder="e.g. a1b2c3d4e5f6g7h8i9j0..."
                  className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
                <span className="text-[10px] text-gray-500 block leading-relaxed mt-1">
                  Optional: Enables JSearch — real jobs from LinkedIn, Indeed & Glassdoor with direct apply links. Get a free key (500 req/month) at{" "}
                  <a href="https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch" target="_blank" rel="noreferrer" className="text-accent underline font-semibold">
                    RapidAPI → JSearch
                  </a>.
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="space-y-1.5">
                  <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                    ADZUNA_APP_ID
                  </label>
                  <input
                    type="text"
                    value={profile.adzuna_app_id || ""}
                    onChange={(e) => setProfile({ ...profile, adzuna_app_id: e.target.value })}
                    placeholder="e.g. abc12345"
                    className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                    ADZUNA_APP_KEY
                  </label>
                  <input
                    type="password"
                    value={profile.adzuna_app_key || ""}
                    onChange={(e) => setProfile({ ...profile, adzuna_app_key: e.target.value })}
                    placeholder="e.g. xyz789..."
                    className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-gray-500"
                  />
                </div>
              </div>
              <span className="text-[10px] text-gray-500 block leading-relaxed font-mono">
                Optional: Enables Adzuna — 250 free requests/day, jobs from 20+ countries. Get credentials at{" "}
                <a href="https://developer.adzuna.com" target="_blank" rel="noreferrer" className="text-accent underline font-semibold">
                  developer.adzuna.com
                </a>.
              </span>

              <button
                type="submit"
                disabled={savingProfile}
                className="flex w-full items-center justify-center h-11 rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all font-semibold tracking-wider"
              >
                {savingProfile ? "EXECUTING_UPDATE..." : "> SAVE_PREFERENCES"}
              </button>
            </form>
          </div>

          {/* CV upload */}
          <div className="space-y-6">
            <div className="console-panel p-6 rounded space-y-6">
              <div className="flex items-center gap-2.5 pb-4 border-b border-border">
                <Upload className="h-4 w-4 text-success" />
                <h3 className="text-sm font-bold text-white tracking-widest">// CV_ASSET_VAULT</h3>
              </div>

              {resume ? (
                <div className="flex items-start gap-4 rounded border border-border bg-black/30 p-4">
                  <FileText className="h-8 w-8 text-accent shrink-0" />
                  <div className="overflow-hidden">
                    <h4 className="font-semibold text-xs text-white truncate">{resume.filename}</h4>
                    <p className="text-[10px] text-gray-500 mt-1">UPLOADED: {new Date(resume.created_at).toLocaleDateString()}</p>
                    <span className="inline-flex mt-2 text-[9px] bg-success/5 border border-success/20 text-success px-2 py-0.5 rounded font-semibold uppercase">
                      ACTIVE_INDEX
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 border border-dashed border-border rounded bg-black/20 text-gray-500">
                  <FileText className="mx-auto h-8 w-8 text-gray-600 mb-2" />
                  <p className="text-xs font-semibold uppercase">[CV_ASSET: NONE]</p>
                  <p className="text-[10px] mt-1 max-w-[200px] mx-auto">Requires PDF schema to process match calculations.</p>
                </div>
              )}

              <div>
                <label className="flex flex-col items-center justify-center w-full h-28 border border-dashed border-border hover:border-gray-500 rounded bg-black/40 cursor-pointer transition-all">
                  <div className="flex flex-col items-center justify-center py-4">
                    {uploading ? (
                      <>
                        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent mb-1.5"></div>
                        <p className="text-[10px] text-accent uppercase font-bold">RUNNING_PARSER_FLOW...</p>
                      </>
                    ) : (
                      <>
                        <Upload className="h-6 w-6 text-gray-500 mb-1.5" />
                        <p className="text-[10px] text-gray-300 font-bold uppercase">Click to load PDF asset</p>
                      </>
                    )}
                  </div>
                  <input
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </label>
              </div>
            </div>

            {/* Resume profile list */}
            {resume && (
              <div className="console-panel p-6 rounded space-y-6">
                <div className="flex items-center gap-2.5 pb-4 border-b border-border">
                  <Briefcase className="h-4 w-4 text-accent" />
                  <h3 className="text-sm font-bold text-white tracking-widest">// PARSED_TELEMETRY</h3>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">// DETECTED_SKILLS</h4>
                    <div className="flex flex-wrap gap-1">
                      {resume.skills?.map((skill: string, idx: number) => (
                        <span key={idx} className="text-[10px] bg-black/40 border border-border text-gray-300 px-2 py-0.5 rounded">
                          {skill.toLowerCase()}
                        </span>
                      ))}
                    </div>
                  </div>

                  {resume.experience?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">// WORK_TIMELINE</h4>
                      <div className="space-y-3 pl-3 border-l border-border">
                        {resume.experience.map((exp: any, idx: number) => (
                          <div key={idx} className="relative space-y-0.5">
                            <span className="absolute -left-[16.5px] top-1 h-2 w-2 rounded-full bg-accent"></span>
                            <h5 className="font-bold text-xs text-white">{exp.role} &bull; <span className="text-gray-400 font-normal">{exp.company}</span></h5>
                            <p className="text-[9px] text-gray-500">{exp.duration}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
