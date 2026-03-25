const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "change-me";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json();
}

// Types
export interface Source {
  document_id: string;
  title: string;
  source_type: string;
  snippet: string;
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  created_at: string;
}

export interface ChatHistoryItem {
  id: string;
  question: string;
  answer: string;
  sources: Source[];
  created_at: string;
}

export interface ConnectorState {
  connector_type: string;
  configured: boolean;
  status: string;
  last_sync_at: string | null;
  document_count: number;
  error: string | null;
}

export interface Entity {
  id: string;
  name: string;
  type: string;
  metadata: Record<string, string>;
  first_seen: string;
  last_seen: string;
}

export interface EntityGraph {
  nodes: Entity[];
  edges: {
    entity_a_id: string;
    entity_b_id: string;
    relation_type: string;
    document_id: string;
    confidence: number;
  }[];
}

export interface IngestionStats {
  total_documents: number;
  total_chunks: number;
  total_entities: number;
  total_relations: number;
}

// API functions
export const api = {
  chat(question: string, topK = 5, sourceFilter?: string) {
    return request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        question,
        top_k: topK,
        source_filter: sourceFilter || null,
      }),
    });
  },

  chatHistory(limit = 20) {
    return request<ChatHistoryItem[]>(`/api/chat/history?limit=${limit}`);
  },

  connectors() {
    return request<ConnectorState[]>("/api/connectors");
  },

  syncConnector(type: string) {
    return request<{ status: string; documents_fetched: number }>(
      `/api/connectors/${type}/sync`,
      { method: "POST" }
    );
  },

  entities(params?: { entity_type?: string; q?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.entity_type) searchParams.set("entity_type", params.entity_type);
    if (params?.q) searchParams.set("q", params.q);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return request<Entity[]>(`/api/entities${qs ? `?${qs}` : ""}`);
  },

  entityGraph() {
    return request<EntityGraph>("/api/entities/graph");
  },

  stats() {
    return request<IngestionStats>("/api/ingestion/stats");
  },

  health() {
    return request<Record<string, unknown>>("/api/health");
  },
};
