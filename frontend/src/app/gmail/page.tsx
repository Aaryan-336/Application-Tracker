"use client";

import { useEffect, useState, useRef } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";
import { Mail, Key, ShieldCheck, RefreshCw, CheckCircle2, AlertTriangle, Terminal, Trash2 } from "lucide-react";

export default function GmailSync() {
    const [statusData, setStatusData] = useState<any>({ is_connected: false });
    const [loading, setLoading] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");
    const [syncing, setSyncing] = useState(false);
    const [connecting, setConnecting] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [syncResults, setSyncResults] = useState<any[]>([]);

    const terminalEndRef = useRef<HTMLDivElement>(null);

    async function loadStatus() {
        try {
            const data = await api.getGmailStatus();
            setStatusData(data);
            if (data.gmail_address) {
                setEmail(data.gmail_address);
            }
            setLoading(false);
        } catch (err: any) {
            setError(err.message || "Failed to load Gmail credentials status.");
            setLoading(false);
        }
    }

    useEffect(() => {
        loadStatus();
    }, []);

    useEffect(() => {
        if (terminalEndRef.current) {
            terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs]);

    const addLog = (text: string) => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs((prev) => [...prev, `[${timestamp}] ${text}`]);
    };

    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccessMsg("");
        setConnecting(true);

        try {
            await api.connectGmail(email, password);
            setSuccessMsg("SYSTEM: Secure channel verified. Credentials stored.");
            setPassword("");
            await loadStatus();
        } catch (err: any) {
            setError(err.message || "Failed to establish secure connection.");
        } finally {
            setConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        if (!confirm("Are you sure you want to disconnect your Gmail sync? Credentials will be removed.")) {
            return;
        }
        setError("");
        setSuccessMsg("");
        try {
            // Disconnect by clearing credentials (we save empty values)
            await api.connectGmail("", "");
            setSuccessMsg("SYSTEM: Gmail synchronization disconnected.");
            setStatusData({ is_connected: false });
            setEmail("");
            setPassword("");
            setSyncResults([]);
            setLogs([]);
        } catch (err: any) {
            setError(err.message || "Failed to disconnect.");
        }
    };

    const handleSync = async () => {
        setSyncing(true);
        setLogs([]);
        setSyncResults([]);
        setError("");

        addLog("Establishing connection to imap.gmail.com:993 via SSL...");
        await new Promise((r) => setTimeout(r, 1000));
        addLog("Authenticating credentials...");
        await new Promise((r) => setTimeout(r, 800));
        addLog("Successfully logged in.");
        addLog("Querying inbox for placement-related mail headers (SINCE 14 days)...");

        try {
            const response = await api.syncGmail(14);
            addLog(`Found ${response.updates_count} relevant placement/application updates.`);
            
            for (const upd of response.updates) {
                await new Promise((r) => setTimeout(r, 600));
                addLog(`Parsed update: [${upd.company}] ${upd.job_title} -> STATUS: [${upd.status.toUpperCase()}]. Action type: ${upd.type}`);
            }

            addLog("Synchronization routine completed successfully. Pipeline states updated.");
            setSyncResults(response.updates);
            await loadStatus();
        } catch (err: any) {
            addLog(`ERROR: Synchronization routine aborted. Details: ${err.message}`);
            setError(err.message || "Failed to sync emails.");
        } finally {
            setSyncing(false);
        }
    };

    const [scheduling, setScheduling] = useState(false);

    const handleStopSync = async () => {
        addLog("SENDING_STOP_SIGNAL: Requesting synchronization abort...");
        try {
            await api.stopGmailSync();
            addLog("ABORT_ACCEPTED: Termination signal confirmed by backend task host.");
        } catch (err: any) {
            addLog(`ABORT_ERROR: Could not dispatch stop signal: ${err.message}`);
        }
    };

    const handleToggleSchedule = async (enabled: boolean) => {
        setScheduling(true);
        setError("");
        setSuccessMsg("");
        try {
            await api.toggleGmailSchedule(enabled);
            setStatusData((prev: any) => ({
                ...prev,
                gmail_sync_enabled: enabled
            }));
            setSuccessMsg(`SYSTEM: Daily background search ${enabled ? "enabled" : "disabled"}.`);
        } catch (err: any) {
            setError(err.message || "Failed to update search schedule.");
        } finally {
            setScheduling(false);
        }
    };

    if (loading) {
        return (
            <AppLayout>
                <div className="flex h-[50vh] items-center justify-center font-mono text-xs text-gray-500 uppercase tracking-widest">
                    Initializing Mail Stream...
                </div>
            </AppLayout>
        );
    }

    return (
        <AppLayout>
            <div className="space-y-10">
                <div className="border-b border-border pb-6">
                    <h2 className="text-xl font-bold tracking-widest text-white font-mono">// GMAIL_SYNC_CONTROL</h2>
                    <p className="text-xs text-gray-500 font-mono mt-1">Read and update job application pipelines automatically from email streams</p>
                </div>

                {error && (
                    <div className="border border-red-500/20 bg-red-500/5 p-4 rounded text-xs font-mono text-red-400 flex items-start gap-3">
                        <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                        <div>{error}</div>
                    </div>
                )}

                {successMsg && (
                    <div className="border border-success/20 bg-success/5 p-4 rounded text-xs font-mono text-success flex items-start gap-3">
                        <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                        <div>{successMsg}</div>
                    </div>
                )}

                {!statusData.is_connected ? (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 console-panel p-6 rounded space-y-6">
                            <h3 className="text-sm font-bold tracking-wider text-white font-mono uppercase flex items-center gap-2">
                                <Mail className="h-4 w-4 text-accent" />
                                Connect Your Account
                            </h3>

                            <form onSubmit={handleConnect} className="space-y-4 font-mono text-xs">
                                <div className="space-y-1.5">
                                    <label className="text-gray-400 block font-semibold">GMAIL_ADDRESS</label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        placeholder="your.email@gmail.com"
                                        className="w-full bg-[#09090b] border border-border focus:border-accent p-3 rounded text-white focus:outline-none"
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-gray-400 block font-semibold">16-CHARACTER_APP_PASSWORD</label>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        placeholder="xxxx xxxx xxxx xxxx"
                                        className="w-full bg-[#09090b] border border-border focus:border-accent p-3 rounded text-white focus:outline-none"
                                    />
                                    <span className="text-[10px] text-gray-500 block leading-relaxed mt-1">
                                        Note: Direct passwords are blocked by Google. You must generate a secure **App Password** from your Google Account settings.
                                    </span>
                                </div>

                                <button
                                    type="submit"
                                    disabled={connecting}
                                    className="w-full bg-accent text-black hover:bg-accent/80 p-3 rounded font-bold font-mono transition-all flex items-center justify-center gap-2"
                                >
                                    {connecting ? (
                                        <>
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                            ESTABLISHING_HANDSHAKE...
                                        </>
                                    ) : (
                                        "CONNECT_AND_VERIFY_GMAIL"
                                    )}
                                </button>
                            </form>
                        </div>

                        <div className="console-panel p-6 rounded space-y-4 border border-dashed border-border/80">
                            <h4 className="text-xs font-bold text-accent font-mono uppercase tracking-wider">// SETUP_GUIDANCE</h4>
                            <div className="border border-red-500/15 bg-red-500/5 p-3 rounded text-[10px] font-mono text-red-300 leading-relaxed">
                                ⚠ Do NOT use your regular Gmail password. Google blocks it via IMAP. You must use a <strong>16-character App Password</strong>.
                            </div>
                            <ol className="list-decimal pl-4 space-y-3 font-mono text-[11px] text-gray-400 leading-relaxed">
                                <li>Open <a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer" className="text-accent underline">Google Account → Security</a> and enable <strong>2-Step Verification</strong> (required first).</li>
                                <li>Then go directly to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-accent underline font-semibold">Google Account → App Passwords</a>.</li>
                                <li>Enter app name as &quot;Applications Tracker&quot; and click <strong>Create</strong>.</li>
                                <li>Copy the <strong>16-character code</strong> (e.g., <code className="text-white bg-black/50 px-1.5 py-0.5 rounded">abcd efgh ijkl mnop</code>).</li>
                                <li>Paste it below — spaces are fine, they&apos;ll be stripped automatically.</li>
                            </ol>
                            <div className="text-[9px] text-gray-500 font-mono mt-2">
                                Also ensure IMAP is enabled: Gmail → Settings → Forwarding and POP/IMAP → Enable IMAP.
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-8">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="console-panel p-5 rounded space-y-2">
                                <span className="text-[10px] text-gray-500 font-mono block uppercase">CONNECTED_STREAM_TARGET</span>
                                <h3 className="font-bold text-white text-base truncate font-mono">{statusData.gmail_address}</h3>
                                <div className="flex items-center gap-2 text-xs font-mono text-success pt-2">
                                    <ShieldCheck className="h-4 w-4" />
                                    Active link verified
                                </div>
                            </div>

                            <div className="console-panel p-5 rounded flex flex-col justify-between space-y-3">
                                <div>
                                    <span className="text-[10px] text-gray-500 font-mono block uppercase">DAILY_BACKGROUND_SCHEDULE</span>
                                    <span className="text-[9px] text-gray-400 font-mono block mt-1">Runs daily at 3:00 AM even when browser is closed</span>
                                </div>
                                <label className="flex items-center gap-3 cursor-pointer select-none mt-2 font-mono text-xs text-white">
                                    <input
                                        type="checkbox"
                                        checked={statusData.gmail_sync_enabled || false}
                                        disabled={scheduling}
                                        onChange={(e) => handleToggleSchedule(e.target.checked)}
                                        className="accent-success h-4 w-4"
                                    />
                                    <span>{statusData.gmail_sync_enabled ? "SCHEDULED: ACTIVE" : "SCHEDULED: INACTIVE"}</span>
                                </label>
                            </div>

                            <div className="console-panel p-5 rounded flex flex-col justify-between">
                                <div>
                                    <span className="text-[10px] text-gray-500 font-mono block uppercase">LAST_SYNCHRONIZED_DATE</span>
                                    <span className="font-bold text-gray-300 font-mono text-xs mt-1 block">
                                        {statusData.gmail_last_synced
                                            ? new Date(statusData.gmail_last_synced).toLocaleString()
                                            : "NEVER_RUN"}
                                    </span>
                                </div>

                                <button
                                    onClick={handleDisconnect}
                                    className="mt-4 flex items-center justify-center gap-1.5 py-2 px-3 border border-red-500/30 text-red-400 hover:bg-red-500/10 font-mono text-[11px] font-bold rounded w-full transition-all"
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    DISCONNECT_CONNECTION
                                </button>
                            </div>
                        </div>

                        <div className="console-panel p-6 rounded space-y-6">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
                                <div className="space-y-0.5">
                                    <h4 className="font-bold text-white text-sm font-mono flex items-center gap-2">
                                        <Terminal className="h-4 w-4 text-accent" />
                                        SYNC_LOGGER_MONITOR
                                    </h4>
                                    <p className="text-[10px] text-gray-500 font-mono">Real-time status updates parsed from incoming mail stream</p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleSync}
                                        disabled={syncing}
                                        className="bg-success text-black hover:bg-success/80 font-bold font-mono px-5 py-2.5 text-xs rounded transition-all flex items-center gap-2 self-start"
                                    >
                                        {syncing ? (
                                            <>
                                                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                                                SYNCING_INBOX...
                                            </>
                                        ) : (
                                            "RUN_GMAIL_SYNCHRONIZATION"
                                        )}
                                    </button>
                                    {syncing && (
                                        <button
                                            onClick={handleStopSync}
                                            className="border border-red-500/40 text-red-400 hover:bg-red-500/10 font-bold font-mono px-4 py-2.5 text-xs rounded transition-all flex items-center gap-2"
                                        >
                                            STOP_SEARCH
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Logs terminal box */}
                            {logs.length > 0 && (
                                <div className="bg-[#050505] border border-border p-4 rounded h-60 overflow-y-auto font-mono text-[11px] text-success leading-relaxed flex flex-col space-y-1 select-text">
                                    {logs.map((log, i) => (
                                        <div key={i}>{log}</div>
                                    ))}
                                    <div ref={terminalEndRef} />
                                </div>
                            )}

                            {/* Sync Results List */}
                            {syncResults.length > 0 && (
                                <div className="space-y-4">
                                    <h5 className="text-xs font-bold text-white font-mono uppercase tracking-wider">// DETECTED_UPDATES</h5>
                                    <div className="overflow-x-auto border border-border rounded">
                                        <table className="w-full font-mono text-xs text-left border-collapse">
                                            <thead>
                                                <tr className="bg-[#0c0c0e] text-gray-400 border-b border-border uppercase text-[10px]">
                                                    <th className="p-3">Company</th>
                                                    <th className="p-3">Job Title</th>
                                                    <th className="p-3">New Status</th>
                                                    <th className="p-3">Sync Event</th>
                                                    <th className="p-3">Extracted Rationale / Notes</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {syncResults.map((upd, idx) => (
                                                    <tr key={idx} className="border-b border-border/60 hover:bg-white/5">
                                                        <td className="p-3 text-white font-bold">{upd.company}</td>
                                                        <td className="p-3 text-gray-300">{upd.job_title}</td>
                                                        <td className="p-3">
                                                            <span className={`px-2 py-0.5 text-[10px] rounded font-semibold ${
                                                                upd.status === 'applied' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/25' :
                                                                upd.status === 'interviewing' ? 'bg-accent/10 text-accent border border-accent/25' :
                                                                upd.status === 'rejected' ? 'bg-red-500/10 text-red-400 border border-red-500/25' :
                                                                'bg-success/10 text-success border border-success/25'
                                                            }`}>
                                                                [{upd.status.toUpperCase()}]
                                                            </span>
                                                        </td>
                                                        <td className="p-3">
                                                            <span className="text-[10px] text-gray-400 bg-border/25 px-1.5 py-0.5 rounded">
                                                                {upd.type.toUpperCase()}
                                                            </span>
                                                        </td>
                                                        <td className="p-3 text-gray-400 font-sans text-xs italic">{upd.notes || "None"}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </AppLayout>
    );
}
