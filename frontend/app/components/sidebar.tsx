"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  MessageSquare,
  Plug,
  Network,
  FileText,
  Box,
  Link2,
  Hash,
} from "lucide-react";
import { api, IngestionStats } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Chat", icon: MessageSquare },
  { href: "/connectors", label: "Connectors", icon: Plug },
  { href: "/entities", label: "Entities", icon: Network },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [stats, setStats] = useState<IngestionStats | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch(() => {});
    const interval = setInterval(() => {
      api.stats().then(setStats).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-64 h-screen flex flex-col border-r border-obsidian-700/50 bg-obsidian-900/50 backdrop-blur-sm">
      {/* Logo */}
      <div className="p-6 pb-4">
        <Link href="/" className="group flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20 group-hover:shadow-amber-500/30 transition-shadow">
            <span className="text-obsidian-950 font-display font-bold text-lg">B</span>
          </div>
          <div>
            <h1 className="font-display text-xl font-semibold text-sand-100 tracking-tight">
              Bitig
            </h1>
            <p className="text-[10px] text-obsidian-500 tracking-widest uppercase">
              Work Memory
            </p>
          </div>
        </Link>
      </div>

      <div className="glow-line mx-4" />

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 mt-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                active
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "text-sand-400 hover:text-sand-200 hover:bg-obsidian-800/50 border border-transparent"
              }`}
            >
              <Icon size={18} strokeWidth={active ? 2 : 1.5} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Stats */}
      {stats && (
        <div className="p-4 mx-3 mb-3 rounded-lg bg-obsidian-850/80 border border-obsidian-700/30">
          <p className="text-[10px] text-obsidian-500 tracking-widest uppercase mb-3 font-medium">
            Ingestion
          </p>
          <div className="space-y-2.5">
            <StatRow icon={FileText} label="Documents" value={stats.total_documents} />
            <StatRow icon={Box} label="Chunks" value={stats.total_chunks} />
            <StatRow icon={Hash} label="Entities" value={stats.total_entities} />
            <StatRow icon={Link2} label="Relations" value={stats.total_relations} />
          </div>
        </div>
      )}

      <div className="p-4 text-[10px] text-obsidian-600 text-center">
        v0.1.0 &middot; MIT License
      </div>
    </aside>
  );
}

function StatRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<any>;
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-sand-400">
        <Icon size={13} />
        <span className="text-xs">{label}</span>
      </div>
      <span className="text-xs font-mono text-sand-200">
        {value.toLocaleString()}
      </span>
    </div>
  );
}
