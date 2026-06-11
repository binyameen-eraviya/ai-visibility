import { useState } from "react";
import { CheckCircle, XCircle, Clock, ChevronRight, X } from "lucide-react";

const PLATFORM_COLORS: Record<string, string> = {
  ChatGPT: "#ff4d8b",
  Perplexity: "#1a3a3a",
  Gemini: "#b8a4ed",
  "AI Overviews": "#e8b94a",
  Copilot: "#ff6b5a",
};

const RUNS = [
  {
    id: 1, prompt: "What's the best AI analytics tool for marketing teams?", platform: "Perplexity",
    country: "🇺🇸 US", status: "success", duration: "4.2s", timestamp: "Jun 11, 2026 · 14:32",
    answer: `Based on my research, several AI analytics tools stand out for marketing teams in 2026. **Acme Corp** leads with its comprehensive AI visibility tracking, allowing teams to monitor brand presence across ChatGPT, Perplexity, and other AI platforms. Rival AI also offers strong features for competitive intelligence.\n\nFor marketing teams specifically, tools that track "AI answer engine" presence are becoming essential. Acme Corp's platform is particularly noted for its intuitive dashboard and daily automated tracking.\n\nOther notable mentions include CompeteBot for its affordability and DataSense for enterprise-grade reporting.`,
    mentions: true, sentiment: 78, sources: ["g2.com/categories/ai-analytics", "techcrunch.com/acme-review", "reddit.com/r/marketing"],
  },
  {
    id: 2, prompt: "Compare AI visibility tracking platforms", platform: "ChatGPT",
    country: "🇺🇸 US", status: "success", duration: "6.1s", timestamp: "Jun 11, 2026 · 13:20",
    answer: `When comparing AI visibility tracking platforms, the main contenders are Acme Corp, Rival AI, CompeteBot, DataSense, and InsightFlow.\n\n**Acme Corp** excels at multi-platform tracking (ChatGPT, Perplexity, Gemini, AI Overviews, Copilot), real-time sentiment analysis, and source citation tracking. It's ideal for marketing agencies managing multiple brands.\n\n**Rival AI** offers similar features but with a steeper learning curve. **CompeteBot** is budget-friendly but lacks Gemini integration.`,
    mentions: true, sentiment: 82, sources: ["capterra.com/ai-tracking", "g2.com/compare", "trustpilot.com/acme"],
  },
  {
    id: 3, prompt: "How do I track brand mentions in ChatGPT?", platform: "Gemini",
    country: "🇺🇸 US", status: "running", duration: "—", timestamp: "Jun 11, 2026 · 12:47",
    answer: null, mentions: null, sentiment: null, sources: [],
  },
  {
    id: 4, prompt: "Best tools for AI answer engine optimization", platform: "AI Overviews",
    country: "🇺🇸 US", status: "success", duration: "3.8s", timestamp: "Jun 11, 2026 · 11:14",
    answer: `AI Answer Engine Optimization (AEO) is a growing field. Top tools include Acme Corp for visibility tracking, along with content optimization platforms like MarketMuse and Clearscope for creating AI-friendly content.\n\nThe key to appearing in AI answers is having high-quality, authoritative content that AI models trust. Acme Corp's source tracking shows which domains get cited most in your niche.`,
    mentions: true, sentiment: 65, sources: ["producthunt.com/aeo", "hackernews.com/thread/aeo"],
  },
  {
    id: 5, prompt: "What is AI visibility tracking?", platform: "Copilot",
    country: "🇺🇸 US", status: "failed", duration: "—", timestamp: "Jun 11, 2026 · 09:55",
    answer: null, mentions: null, sentiment: null, sources: [],
  },
  {
    id: 6, prompt: "Which brands appear in Perplexity for martech tools?", platform: "Perplexity",
    country: "🇺🇸 US", status: "success", duration: "5.3s", timestamp: "Jun 10, 2026 · 22:10",
    answer: `In the martech category on Perplexity, Acme Corp frequently appears in AI answers alongside HubSpot, Salesforce, and several AI-native platforms. Brand visibility varies significantly by prompt phrasing.`,
    mentions: true, sentiment: 71, sources: ["g2.com/martech", "venturebeat.com/martech-2026"],
  },
];

const statusIcon = (s: string) => {
  if (s === "success") return <CheckCircle size={16} color="#22c55e" />;
  if (s === "failed") return <XCircle size={16} color="#ef4444" />;
  return <Clock size={16} color="#e8b94a" />;
};

const statusBg: Record<string, string> = { success: "#dcfce7", failed: "#fee2e2", running: "#fef9c3" };
const statusText: Record<string, string> = { success: "#16a34a", failed: "#dc2626", running: "#ca8a04" };

