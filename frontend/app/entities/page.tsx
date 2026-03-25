"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import {
  User,
  FolderKanban,
  TicketCheck,
  Lightbulb,
  CheckSquare,
  Tag,
  Search,
  Loader2,
  Network,
} from "lucide-react";
import { api, Entity, EntityGraph } from "@/lib/api";

const TYPE_META: Record<
  string,
  {
    label: string;
    icon: React.ComponentType<any>;
    color: string;
    bg: string;
  }
> = {
  person: { label: "Person", icon: User, color: "#d4a254", bg: "bg-amber-500/10" },
  project: { label: "Project", icon: FolderKanban, color: "#60a5fa", bg: "bg-blue-500/10" },
  ticket: { label: "Ticket", icon: TicketCheck, color: "#34d399", bg: "bg-emerald-500/10" },
  decision: { label: "Decision", icon: Lightbulb, color: "#c084fc", bg: "bg-purple-500/10" },
  action_item: { label: "Action Item", icon: CheckSquare, color: "#fb923c", bg: "bg-orange-500/10" },
  topic: { label: "Topic", icon: Tag, color: "#f472b6", bg: "bg-pink-500/10" },
};

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [graph, setGraph] = useState<EntityGraph | null>(null);
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"list" | "graph">("list");

  useEffect(() => {
    loadEntities();
    api.entityGraph().then(setGraph).catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => loadEntities(), 300);
    return () => clearTimeout(timer);
  }, [typeFilter, search]);

  async function loadEntities() {
    setLoading(true);
    try {
      const data = await api.entities({
        entity_type: typeFilter || undefined,
        q: search || undefined,
        limit: 100,
      });
      setEntities(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-10">
        {/* Header */}
        <div className="flex items-start justify-between mb-8 animate-fade-in">
          <div>
            <h1 className="font-display text-3xl font-semibold text-sand-100 mb-2">
              Entities
            </h1>
            <p className="text-sand-400 text-sm">
              People, projects, tickets, and concepts extracted from your data.
            </p>
          </div>
          <div className="flex gap-1 bg-obsidian-800 rounded-lg p-1 border border-obsidian-700/50">
            <button
              onClick={() => setView("list")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                view === "list"
                  ? "bg-amber-500/15 text-amber-400"
                  : "text-sand-400 hover:text-sand-200"
              }`}
            >
              List
            </button>
            <button
              onClick={() => setView("graph")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
                view === "graph"
                  ? "bg-amber-500/15 text-amber-400"
                  : "text-sand-400 hover:text-sand-200"
              }`}
            >
              <Network size={12} />
              Graph
            </button>
          </div>
        </div>

        <div className="glow-line mb-6" />

        {view === "list" ? (
          <>
            {/* Filters */}
            <div className="flex items-center gap-3 mb-6 animate-slide-up">
              <div className="relative flex-1 max-w-xs">
                <Search
                  size={15}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-obsidian-500"
                />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search entities..."
                  className="input-field pl-9 py-2 text-sm"
                />
              </div>
              <div className="flex gap-1.5">
                <TypeFilterBtn
                  label="All"
                  active={typeFilter === ""}
                  onClick={() => setTypeFilter("")}
                />
                {Object.entries(TYPE_META).map(([type, meta]) => (
                  <TypeFilterBtn
                    key={type}
                    label={meta.label}
                    icon={meta.icon}
                    active={typeFilter === type}
                    onClick={() => setTypeFilter(type)}
                  />
                ))}
              </div>
            </div>

            {/* Entity list */}
            {loading ? (
              <div className="flex items-center justify-center py-20 text-sand-400">
                <Loader2 className="animate-spin mr-2" size={20} />
                Loading entities...
              </div>
            ) : entities.length === 0 ? (
              <div className="text-center py-20 text-sand-400 text-sm">
                No entities found.
              </div>
            ) : (
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {entities.map((entity, i) => (
                  <EntityCard
                    key={entity.id}
                    entity={entity}
                    delay={i * 0.03}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="animate-fade-in">
            {graph ? (
              <GraphView graph={graph} />
            ) : (
              <div className="flex items-center justify-center py-20 text-sand-400">
                <Loader2 className="animate-spin mr-2" size={20} />
                Loading graph...
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TypeFilterBtn({
  label,
  icon: Icon,
  active,
  onClick,
}: {
  label: string;
  icon?: React.ComponentType<any>;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
        active
          ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
          : "text-obsidian-500 hover:text-sand-400 border border-obsidian-700/50"
      }`}
    >
      {Icon && <Icon size={12} />}
      {label}
    </button>
  );
}

function EntityCard({ entity, delay }: { entity: Entity; delay: number }) {
  const meta = TYPE_META[entity.type] || {
    label: entity.type,
    icon: Tag,
    color: "#a89577",
    bg: "bg-obsidian-700/50",
  };
  const Icon = meta.icon;

  return (
    <div
      className="card-hover p-4 animate-slide-up"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-start gap-3">
        <div
          className={`w-9 h-9 rounded-lg ${meta.bg} flex items-center justify-center shrink-0`}
          style={{ color: meta.color }}
        >
          <Icon size={16} />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-sand-100 truncate">
            {entity.name}
          </h3>
          <p className="text-[11px] text-obsidian-500 mt-0.5">{meta.label}</p>
          <p className="text-[10px] text-obsidian-600 mt-1.5">
            Last seen {new Date(entity.last_seen).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
}

function GraphView({ graph }: { graph: EntityGraph }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = container.clientWidth;
    const h = 500;
    canvas.width = w * 2;
    canvas.height = h * 2;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.scale(2, 2);

    ctx.clearRect(0, 0, w, h);

    if (graph.nodes.length === 0) {
      ctx.fillStyle = "#47474e";
      ctx.font = '14px "DM Sans", sans-serif';
      ctx.textAlign = "center";
      ctx.fillText("No entities to display", w / 2, h / 2);
      return;
    }

    // Layout: circle
    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) / 2 - 60;

    const positions = new Map<string, { x: number; y: number }>();
    graph.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / graph.nodes.length - Math.PI / 2;
      positions.set(node.id, {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      });
    });

    // Draw edges
    ctx.lineWidth = 0.5;
    graph.edges.forEach((edge) => {
      const a = positions.get(edge.entity_a_id);
      const b = positions.get(edge.entity_b_id);
      if (!a || !b) return;

      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = "rgba(212, 162, 84, 0.12)";
      ctx.stroke();
    });

    // Draw nodes
    graph.nodes.forEach((node) => {
      const pos = positions.get(node.id);
      if (!pos) return;

      const meta = TYPE_META[node.type];
      const color = meta?.color || "#a89577";

      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.8;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Glow
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 10, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.1;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Label
      ctx.fillStyle = "#e0d0b8";
      ctx.font = '11px "DM Sans", sans-serif';
      ctx.textAlign = "center";
      ctx.fillText(node.name, pos.x, pos.y + 20);
    });
  }, [graph]);

  useEffect(() => {
    draw();
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, [draw]);

  return (
    <div ref={containerRef} className="card p-4">
      <canvas ref={canvasRef} />
      <div className="flex items-center justify-center gap-4 mt-4 pt-4 border-t border-obsidian-700/30">
        {Object.entries(TYPE_META).map(([type, meta]) => (
          <div key={type} className="flex items-center gap-1.5 text-xs text-sand-400">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: meta.color }}
            />
            {meta.label}
          </div>
        ))}
      </div>
    </div>
  );
}
