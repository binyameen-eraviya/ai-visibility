import { useState } from "react";
import { Plus, Search, Filter, ChevronDown, X, MessageSquare } from "lucide-react";

const PLATFORM_COLORS: Record<string, string> = {
  ChatGPT: "#ff4d8b",
  Perplexity: "#1a3a3a",
  Gemini: "#b8a4ed",
  "AI Overviews": "#e8b94a",
  Copilot: "#ff6b5a",
};

const PROMPTS = [
  {
    id: 1,
    text: "What's the best AI analytics tool for marketing teams?",
    topic: "Product Discovery",
    tags: ["analytics", "marketing"],
    status: "Active",
    platforms: { ChatGPT: 68, Perplexity: 82, Gemini: 55, "AI Overviews": 40, Copilot: 61 },
  },
  {
    id: 2,
    text: "Compare AI visibility tracking platforms",
    topic: "Competitive Research",
    tags: ["comparison", "AI tracking"],
    status: "Active",
    platforms: { ChatGPT: 45, Perplexity: 71, Gemini: 38, "AI Overviews": 29, Copilot: 52 },
  },
  {
    id: 3,
    text: "How do I track brand mentions in ChatGPT?",
    topic: "Use Cases",
    tags: ["brand monitoring", "ChatGPT"],
    status: "Active",
    platforms: { ChatGPT: 89, Perplexity: 64, Gemini: 72, "AI Overviews": 55, Copilot: 67 },
  },
  {
    id: 4,
    text: "Best tools for AI answer engine optimization",
    topic: "Product Discovery",
    tags: ["AEO", "optimization"],
    status: "Active",
    platforms: { ChatGPT: 34, Perplexity: 58, Gemini: 29, "AI Overviews": 62, Copilot: 41 },
  },
  {
    id: 5,
    text: "What is AI visibility tracking?",
    topic: "Education",
    tags: ["educational", "intro"],
    status: "Active",
    platforms: { ChatGPT: 72, Perplexity: 88, Gemini: 65, "AI Overviews": 48, Copilot: 59 },
  },
  {
    id: 6,
    text: "How do marketing teams measure AI search presence?",
    topic: "Use Cases",
    tags: ["marketing", "measurement"],
    status: "Paused",
    platforms: { ChatGPT: 0, Perplexity: 0, Gemini: 0, "AI Overviews": 0, Copilot: 0 },
  },
  {
    id: 7,
    text: "Which brands appear most in Perplexity answers for martech?",
    topic: "Competitive Research",
    tags: ["martech", "Perplexity"],
    status: "Active",
    platforms: { ChatGPT: 52, Perplexity: 94, Gemini: 43, "AI Overviews": 31, Copilot: 48 },
  },
];

const TOPICS = ["All Topics", "Product Discovery", "Competitive Research", "Use Cases", "Education"];
const STATUSES = ["All Status", "Active", "Paused", "Archived"];

