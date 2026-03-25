"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Mail,
  TicketCheck,
  Video,
  FileText,
  Clock,
  Loader2,
  Sparkles,
} from "lucide-react";
import { api, ChatResponse, Source } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await api.chat(question, 5, sourceFilter || undefined);
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Failed to get a response. Please check the backend connection.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
            {messages.map((msg, i) => (
              <div
                key={msg.id}
                className="animate-slide-up"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                {msg.role === "user" ? (
                  <UserMessage content={msg.content} />
                ) : (
                  <AssistantMessage content={msg.content} sources={msg.sources} />
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-3 text-sand-400 animate-fade-in">
                <Loader2 size={16} className="animate-spin text-amber-500" />
                <span className="text-sm">Searching your work memory...</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-obsidian-700/50 bg-obsidian-900/30 backdrop-blur-sm">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto px-6 py-4">
          {/* Source filter */}
          <div className="flex gap-2 mb-3">
            {[
              { value: "", label: "All Sources" },
              { value: "gmail", label: "Gmail", icon: Mail },
              { value: "jira", label: "Jira", icon: TicketCheck },
              { value: "meet", label: "Meet", icon: Video },
            ].map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => setSourceFilter(value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                  sourceFilter === value
                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                    : "text-obsidian-500 hover:text-sand-400 border border-obsidian-700/50 hover:border-obsidian-600"
                }`}
              >
                {Icon && <Icon size={12} />}
                {label}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your work history..."
              rows={1}
              className="input-field pr-12 resize-none min-h-[48px] max-h-[160px]"
              style={{ height: "48px" }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "48px";
                target.style.height = Math.min(target.scrollHeight, 160) + "px";
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-2 p-2 rounded-lg bg-amber-500 text-obsidian-950
                         transition-all hover:bg-amber-400 disabled:opacity-30 disabled:hover:bg-amber-500"
            >
              <Send size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center max-w-md animate-fade-in">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/20 flex items-center justify-center">
          <Sparkles size={28} className="text-amber-500" />
        </div>
        <h2 className="font-display text-2xl font-semibold text-sand-100 mb-2">
          Your Work Memory
        </h2>
        <p className="text-sand-400 text-sm leading-relaxed mb-6">
          Ask questions about your emails, Jira tickets, and meeting transcripts.
          Bitig searches across all your connected sources to find answers.
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {[
            "What was decided in last week's standup?",
            "Who is working on PROJ-42?",
            "Summarize recent emails from Alice",
          ].map((q) => (
            <button
              key={q}
              className="text-xs text-sand-400 px-3 py-1.5 rounded-full border border-obsidian-700/50 hover:border-amber-500/30 hover:text-amber-400 transition-all"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function UserMessage({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-br-sm bg-amber-500/10 border border-amber-500/20 text-sand-100 text-sm leading-relaxed">
        {content}
      </div>
    </div>
  );
}

function AssistantMessage({
  content,
  sources,
}: {
  content: string;
  sources?: Source[];
}) {
  return (
    <div className="space-y-3">
      <div className="text-sand-200 text-sm leading-relaxed whitespace-pre-wrap">
        {content}
      </div>
      {sources && sources.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sources.map((source, i) => (
            <SourceBadge key={i} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}

function SourceBadge({ source }: { source: Source }) {
  const icons: Record<string, React.ComponentType<any>> = {
    gmail: Mail,
    jira: TicketCheck,
    meet: Video,
  };
  const Icon = icons[source.source_type] || FileText;

  return (
    <div
      className="group relative badge bg-obsidian-800 border border-obsidian-700/50 text-sand-400 hover:border-amber-500/30 hover:text-amber-400 transition-all cursor-default"
      title={source.snippet}
    >
      <Icon size={11} />
      <span className="ml-1.5">{source.title}</span>
      <Clock size={9} className="ml-1.5 opacity-50" />
      <span className="ml-0.5 opacity-50 text-[10px]">
        {new Date(source.timestamp).toLocaleDateString()}
      </span>
    </div>
  );
}
