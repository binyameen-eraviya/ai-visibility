import { useMemo, useState } from "react";
import { CheckCircle, XCircle, Clock, ChevronRight, X, Play } from "lucide-react";
import { toast } from "sonner";
import { useProjectStore } from "../../../store/projectStore";
import { useRuns, useRunDetail, useRunPrompt } from "../../../hooks/useScrapeRuns";
import { useTrackingConfigs, usePlatforms, useCountries } from "../../../hooks/useTrackingConfigs";
import { usePrompts } from "../../../hooks/usePrompts";
import { Skeleton } from "../ui/skeleton";

const PLATFORM_COLORS: Record<string, string> = {
  "ChatGPT": "#ff4d8b",
  "Perplexity": "#1a3a3a",
  "Gemini": "#b8a4ed",
  "Google AI Overviews": "#e8b94a",
  "Microsoft Copilot": "#ff6b5a",
};

const statusIcon = (s: string) => {
  if (s === "success") return <CheckCircle size={16} color="#22c55e" />;
  if (s === "failed") return <XCircle size={16} color="#ef4444" />;
  return <Clock size={16} color="#e8b94a" />;
};

function renderAnswer(text: string) {
  return text.split(/\*\*(.*?)\*\*/g).map((part, i) =>
    i % 2 === 1 ? (
      <mark key={i} style={{ background: "#fef9c3", padding: "0 2px", borderRadius: 3, fontWeight: 600 }}>{part}</mark>
    ) : (
      part
    )
  );
}

const statusBg: Record<string, string> = {
  success: "#dcfce7", failed: "#fee2e2", running: "#fef9c3", pending: "#fef9c3", retrying: "#fef9c3",
};
const statusText: Record<string, string> = {
  success: "#16a34a", failed: "#dc2626", running: "#ca8a04", pending: "#ca8a04", retrying: "#ca8a04",
};

