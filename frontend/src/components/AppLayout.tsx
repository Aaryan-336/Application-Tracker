"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Loader2, Menu, X } from "lucide-react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const timeoutId = setTimeout(() => {
      if (isMounted && loading) {
        console.warn("Auth check timed out, falling back to login.");
        try {
          localStorage.removeItem("career_agent_token");
        } catch (e) {}
        router.push("/login");
      }
    }, 4000);

    async function verifyAuth() {
      let token = null;
      try {
        token = localStorage.getItem("career_agent_token");
      } catch (e) {
        console.error("Storage access failed:", e);
      }
      if (!token) {
        clearTimeout(timeoutId);
        router.push("/login");
        return;
      }
      try {
        const userData = await api.getMe();
        if (isMounted) {
          setUser(userData);
          setLoading(false);
          clearTimeout(timeoutId);
        }
      } catch (err) {
        console.error("Auth check failed:", err);
        if (isMounted) {
          try {
            localStorage.removeItem("career_agent_token");
          } catch (e) {}
          clearTimeout(timeoutId);
          router.push("/login");
        }
      }
    }
    verifyAuth();

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [router]);

  const handleLogout = () => {
    try {
      localStorage.removeItem("career_agent_token");
    } catch (e) {}
    router.push("/");
  };

  const navItems = [
    { index: "01", name: "DASHBOARD", href: "/dashboard" },
    { index: "02", name: "MATCH_FEED", href: "/jobs" },
    { index: "03", name: "PIPELINE", href: "/tracker" },
    { index: "04", name: "PROFILE", href: "/profile" },
    { index: "05", name: "GMAIL_SYNC", href: "/gmail" },
  ];

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#050505] text-[#e2e8f0]">
        <div className="flex flex-col items-center gap-3 data-mono">
          <Loader2 className="h-6 w-6 animate-spin text-accent" />
          <p className="text-xs text-gray-500 uppercase tracking-widest">Initialising Console...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#050505] md:flex-row text-[#e2e8f0]">
      {/* Desktop Console Sidebar */}
      <aside className="hidden w-64 border-r border-[#1e1e24] bg-[#09090b] p-6 md:flex md:flex-col md:justify-between shrink-0">
        <div className="space-y-10">
          <div className="space-y-1.5 accent-line pb-4 border-b border-[#1e1e24]">
            <h1 className="font-bold text-sm tracking-widest text-white data-mono">AGENT // CONSOLE</h1>
            <p className="text-[10px] text-gray-500 font-mono tracking-widest">SECURE DATA VAULT</p>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3.5 px-4 py-3 rounded text-xs font-mono tracking-wider transition-all ${
                    isActive
                      ? "bg-accent/10 border-l-2 border-accent text-accent font-bold"
                      : "text-gray-400 border-l-2 border-transparent hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <span className="text-[10px] opacity-55">[{item.index}]</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3.5 px-4 py-3 rounded text-xs font-mono tracking-wider text-gray-500 hover:text-red-400 hover:bg-red-500/5 transition-all text-left border-t border-[#1e1e24]"
        >
          <span>[x]</span>
          SHUTDOWN SESSION
        </button>
      </aside>

      {/* Mobile Top Header */}
      <header className="flex items-center justify-between border-b border-[#1e1e24] bg-[#09090b] px-6 py-4 md:hidden sticky top-0 z-40">
        <button
          onClick={() => setMenuOpen(true)}
          className="p-1 -ml-1 text-gray-400 hover:text-white transition-all focus:outline-none"
          aria-label="Open Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="space-y-0.5 text-center flex-1">
          <span className="font-bold text-xs tracking-widest text-white font-mono">AGENT // CONSOLE</span>
        </div>

        <button
          onClick={handleLogout}
          className="text-xs font-mono text-gray-500 hover:text-red-400 transition-all"
        >
          [SHUTDOWN]
        </button>
      </header>

      {/* Mobile Navigation Drawer Backdrop overlay */}
      <div 
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-50 md:hidden transition-opacity duration-300 ${
          menuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setMenuOpen(false)}
      />

      {/* Mobile Navigation Drawer Panel */}
      <aside 
        className={`fixed top-0 left-0 bottom-0 w-64 bg-[#09090b] border-r border-[#1e1e24] p-6 flex flex-col justify-between shrink-0 z-50 md:hidden transition-transform duration-300 ease-in-out ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="space-y-10">
          <div className="flex items-center justify-between pb-4 border-b border-[#1e1e24]">
            <div className="space-y-1">
              <h1 className="font-bold text-sm tracking-widest text-white font-mono">AGENT // CONSOLE</h1>
              <p className="text-[10px] text-gray-500 font-mono tracking-widest">SECURE DATA VAULT</p>
            </div>
            <button
              onClick={() => setMenuOpen(false)}
              className="p-1 -mr-1 text-gray-500 hover:text-white transition-all focus:outline-none"
              aria-label="Close Navigation Menu"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center gap-3.5 px-4 py-3 rounded text-xs font-mono tracking-wider transition-all ${
                    isActive
                      ? "bg-accent/10 border-l-2 border-accent text-accent font-bold"
                      : "text-gray-400 border-l-2 border-transparent hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <span className="text-[10px] opacity-55">[{item.index}]</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <button
          onClick={() => {
            setMenuOpen(false);
            handleLogout();
          }}
          className="flex items-center gap-3.5 px-4 py-3 rounded text-xs font-mono tracking-wider text-gray-500 hover:text-red-400 hover:bg-red-500/5 transition-all text-left border-t border-[#1e1e24]"
        >
          <span>[x]</span>
          SHUTDOWN SESSION
        </button>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 overflow-y-auto px-6 py-8 md:pb-8 max-w-5xl mx-auto w-full">
        {children}
      </main>
    </div>
  );
}
