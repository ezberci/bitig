"use client";

import { useEffect, useState } from "react";
import {
  Mail,
  TicketCheck,
  Video,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { api, ConnectorState } from "@/lib/api";

const CONNECTOR_META: Record<
  string,
  {
    label: string;
    icon: React.ComponentType<any>;
    description: string;
    color: string;
  }
> = {
  gmail: {
    label: "Gmail",
    icon: Mail,
    description: "Emails and threads from your Gmail account",
    color: "text-red-400",
  },
  jira: {
    label: "Jira",
    icon: TicketCheck,
    description: "Issues, comments, and project updates",
    color: "text-blue-400",
  },
  meet: {
    label: "Google Meet",
    icon: Video,
    description: "Meeting transcripts and recordings",
    color: "text-green-400",
  },
};

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<ConnectorState[]>([]);
  const [syncing, setSyncing] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConnectors();
  }, []);

  async function loadConnectors() {
    try {
      const data = await api.connectors();
      setConnectors(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }

  async function handleSync(type: string) {
    setSyncing((prev) => new Set(prev).add(type));
    try {
      await api.syncConnector(type);
      await loadConnectors();
    } catch {
      // silently fail
    } finally {
      setSyncing((prev) => {
        const next = new Set(prev);
        next.delete(type);
        return next;
      });
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto px-8 py-10">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <h1 className="font-display text-3xl font-semibold text-sand-100 mb-2">
            Connectors
          </h1>
          <p className="text-sand-400 text-sm">
            Manage your data sources and trigger syncs.
          </p>
        </div>

        <div className="glow-line mb-8" />

        {loading ? (
          <div className="flex items-center justify-center py-20 text-sand-400">
            <Loader2 className="animate-spin mr-2" size={20} />
            Loading connectors...
          </div>
        ) : (
          <div className="grid gap-4">
            {connectors.map((connector, i) => (
              <ConnectorCard
                key={connector.connector_type}
                connector={connector}
                syncing={syncing.has(connector.connector_type)}
                onSync={() => handleSync(connector.connector_type)}
                delay={i * 0.1}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ConnectorCard({
  connector,
  syncing,
  onSync,
  delay,
}: {
  connector: ConnectorState;
  syncing: boolean;
  onSync: () => void;
  delay: number;
}) {
  const meta = CONNECTOR_META[connector.connector_type] || {
    label: connector.connector_type,
    icon: AlertCircle,
    description: "",
    color: "text-sand-400",
  };
  const Icon = meta.icon;

  return (
    <div
      className="card-hover p-6 animate-slide-up"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={`w-12 h-12 rounded-xl bg-obsidian-800 border border-obsidian-700/50 flex items-center justify-center ${meta.color}`}
          >
            <Icon size={22} />
          </div>

          {/* Info */}
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className="font-display text-lg font-semibold text-sand-100">
                {meta.label}
              </h3>
              <StatusBadge status={connector.status} configured={connector.configured} />
            </div>
            <p className="text-sm text-sand-400 mb-3">{meta.description}</p>

            <div className="flex items-center gap-5 text-xs text-obsidian-500">
              {connector.last_sync_at && (
                <span className="flex items-center gap-1.5">
                  <Clock size={12} />
                  Last sync: {new Date(connector.last_sync_at).toLocaleString()}
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <span className="font-mono text-sand-300">
                  {connector.document_count}
                </span>
                documents
              </span>
            </div>

            {connector.error && (
              <div className="mt-3 flex items-start gap-2 text-xs text-red-400/80 bg-red-500/5 border border-red-500/10 rounded-lg px-3 py-2">
                <XCircle size={14} className="mt-0.5 shrink-0" />
                {connector.error}
              </div>
            )}
          </div>
        </div>

        {/* Sync button */}
        <button
          onClick={onSync}
          disabled={syncing || !connector.configured}
          className="btn-primary flex items-center gap-2 text-sm shrink-0"
        >
          {syncing ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <RefreshCw size={14} />
          )}
          {syncing ? "Syncing..." : "Sync"}
        </button>
      </div>
    </div>
  );
}

function StatusBadge({
  status,
  configured,
}: {
  status: string;
  configured: boolean;
}) {
  if (!configured) {
    return (
      <span className="badge bg-obsidian-700/50 text-obsidian-500 border border-obsidian-600/50">
        Not configured
      </span>
    );
  }

  const styles: Record<string, string> = {
    idle: "bg-obsidian-700/50 text-sand-400 border border-obsidian-600/50",
    running: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
    success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    failed: "bg-red-500/10 text-red-400 border border-red-500/20",
  };

  const icons: Record<string, React.ReactNode> = {
    running: <Loader2 size={10} className="animate-spin mr-1" />,
    success: <CheckCircle2 size={10} className="mr-1" />,
    failed: <XCircle size={10} className="mr-1" />,
  };

  return (
    <span className={`badge ${styles[status] || styles.idle}`}>
      {icons[status]}
      {status}
    </span>
  );
}