function formatTs(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

interface RunDetailModalProps {
  runId: string;
  projectId: string;
  promptText: string;
  platformName: string;
  platformColor: string;
  countryName: string;
  onClose: () => void;
}

function RunDetailModal({ runId, projectId, promptText, platformName, platformColor, countryName, onClose }: RunDetailModalProps) {
  const { data: detail, isLoading } = useRunDetail(projectId, runId);
  const status = detail?.status.toLowerCase() ?? "pending";
  const answerText: string | null = detail?.raw?.answer_text ?? detail?.raw?.text ?? null;
  const sources: string[] = detail?.raw?.sources ?? [];

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
          {isLoading ? (
            <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
          ) : !detail ? null : (
            <>
              <div className="rounded-xl p-4 space-y-3" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
                <div className="flex items-center gap-2">
                  {statusIcon(status)}
                  <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 11, fontWeight: 600, background: statusBg[status], color: statusText[status] }}>
                    {detail.status.charAt(0) + detail.status.slice(1).toLowerCase()}
                  </span>
                  <span className="ml-auto" style={{ fontSize: 12, color: "#9a9a9a" }}>{formatTs(detail.created_at)}</span>
                </div>
                <p style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>"{promptText}"</p>
                <div className="flex gap-3 flex-wrap">
                  {platformName && (
                    <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 11, background: platformColor + "20", color: platformColor, fontWeight: 600 }}>
                      {platformName}
                    </span>
                  )}
                  {countryName && <span style={{ fontSize: 12, color: "#6a6a6a" }}>{countryName}</span>}
                  {detail.duration_ms != null && (
                    <span style={{ fontSize: 12, color: "#6a6a6a" }}>⏱ {(detail.duration_ms / 1000).toFixed(1)}s</span>
                  )}
                </div>
                {detail.error && (
                  <p style={{ fontSize: 13, color: "#dc2626" }}>{detail.error}</p>
                )}
              </div>

              {answerText ? (
                <>
                  <div>
                    <h4 style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a", marginBottom: 10 }}>Captured AI Answer</h4>
                    <div
                      className="rounded-xl p-4"
                      style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#3a3a3a", lineHeight: 1.7, whiteSpace: "pre-wrap" }}
                    >
                      {renderAnswer(answerText)}
                    </div>
                  </div>
                  {sources.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a", marginBottom: 10 }}>Cited Sources</h4>
                      <div className="space-y-2">
                        {sources.map((s: string) => (
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
                  {status === "running" || status === "pending" ? (
                    <>
                      <Clock size={32} color="#e8b94a" />
                      <p style={{ fontSize: 14, color: "#6a6a6a" }}>Run is in progress...</p>
                    </>
                  ) : (
                    <>
                      <XCircle size={32} color="#ef4444" />
                      <p style={{ fontSize: 14, color: "#6a6a6a" }}>
                        {status === "failed" ? "This run failed. Check platform connectivity and retry." : "No result captured."}
                      </p>
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function NewRunModal({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const { data: prompts = [] } = usePrompts(projectId);
  const { data: platforms = [] } = usePlatforms();
  const { data: countries = [] } = useCountries();
  const runPrompt = useRunPrompt(projectId);
  const [promptId, setPromptId] = useState("");
  const [platformId, setPlatformId] = useState("");
  const [countryId, setCountryId] = useState("");

  const handleRun = async () => {
    if (!promptId || !platformId) return;
    try {
      await runPrompt.mutateAsync({ promptId, payload: { platform_id: platformId, country_id: countryId || undefined } });
      toast.success("Run queued successfully");
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to start run");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.3)" }} onClick={onClose}>
      <div className="w-full max-w-md rounded-2xl p-6" style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>New Run</h3>
          <button onClick={onClose} style={{ color: "#6a6a6a" }}><X size={18} /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Prompt</label>
            <select value={promptId} onChange={(e) => setPromptId(e.target.value)} className="w-full px-4 py-2.5 rounded-xl outline-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}>
              <option value="">Select a prompt...</option>
              {prompts.map((p) => <option key={p.id} value={p.id}>{p.text.slice(0, 60)}{p.text.length > 60 ? "…" : ""}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Platform</label>
            <select value={platformId} onChange={(e) => setPlatformId(e.target.value)} className="w-full px-4 py-2.5 rounded-xl outline-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}>
              <option value="">Select a platform...</option>
              {platforms.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Country <span style={{ color: "#9a9a9a", fontWeight: 400 }}>(optional)</span></label>
            <select value={countryId} onChange={(e) => setCountryId(e.target.value)} className="w-full px-4 py-2.5 rounded-xl outline-none"
              style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}>
              <option value="">Default (US)</option>
              {countries.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-xl" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}>Cancel</button>
            <button onClick={handleRun} disabled={runPrompt.isPending || !promptId || !platformId} className="flex-1 py-2.5 rounded-xl disabled:opacity-60 flex items-center justify-center gap-2"
              style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}>
              <Play size={14} />{runPrompt.isPending ? "Starting..." : "Run Now"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function RunHistoryPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId) ?? undefined;
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [showNewRun, setShowNewRun] = useState(false);

  const { data: runs = [], isLoading } = useRuns(activeProjectId);
  const { data: trackingConfigs = [] } = useTrackingConfigs(activeProjectId);
  const { data: prompts = [] } = usePrompts(activeProjectId);
  const { data: platforms = [] } = usePlatforms();
  const { data: countries = [] } = useCountries();

  const tcMap = useMemo(() => new Map(trackingConfigs.map((tc) => [tc.id, tc])), [trackingConfigs]);
  const promptMap = useMemo(() => new Map(prompts.map((p) => [p.id, p])), [prompts]);
  const platformMap = useMemo(() => new Map(platforms.map((p) => [p.id, p])), [platforms]);
  const countryMap = useMemo(() => new Map(countries.map((c) => [c.id, c])), [countries]);

  const getRunMeta = (tcId: string) => {
    const tc = tcMap.get(tcId);
    const prompt = tc ? promptMap.get(tc.prompt_id) : undefined;
    const platform = tc ? platformMap.get(tc.platform_id) : undefined;
    const country = tc ? countryMap.get(tc.country_id) : undefined;
    return {
      promptText: prompt?.text ?? "Tracking run",
      platformName: platform?.display_name ?? "",
      platformColor: platform ? (PLATFORM_COLORS[platform.display_name] ?? "#9a9a9a") : "#9a9a9a",
      countryName: country?.name ?? "",
    };
  };

  const selectedMeta = selectedRunId ? (() => {
    const run = runs.find((r) => r.id === selectedRunId);
    return run ? getRunMeta(run.tracking_config_id) : null;
  })() : null;

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {selectedRunId && selectedMeta && activeProjectId && (
        <RunDetailModal
          runId={selectedRunId}
          projectId={activeProjectId}
          {...selectedMeta}
          onClose={() => setSelectedRunId(null)}
        />
      )}
      {showNewRun && activeProjectId && (
        <NewRunModal projectId={activeProjectId} onClose={() => setShowNewRun(false)} />
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Run History</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>View and debug all scrape runs</p>
        </div>
        <button
          onClick={() => setShowNewRun(true)}
          disabled={!activeProjectId}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl disabled:opacity-60"
          style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
        >
          <Play size={14} /> New Run
        </button>
      </div>

      <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="grid px-4 py-3" style={{ gridTemplateColumns: "1fr 120px 120px 80px 90px 40px", borderBottom: "1px solid #e5e5e5" }}>
          {["Prompt", "Timestamp", "Platform", "Country", "Status", ""].map((h, i) => (
            <span key={i} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
          ))}
        </div>

        {isLoading && (
          <div className="p-4 space-y-3">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        )}

        {!isLoading && runs.length === 0 && (
          <div className="flex flex-col items-center py-16 gap-3">
            <Clock size={32} style={{ color: "#d4cfc0" }} />
            <p style={{ fontSize: 14, color: "#9a9a9a" }}>No runs yet</p>
            <p style={{ fontSize: 12, color: "#b4b0a0" }}>Use the "New Run" button to trigger your first scrape</p>
          </div>
        )}

        {runs.map((run) => {
          const { promptText, platformName, platformColor, countryName } = getRunMeta(run.tracking_config_id);
          const status = run.status.toLowerCase();
          return (
            <div
              key={run.id}
              className="grid px-4 py-3 items-center cursor-pointer hover:bg-[#ebe6d6] transition-colors"
              style={{ gridTemplateColumns: "1fr 120px 120px 80px 90px 40px", borderBottom: "1px solid #e5e5e5" }}
              onClick={() => setSelectedRunId(run.id)}
            >
              <div className="flex items-center gap-2 pr-4">
                {statusIcon(status)}
                <span style={{ fontSize: 13, color: "#0a0a0a" }} className="line-clamp-1">{promptText}</span>
              </div>
              <span style={{ fontSize: 12, color: "#6a6a6a" }}>{formatTs(run.created_at)}</span>
              {platformName ? (
                <span className="px-2 py-0.5 rounded-full w-fit" style={{ fontSize: 11, fontWeight: 600, background: platformColor + "20", color: platformColor }}>
                  {platformName.split(" ")[0]}
                </span>
              ) : <span style={{ fontSize: 12, color: "#d4cfc0" }}>—</span>}
              <span style={{ fontSize: 12, color: "#6a6a6a" }}>{countryName || "—"}</span>
              <span className="px-2 py-0.5 rounded-full w-fit" style={{ fontSize: 11, fontWeight: 600, background: statusBg[status] ?? "#f5f0e0", color: statusText[status] ?? "#6a6a6a" }}>
                {run.status.charAt(0) + run.status.slice(1).toLowerCase()}
              </span>
              <ChevronRight size={14} style={{ color: "#9a9a9a" }} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
