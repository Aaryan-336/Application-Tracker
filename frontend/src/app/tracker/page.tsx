"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { Calendar, FileText, ChevronDown, CheckCircle, Save } from "lucide-react";

const STAGES = [
  { key: "saved", label: "SAVED" },
  { key: "applied", label: "APPLIED" },
  { key: "assessment", label: "ASSESS" },
  { key: "interview", label: "INTERVIEW" },
  { key: "offer", label: "OFFER" },
  { key: "rejected", label: "REJECTED" },
];

export default function Tracker() {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeStage, setActiveStage] = useState("saved");
  const [editingApp, setEditingApp] = useState<any>(null);
  
  // Edit forms
  const [statusVal, setStatusVal] = useState("");
  const [notesVal, setNotesVal] = useState("");
  const [saveLoading, setSaveLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  async function loadApplications() {
    try {
      const data = await api.getTrackedApplications();
      setApplications(data);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApplications();
  }, []);

  const handleOpenEdit = (app: any) => {
    setEditingApp(app);
    setStatusVal(app.status);
    setNotesVal(app.notes || "");
    setSuccessMsg("");
  };

  const handleSaveUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingApp) return;

    setSaveLoading(true);
    setSuccessMsg("");
    try {
      await api.updateStatus(editingApp.id, statusVal, notesVal);
      setSuccessMsg("SYSTEM: Pipeline entry modified successfully.");
      setEditingApp(null);
      await loadApplications();
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch {
      // Error handling
    } finally {
      setSaveLoading(false);
    }
  };

  // Group to count
  const stageCounts = STAGES.reduce((acc, stage) => {
    acc[stage.key] = applications.filter((app) => app.status === stage.key).length;
    return acc;
  }, {} as Record<string, number>);

  const activeApps = applications.filter((app) => app.status === activeStage);

  if (loading) {
    return (
      <AppLayout>
        <div className="flex h-[50vh] items-center justify-center data-mono text-xs text-gray-500 uppercase tracking-widest">
          Parsing tracked records...
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-10">
        <div className="border-b border-border pb-6">
          <h2 className="text-xl font-bold tracking-widest text-white font-mono">// PIPELINE_TRACKER</h2>
          <p className="text-xs text-gray-500 font-mono mt-1">Status management pipeline for indexed applications</p>
        </div>

        {successMsg && (
          <div className="flex items-center gap-3 border border-success/20 bg-success/5 p-4 rounded text-xs font-mono text-success">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <p>{successMsg}</p>
          </div>
        )}

        {/* Tab Selector */}
        <div className="flex border-b border-border overflow-x-auto scrollbar-none pb-[1px] gap-1 font-mono text-xs">
          {STAGES.map((stage) => {
            const isActive = activeStage === stage.key;
            const count = stageCounts[stage.key] || 0;
            const paddedCount = count < 10 ? `0${count}` : `${count}`;
            return (
              <button
                key={stage.key}
                onClick={() => setActiveStage(stage.key)}
                className={`flex items-center gap-2 px-4 py-3 shrink-0 font-semibold transition-all border-b-2 ${
                  isActive
                    ? "border-accent text-accent font-bold bg-accent/5"
                    : "border-transparent text-gray-500 hover:text-white"
                }`}
              >
                {stage.label}
                <span className="opacity-55 font-normal">({paddedCount})</span>
              </button>
            );
          })}
        </div>

        {/* Contents */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 font-mono text-xs">
          {/* Applications list */}
          <div className="lg:col-span-2 space-y-3">
            {activeApps.length === 0 ? (
              <div className="text-center py-16 border border-dashed border-border rounded text-gray-500">
                [STAGE: EMPTY] &bull; No active listings tracked under this node.
              </div>
            ) : (
              <div className="space-y-2">
                {activeApps.map((app) => (
                  <div
                    key={app.id}
                    onClick={() => handleOpenEdit(app)}
                    className={`console-panel p-4.5 rounded cursor-pointer transition-all ${
                      editingApp?.id === app.id ? "border-accent bg-accent/5" : "border-border"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">
                          {app.company}
                        </span>
                        <h4 className="font-bold text-sm text-white">{app.title}</h4>
                        {app.applied_at && (
                          <div className="flex items-center gap-1.5 text-[10px] text-gray-400 pt-1">
                            <Calendar className="h-3.5 w-3.5 text-gray-500" />
                            DATE_APPLIED: {new Date(app.applied_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                      
                      <div className="shrink-0 flex items-center gap-2">
                        <span className="text-[11px] text-gray-400 font-bold">
                          [FIT: {app.match_score}%]
                        </span>
                      </div>
                    </div>

                    {app.notes && (
                      <p className="mt-3 text-xs text-gray-500 pl-2.5 border-l border-border leading-relaxed">
                        &gt; {app.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Edit Sidebar */}
          <div className="lg:col-span-1">
            {editingApp ? (
              <div className="console-panel p-6 rounded space-y-6 sticky top-6">
                <div>
                  <span className="text-[10px] text-accent font-bold uppercase tracking-wider block">{editingApp.company}</span>
                  <h3 className="text-sm font-bold text-white leading-tight mt-0.5">{editingApp.title}</h3>
                  <a
                    href={editingApp.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-block text-[10px] text-success hover:underline mt-2"
                  >
                    [OPEN_SOURCE_LISTING]
                  </a>
                </div>

                <form onSubmit={handleSaveUpdate} className="space-y-5">
                  <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                      PIPELINE_STATUS
                    </label>
                    <div className="relative">
                      <select
                        value={statusVal}
                        onChange={(e) => setStatusVal(e.target.value)}
                        className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white focus:outline-none appearance-none cursor-pointer"
                      >
                        {STAGES.map((s) => (
                          <option key={s.key} value={s.key} className="bg-[#09090b]">
                            {s.label}
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-4 top-3.5 h-3.5 w-3.5 text-gray-500 pointer-events-none" />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                      CONSOLE_NOTES
                    </label>
                    <textarea
                      value={notesVal}
                      onChange={(e) => setNotesVal(e.target.value)}
                      placeholder="Add recruiter feedback or schedule checkpoints..."
                      rows={5}
                      className="w-full rounded bg-black/40 border border-border px-4 py-3 text-xs text-white placeholder-gray-600 focus:outline-none resize-none"
                    />
                  </div>

                  <div className="flex gap-2 text-center">
                    <button
                      type="button"
                      onClick={() => setEditingApp(null)}
                      className="flex-1 py-2.5 rounded border border-border bg-[#09090b] text-gray-400 hover:text-white transition-all text-xs"
                    >
                      [CANCEL]
                    </button>
                    <button
                      type="submit"
                      disabled={saveLoading}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded border border-accent text-accent bg-accent/5 hover:bg-accent hover:text-black transition-all text-xs font-semibold"
                    >
                      <Save className="h-3.5 w-3.5" />
                      {saveLoading ? "SAVING..." : "[SAVE]"}
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              <div className="hidden lg:flex flex-col items-center justify-center h-44 border border-dashed border-border rounded p-6 text-center text-gray-500">
                <FileText className="h-6 w-6 text-gray-600 mb-2" />
                <p className="text-[10px] font-semibold uppercase tracking-wider">Select tracker node to edit values.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