function AddPromptModal({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.3)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl p-6"
        style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>Add Prompt</h3>
          <button onClick={onClose} style={{ color: "#6a6a6a" }}><X size={18} /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Prompt text</label>
            <textarea
              rows={3}
              className="w-full px-4 py-3 rounded-xl outline-none resize-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
              placeholder="What would your customers ask an AI chatbot?"
            />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Topic</label>
            <select
              className="w-full px-4 py-2.5 rounded-xl outline-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
            >
              {TOPICS.slice(1).map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Tags</label>
            <input
              className="w-full px-4 py-2.5 rounded-xl outline-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a" }}
              placeholder="analytics, marketing, comparison"
            />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 8 }}>Platforms</label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(PLATFORM_COLORS).map(([p, c]) => (
                <label key={p} className="flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" defaultChecked className="accent-[#1a3a3a]" />
                  <span style={{ fontSize: 13, color: "#0a0a0a" }}>{p}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-xl" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}>
              Cancel
            </button>
            <button onClick={onClose} className="flex-1 py-2.5 rounded-xl" style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}>
              Save Prompt
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PromptsPage() {
  const [search, setSearch] = useState("");
  const [topic, setTopic] = useState("All Topics");
  const [status, setStatus] = useState("All Status");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);

  const filtered = PROMPTS.filter((p) => {
    if (search && !p.text.toLowerCase().includes(search.toLowerCase())) return false;
    if (topic !== "All Topics" && p.topic !== topic) return false;
    if (status !== "All Status" && p.status !== status) return false;
    return true;
  });

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {showModal && <AddPromptModal onClose={() => setShowModal(false)} />}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Prompts</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Track the questions your customers ask AI</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl"
          style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
        >
          <Plus size={16} />
          Add Prompt
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#9a9a9a" }} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search prompts..."
            className="pl-8 pr-4 py-2 rounded-xl outline-none"
            style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#0a0a0a", width: 200 }}
          />
        </div>
        <select
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="px-3 py-2 rounded-xl outline-none"
          style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
        >
          {TOPICS.map((t) => <option key={t}>{t}</option>)}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2 rounded-xl outline-none"
          style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
        >
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        {/* Header row */}
        <div
          className="grid px-4 py-3"
          style={{ gridTemplateColumns: "1fr 140px 80px 80px 80px 80px 80px 80px", borderBottom: "1px solid #e5e5e5" }}
        >
          {["Prompt", "Topic", "Status", "ChatGPT", "Perplexity", "Gemini", "AI Overviews", "Copilot"].map((h) => (
            <span key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="flex flex-col items-center py-16 gap-3">
            <MessageSquare size={32} style={{ color: "#d4cfc0" }} />
            <p style={{ fontSize: 14, color: "#9a9a9a" }}>No prompts match your filters</p>
            <button onClick={() => setShowModal(true)} className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#0a0a0a", color: "#fff" }}>
              Add your first prompt
            </button>
          </div>
        )}

        {filtered.map((p) => (
          <div key={p.id}>
            <div
              className="grid px-4 py-3 items-center cursor-pointer hover:bg-[#ebe6d6] transition-colors"
              style={{ gridTemplateColumns: "1fr 140px 80px 80px 80px 80px 80px 80px", borderBottom: "1px solid #e5e5e5" }}
              onClick={() => setExpanded(expanded === p.id ? null : p.id)}
            >
              <div className="pr-4">
                <p style={{ fontSize: 13, color: "#0a0a0a" }} className="line-clamp-1">{p.text}</p>
                <div className="flex gap-1 mt-1 flex-wrap">
                  {p.tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded-full" style={{ fontSize: 10, background: "#fffaf0", color: "#6a6a6a", border: "1px solid #e5e5e5" }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
              <span style={{ fontSize: 12, color: "#3a3a3a" }} className="truncate">{p.topic}</span>
              <span
                className="px-2 py-0.5 rounded-full w-fit"
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  background: p.status === "Active" ? "#dcfce7" : "#f5f0e0",
                  color: p.status === "Active" ? "#16a34a" : "#9a9a9a",
                }}
              >
                {p.status}
              </span>
              {Object.entries(PLATFORM_COLORS).map(([platform, color]) => {
                const v = p.platforms[platform as keyof typeof p.platforms];
                return (
                  <span key={platform} style={{ fontSize: 13, color: v > 0 ? color : "#d4cfc0", fontWeight: v > 0 ? 600 : 400 }}>
                    {v > 0 ? `${v}%` : "—"}
                  </span>
                );
              })}
            </div>

            {/* Expanded row */}
            {expanded === p.id && (
              <div className="px-6 py-5" style={{ background: "#fffaf0", borderBottom: "1px solid #e5e5e5" }}>
                <p style={{ fontSize: 14, color: "#0a0a0a", marginBottom: 16, fontStyle: "italic" }}>"{p.text}"</p>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {Object.entries(PLATFORM_COLORS).map(([platform, color]) => {
                    const v = p.platforms[platform as keyof typeof p.platforms];
                    return (
                      <div key={platform} className="rounded-xl p-4" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                        <div className="flex items-center gap-1.5 mb-2">
                          <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                          <span style={{ fontSize: 11, fontWeight: 600, color: "#6a6a6a" }}>{platform}</span>
                        </div>
                        <div style={{ fontSize: 22, fontWeight: 700, color: v > 0 ? "#0a0a0a" : "#d4cfc0" }}>
                          {v > 0 ? `${v}%` : "—"}
                        </div>
                        <div style={{ fontSize: 11, color: "#9a9a9a" }}>visibility</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
