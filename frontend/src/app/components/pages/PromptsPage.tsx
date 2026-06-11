import { useState } from "react";
import { Plus, Search, X, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { useProjectStore } from "../../../store/projectStore";
import { usePrompts, useCreatePrompt, useTopics } from "../../../hooks/usePrompts";
import { Skeleton } from "../ui/skeleton";

const PLATFORM_COLORS: Record<string, string> = {
  ChatGPT: "#ff4d8b",
  Perplexity: "#1a3a3a",
  Gemini: "#b8a4ed",
  "AI Overviews": "#e8b94a",
  Copilot: "#ff6b5a",
};

const STATUSES = ["All Status", "active", "paused", "archived"];

function AddPromptModal({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const [text, setText] = useState("");
  const [topicId, setTopicId] = useState("");
  const { data: topics = [] } = useTopics(projectId);
  const createPrompt = useCreatePrompt(projectId);

  const handleSave = async () => {
    if (!text.trim()) return;
    try {
      await createPrompt.mutateAsync({
        text: text.trim(),
        topic_id: topicId || undefined,
      });
      toast.success("Prompt added");
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add prompt");
    }
  };

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
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full px-4 py-3 rounded-xl outline-none resize-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
              placeholder="What would your customers ask an AI chatbot?"
            />
          </div>
          {topics.length > 0 && (
            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Topic</label>
              <select
                value={topicId}
                onChange={(e) => setTopicId(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl outline-none"
                style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
              >
                <option value="">No topic</option>
                {topics.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-xl" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}>
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={createPrompt.isPending || !text.trim()}
              className="flex-1 py-2.5 rounded-xl disabled:opacity-60"
              style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
            >
              {createPrompt.isPending ? "Saving..." : "Save Prompt"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PromptsPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const { data: prompts = [], isLoading } = usePrompts(activeProjectId ?? undefined);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All Status");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  const filtered = prompts.filter((p) => {
    if (search && !p.text.toLowerCase().includes(search.toLowerCase())) return false;
    if (status !== "All Status" && p.status !== status) return false;
    return true;
  });

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {showModal && activeProjectId && (
        <AddPromptModal projectId={activeProjectId} onClose={() => setShowModal(false)} />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Prompts</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Track the questions your customers ask AI</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          disabled={!activeProjectId}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl disabled:opacity-60"
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
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2 rounded-xl outline-none"
          style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
        >
          {STATUSES.map((s) => <option key={s} value={s}>{s === "All Status" ? s : s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
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

        {isLoading && (
          <div className="p-4 space-y-3">
            {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        )}

        {!isLoading && filtered.length === 0 && (
          <div className="flex flex-col items-center py-16 gap-3">
            <MessageSquare size={32} style={{ color: "#d4cfc0" }} />
            <p style={{ fontSize: 14, color: "#9a9a9a" }}>
              {prompts.length === 0 ? "No prompts yet" : "No prompts match your filters"}
            </p>
            {activeProjectId && (
              <button onClick={() => setShowModal(true)} className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#0a0a0a", color: "#fff" }}>
                Add your first prompt
              </button>
            )}
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
                    <span key={t.id} className="px-2 py-0.5 rounded-full" style={{ fontSize: 10, background: "#fffaf0", color: "#6a6a6a", border: "1px solid #e5e5e5" }}>
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
              <span style={{ fontSize: 12, color: "#3a3a3a" }} className="truncate">{p.topic?.name ?? "—"}</span>
              <span
                className="px-2 py-0.5 rounded-full w-fit"
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  background: p.status === "active" ? "#dcfce7" : "#f5f0e0",
                  color: p.status === "active" ? "#16a34a" : "#9a9a9a",
                  textTransform: "capitalize",
                }}
              >
                {p.status}
              </span>
              {Object.keys(PLATFORM_COLORS).map((platform) => (
                <span key={platform} style={{ fontSize: 13, color: "#d4cfc0", fontWeight: 400 }}>
                  —
                </span>
              ))}
            </div>

            {/* Expanded row */}
            {expanded === p.id && (
              <div className="px-6 py-5" style={{ background: "#fffaf0", borderBottom: "1px solid #e5e5e5" }}>
                <p style={{ fontSize: 14, color: "#0a0a0a", marginBottom: 16, fontStyle: "italic" }}>"{p.text}"</p>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {Object.entries(PLATFORM_COLORS).map(([platform, color]) => (
                    <div key={platform} className="rounded-xl p-4" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                      <div className="flex items-center gap-1.5 mb-2">
                        <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                        <span style={{ fontSize: 11, fontWeight: 600, color: "#6a6a6a" }}>{platform}</span>
                      </div>
                      <div style={{ fontSize: 22, fontWeight: 700, color: "#d4cfc0" }}>—</div>
                      <div style={{ fontSize: 11, color: "#9a9a9a" }}>No data yet</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