function RunDetailModal({ run, onClose }: { run: typeof RUNS[0]; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end" onClick={onClose}>
      <div
        className="h-full w-full max-w-xl overflow-y-auto"
        style={{ background: "#fffaf0", borderLeft: "1px solid #e5e5e5", boxShadow: "-8px 0 32px rgba(0,0,0,0.08)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-5 sticky top-0" style={{ background: "#fffaf0", borderBottom: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a" }}>Run Detail</h3>
          <button onClick={onClose} style={{ color: "#6a6a6a" }}><X size={18} /></button>
        </div>
        <div className="px-6 py-5 space-y-6">
          {/* Meta */}
          <div className="rounded-xl p-4 space-y-3" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
            <div className="flex items-center gap-2">
              {statusIcon(run.status)}
              <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 11, fontWeight: 600, background: statusBg[run.status], color: statusText[run.status] }}>
                {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
              </span>
              <span className="ml-auto" style={{ fontSize: 12, color: "#9a9a9a" }}>{run.timestamp}</span>
            </div>
            <p style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>"{run.prompt}"</p>
            <div className="flex gap-3">
              <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 11, background: (PLATFORM_COLORS[run.platform] || "#9a9a9a") + "20", color: PLATFORM_COLORS[run.platform] || "#9a9a9a", fontWeight: 600 }}>
                {run.platform}
              </span>
              <span style={{ fontSize: 12, color: "#6a6a6a" }}>{run.country}</span>
              {run.duration !== "—" && <span style={{ fontSize: 12, color: "#6a6a6a" }}>⏱ {run.duration}</span>}
            </div>
          </div>

          {run.answer ? (
            <>
              {/* Parsed results */}
              <div>
                <h4 style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a", marginBottom: 12 }}>Parsed Results</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-xl p-3 text-center" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: run.mentions ? "#22c55e" : "#ef4444" }}>
                      {run.mentions ? "✓" : "✗"}
                    </div>
                    <div style={{ fontSize: 11, color: "#6a6a6a" }}>Brand Mentioned</div>
                  </div>
                  <div className="rounded-xl p-3 text-center" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: "#0a0a0a" }}>{run.sentiment}</div>
                    <div style={{ fontSize: 11, color: "#6a6a6a" }}>Sentiment</div>
                  </div>
                  <div className="rounded-xl p-3 text-center" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: "#0a0a0a" }}>{run.sources.length}</div>
                    <div style={{ fontSize: 11, color: "#6a6a6a" }}>Sources Cited</div>
                  </div>
                </div>
              </div>

              {/* AI Answer */}
              <div>
                <h4 style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a", marginBottom: 10 }}>Captured AI Answer</h4>
                <div
                  className="rounded-xl p-4"
                  style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#3a3a3a", lineHeight: 1.7, whiteSpace: "pre-wrap" }}
                  dangerouslySetInnerHTML={{
                    __html: run.answer.replace(/\*\*(.*?)\*\*/g, '<mark style="background:#fef9c3;padding:0 2px;border-radius:3px;font-weight:600">$1</mark>'),
                  }}
                />
              </div>

              {/* Sources */}
              {run.sources.length > 0 && (
                <div>
                  <h4 style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a", marginBottom: 10 }}>Cited Sources</h4>
                  <div className="space-y-2">
                    {run.sources.map((s) => (
                      <div key={s} className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                        <div className="w-4 h-4 rounded flex items-center justify-center" style={{ background: "#ebe6d6" }}>
                          <span style={{ fontSize: 8, fontWeight: 700 }}>{s.charAt(0).toUpperCase()}</span>
                        </div>
                        <span style={{ fontSize: 13, color: "#1a3a3a" }}>{s}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="rounded-xl p-8 flex flex-col items-center gap-3" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
              {run.status === "running" ? (
                <>
                  <Clock size={32} color="#e8b94a" />
                  <p style={{ fontSize: 14, color: "#6a6a6a" }}>Run is in progress...</p>
                </>
              ) : (
                <>
                  <XCircle size={32} color="#ef4444" />
                  <p style={{ fontSize: 14, color: "#6a6a6a" }}>This run failed. Check platform connectivity and retry.</p>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function RunHistoryPage() {
  const [selected, setSelected] = useState<typeof RUNS[0] | null>(null);

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {selected && <RunDetailModal run={selected} onClose={() => setSelected(null)} />}

      <div className="mb-6">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Run History</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>View and debug all scrape runs</p>
      </div>

      <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div
          className="grid px-4 py-3"
          style={{ gridTemplateColumns: "1fr 120px 80px 80px 90px 40px", borderBottom: "1px solid #e5e5e5" }}
        >
          {["Prompt", "Timestamp", "Platform", "Country", "Status", ""].map((h, i) => (
            <span key={i} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
          ))}
        </div>

        {RUNS.map((run) => (
          <div
            key={run.id}
            className="grid px-4 py-3 items-center cursor-pointer hover:bg-[#ebe6d6] transition-colors"
            style={{ gridTemplateColumns: "1fr 120px 80px 80px 90px 40px", borderBottom: "1px solid #e5e5e5" }}
            onClick={() => setSelected(run)}
          >
            <div className="flex items-center gap-2 pr-4">
              {statusIcon(run.status)}
              <span style={{ fontSize: 13, color: "#0a0a0a" }} className="line-clamp-1">{run.prompt}</span>
            </div>
            <span style={{ fontSize: 12, color: "#6a6a6a" }}>{run.timestamp.split(" · ")[1]}</span>
            <span
              className="px-2 py-0.5 rounded-full w-fit"
              style={{ fontSize: 11, fontWeight: 600, background: (PLATFORM_COLORS[run.platform] || "#9a9a9a") + "20", color: PLATFORM_COLORS[run.platform] || "#9a9a9a" }}
            >
              {run.platform.split(" ")[0]}
            </span>
            <span style={{ fontSize: 12, color: "#6a6a6a" }}>{run.country}</span>
            <span
              className="px-2 py-0.5 rounded-full w-fit"
              style={{ fontSize: 11, fontWeight: 600, background: statusBg[run.status], color: statusText[run.status] }}
            >
              {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
            </span>
            <ChevronRight size={14} style={{ color: "#9a9a9a" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
