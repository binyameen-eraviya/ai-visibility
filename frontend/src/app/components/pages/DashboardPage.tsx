import { useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, CheckCircle, XCircle, Clock, ExternalLink, BarChart2 } from "lucide-react";
import { useProjectStore } from "../../../store/projectStore";
import { useBrands, type Brand } from "../../../hooks/useBrands";
import { usePlatforms, useTrackingConfigs, type Platform } from "../../../hooks/useTrackingConfigs";
import { useDailyMetrics, useSourceMetrics, type DailyMetric, type SourceMetric } from "../../../hooks/useReports";
import { useRuns } from "../../../hooks/useScrapeRuns";
import { usePrompts } from "../../../hooks/usePrompts";
import { Skeleton } from "../ui/skeleton";

const PLATFORM_COLORS: Record<string, string> = {
  "ChatGPT": "#ff4d8b",
  "Perplexity": "#1a3a3a",
  "Gemini": "#b8a4ed",
  "Google AI Overviews": "#e8b94a",
  "Microsoft Copilot": "#ff6b5a",
};

const SOURCE_TYPE_COLORS: Record<string, string> = {
  REVIEW_SITE: "#ff4d8b", REDDIT: "#ff6b5a", EDITORIAL: "#1a3a3a",
  CORPORATE: "#22c55e", UGC: "#b8a4ed", REFERENCE: "#e8b94a", OTHER: "#9a9a9a",
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  REVIEW_SITE: "Review Site", REDDIT: "Reddit", EDITORIAL: "Editorial",
  CORPORATE: "Corporate", UGC: "UGC", REFERENCE: "Reference", OTHER: "Other",
};

function buildChartData(metrics: DailyMetric[], platforms: Platform[]) {
  if (!metrics.length) return [];
  const platformMap = new Map(platforms.map((p) => [p.id, p.display_name]));
  const byDate = new Map<string, Map<string, number[]>>();
  for (const m of metrics) {
    const name = platformMap.get(m.platform_id);
    if (!name) continue;
    if (!byDate.has(m.date)) byDate.set(m.date, new Map());
    const dateMap = byDate.get(m.date)!;
    if (!dateMap.has(name)) dateMap.set(name, []);
    dateMap.get(name)!.push(m.visibility_pct);
  }
  return Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, platformData]) => {
      const row: Record<string, any> = { date: date.slice(5).replace("-", "/") };
      for (const [name, vals] of platformData) {
        row[name] = Math.round(vals.reduce((s, v) => s + v, 0) / vals.length);
      }
      return row;
    });
}

function aggregateMetrics(metrics: DailyMetric[], primaryBrandId?: string) {
  const filtered = primaryBrandId ? metrics.filter((m) => m.brand_id === primaryBrandId) : metrics;
  if (!filtered.length) return null;
  const withPos = filtered.filter((m) => m.avg_position != null);
  const withSent = filtered.filter((m) => m.avg_sentiment != null);
  return {
    visibility: filtered.reduce((s, m) => s + m.visibility_pct, 0) / filtered.length,
    avgPosition: withPos.length ? withPos.reduce((s, m) => s + (m.avg_position ?? 0), 0) / withPos.length : null,
    sentiment: withSent.length ? withSent.reduce((s, m) => s + (m.avg_sentiment ?? 0), 0) / withSent.length : null,
    shareOfVoice: filtered.reduce((s, m) => s + m.share_of_voice, 0) / filtered.length,
  };
}

function aggregateByBrand(metrics: DailyMetric[], brands: Brand[]) {
  if (!metrics.length) return [];
  const brandMap = new Map(brands.map((b) => [b.id, b]));
  const byBrand = new Map<string, DailyMetric[]>();
  for (const m of metrics) {
    if (!byBrand.has(m.brand_id)) byBrand.set(m.brand_id, []);
    byBrand.get(m.brand_id)!.push(m);
  }
  return Array.from(byBrand.entries())
    .map(([brandId, ms]) => {
      const brand = brandMap.get(brandId);
      const withPos = ms.filter((m) => m.avg_position != null);
      const withSent = ms.filter((m) => m.avg_sentiment != null);
      return {
        brand: brand?.name ?? "Unknown",
        isYou: brand?.is_primary ?? false,
        visibility: Math.round((ms.reduce((s, m) => s + m.visibility_pct, 0) / ms.length) * 10) / 10,
        position: withPos.length ? Math.round((withPos.reduce((s, m) => s + (m.avg_position ?? 0), 0) / withPos.length) * 10) / 10 : null,
        sentiment: withSent.length ? Math.round(withSent.reduce((s, m) => s + (m.avg_sentiment ?? 0), 0) / withSent.length) : null,
        trend: 0,
      };
    })
    .sort((a, b) => b.visibility - a.visibility);
}

function aggregateSources(metrics: SourceMetric[]) {
  if (!metrics.length) return [];
  const byDomain = new Map<string, { citations: number; type: string }>();
  for (const m of metrics) {
    if (!byDomain.has(m.domain)) byDomain.set(m.domain, { citations: 0, type: m.source_type });
    byDomain.get(m.domain)!.citations += m.citation_count;
  }
  return Array.from(byDomain.entries())
    .map(([domain, { citations, type }]) => ({ domain, citations, type }))
    .sort((a, b) => b.citations - a.citations)
    .slice(0, 7);
}

function formatRelativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  return `${Math.floor(hrs / 24)} days ago`;
}

function MetricCard({
  label, value, bg, textColor, noData,
}: {
  label: string; value: string; bg: string; textColor: string; noData?: boolean;
}) {
  return (
    <div className="rounded-2xl p-6 flex flex-col gap-3" style={{ background: bg }}>
      <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase", color: textColor, opacity: 0.7 }}>
        {label}
      </div>
      <div style={{ fontSize: 36, fontWeight: 600, color: textColor, lineHeight: 1, letterSpacing: "-0.5px" }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: textColor, opacity: 0.4 }}>
        {noData ? "No data yet" : "vs last period"}
      </div>
    </div>
  );
}

const statusIcon = (s: string) => {
  if (s === "success") return <CheckCircle size={14} color="#22c55e" />;
  if (s === "failed") return <XCircle size={14} color="#ef4444" />;
  return <Clock size={14} color="#e8b94a" />;
};

const statusBg: Record<string, string> = {
  success: "#dcfce7", failed: "#fee2e2", running: "#fef9c3", pending: "#fef9c3", retrying: "#fef9c3",
};
const statusText: Record<string, string> = {
  success: "#16a34a", failed: "#dc2626", running: "#ca8a04", pending: "#ca8a04", retrying: "#ca8a04",
};

export function DashboardPage() {
  const navigate = useNavigate();
  const activeProjectId = useProjectStore((s) => s.activeProjectId) ?? undefined;
  const [activePlatforms, setActivePlatforms] = useState(Object.keys(PLATFORM_COLORS));

  const { data: dailyMetrics = [], isLoading: loadingMetrics } = useDailyMetrics(activeProjectId);
  const { data: sourceMetrics = [], isLoading: loadingSources } = useSourceMetrics(activeProjectId);
  const { data: recentRuns = [], isLoading: loadingRuns } = useRuns(activeProjectId);
  const { data: brands = [] } = useBrands(activeProjectId);
  const { data: platforms = [] } = usePlatforms();
  const { data: trackingConfigs = [] } = useTrackingConfigs(activeProjectId);
  const { data: prompts = [] } = usePrompts(activeProjectId);

  const primaryBrand = useMemo(() => brands.find((b) => b.is_primary), [brands]);
  const chartData = useMemo(() => buildChartData(dailyMetrics, platforms), [dailyMetrics, platforms]);
  const competitorData = useMemo(() => aggregateByBrand(dailyMetrics, brands), [dailyMetrics, brands]);
  const sourcesData = useMemo(() => aggregateSources(sourceMetrics), [sourceMetrics]);
  const aggregated = useMemo(() => aggregateMetrics(dailyMetrics, primaryBrand?.id), [dailyMetrics, primaryBrand]);
  const tcMap = useMemo(() => new Map(trackingConfigs.map((tc) => [tc.id, tc])), [trackingConfigs]);
  const promptMap = useMemo(() => new Map(prompts.map((p) => [p.id, p])), [prompts]);
  const platformMap = useMemo(() => new Map(platforms.map((p) => [p.id, p])), [platforms]);

  const hasMetrics = dailyMetrics.length > 0;

  const togglePlatform = (p: string) =>
    setActivePlatforms((prev) =>
      prev.includes(p) ? (prev.length > 1 ? prev.filter((x) => x !== p) : prev) : [...prev, p]
    );

  return (
    <div className="space-y-6" style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loadingMetrics ? (
          [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-32 rounded-2xl" />)
        ) : (
          <>
            <MetricCard label="Visibility" value={aggregated ? `${aggregated.visibility.toFixed(1)}%` : "—"} bg="#1a3a3a" textColor="#ffffff" noData={!hasMetrics} />
            <MetricCard label="Avg Position" value={aggregated?.avgPosition != null ? aggregated.avgPosition.toFixed(1) : "—"} bg="#b8a4ed" textColor="#0a0a0a" noData={!hasMetrics} />
            <MetricCard label="Sentiment" value={aggregated?.sentiment != null ? `${Math.round(aggregated.sentiment)}/100` : "—"} bg="#ffb084" textColor="#0a0a0a" noData={!hasMetrics} />
            <MetricCard label="Share of Voice" value={aggregated ? `${aggregated.shareOfVoice.toFixed(1)}%` : "—"} bg="#e8b94a" textColor="#0a0a0a" noData={!hasMetrics} />
          </>
        )}
      </div>

      {/* Main visibility chart */}
      <div className="rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a" }}>AI Visibility Over Time</h3>
            <p style={{ fontSize: 13, color: "#6a6a6a", marginTop: 2 }}>% of prompts where your brand is mentioned</p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(PLATFORM_COLORS).map(([platform, color]) => {
              const active = activePlatforms.includes(platform);
              return (
                <button
                  key={platform}
                  onClick={() => togglePlatform(platform)}
                  className="px-2.5 py-1 rounded-full flex items-center gap-1.5 transition-all"
                  style={{
                    fontSize: 11, fontWeight: 500,
                    background: active ? color : "#fffaf0",
                    color: active ? (color === "#1a3a3a" ? "#fff" : "#0a0a0a") : "#6a6a6a",
                    border: `1px solid ${active ? color : "#e5e5e5"}`,
                    opacity: active ? 1 : 0.6,
                  }}
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: active ? (color === "#1a3a3a" ? "#fff" : color) : "#9a9a9a" }} />
                  {platform}
                </button>
              );
            })}
          </div>
        </div>

        {loadingMetrics ? (
          <Skeleton className="w-full h-64 rounded-xl" />
        ) : !hasMetrics ? (
          <div className="flex flex-col items-center justify-center gap-3" style={{ height: 280 }}>
            <BarChart2 size={36} style={{ color: "#d4cfc0" }} />
            <p style={{ fontSize: 15, fontWeight: 500, color: "#9a9a9a" }}>No data yet</p>
            <p style={{ fontSize: 13, color: "#b4b0a0" }}>Set up tracking to see your AI visibility</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <defs>
                {Object.entries(PLATFORM_COLORS).map(([p, c]) => (
                  <linearGradient key={p} id={`grad-${p.replace(/\s+/g, "-")}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={c} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={c} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9a9a9a" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#9a9a9a" }} axisLine={false} tickLine={false} unit="%" />
              <Tooltip
                contentStyle={{ background: "#fffaf0", border: "1px solid #e5e5e5", borderRadius: 12, fontSize: 12 }}
                formatter={(v: any) => [`${v}%`]}
              />
              {Object.entries(PLATFORM_COLORS).map(([platform, color]) =>
                activePlatforms.includes(platform) ? (
                  <Area key={platform} type="monotone" dataKey={platform} stroke={color} strokeWidth={2}
                    fill={`url(#grad-${platform.replace(/\s+/g, "-")})`} dot={false} activeDot={{ r: 4 }} />
                ) : null
              )}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Bottom 2-col */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Competitors */}
        <div className="lg:col-span-3 rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Top Competitors</h3>
          {loadingMetrics ? (
            <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
          ) : !hasMetrics ? (
            <div className="flex flex-col items-center py-10 gap-2">
              <p style={{ fontSize: 14, color: "#9a9a9a" }}>Set up tracking to see your AI visibility</p>
              <p style={{ fontSize: 12, color: "#b4b0a0" }}>Competitor rankings appear once data is collected</p>
            </div>
          ) : (
            <div className="space-y-0">
              <div className="grid gap-2 pb-2" style={{ gridTemplateColumns: "1fr 80px 70px 70px 64px", borderBottom: "1px solid #e5e5e5" }}>
                {["Brand", "Visibility", "Position", "Sentiment", "30d"].map((h) => (
                  <span key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
                ))}
              </div>
              {competitorData.map((c) => (
                <div key={c.brand} className="grid gap-2 py-3 items-center"
                  style={{ gridTemplateColumns: "1fr 80px 70px 70px 64px", borderBottom: "1px solid #e5e5e5", borderLeft: c.isYou ? "3px solid #1a3a3a" : "3px solid transparent", paddingLeft: c.isYou ? 8 : 0 }}>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0" style={{ background: c.isYou ? "#1a3a3a" : "#ebe6d6" }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: c.isYou ? "#fff" : "#6a6a6a" }}>{c.brand.charAt(0)}</span>
                    </div>
                    <span style={{ fontSize: 13, fontWeight: c.isYou ? 600 : 400, color: "#0a0a0a" }}>{c.brand}</span>
                    {c.isYou && <span className="px-1.5 py-0.5 rounded text-xs" style={{ background: "#1a3a3a", color: "#fff", fontSize: 10 }}>You</span>}
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{c.visibility}%</span>
                  <span style={{ fontSize: 13, color: "#3a3a3a" }}>{c.position != null ? `#${c.position}` : "—"}</span>
                  <div className="flex items-center gap-1">
                    {c.sentiment != null ? (
                      <div className="w-16 h-1.5 rounded-full" style={{ background: "#e5e5e5" }}>
                        <div className="h-full rounded-full" style={{ width: `${c.sentiment}%`, background: c.sentiment > 70 ? "#22c55e" : c.sentiment > 50 ? "#f59e0b" : "#ef4444" }} />
                      </div>
                    ) : <span style={{ fontSize: 12, color: "#d4cfc0" }}>—</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    {c.trend >= 0 ? <TrendingUp size={12} color="#22c55e" /> : <TrendingDown size={12} color="#ef4444" />}
                    <span style={{ fontSize: 12, color: c.trend >= 0 ? "#22c55e" : "#ef4444", fontWeight: 500 }}>{c.trend >= 0 ? "+" : ""}{c.trend}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Sources */}
        <div className="lg:col-span-2 rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Top Cited Sources</h3>
          {loadingSources ? (
            <div className="space-y-3">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
          ) : !sourcesData.length ? (
            <div className="flex flex-col items-center py-10 gap-2">
              <p style={{ fontSize: 14, color: "#9a9a9a" }}>No data yet</p>
              <p style={{ fontSize: 12, color: "#b4b0a0" }}>Sources appear after runs complete</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sourcesData.map((s, i) => {
                const color = SOURCE_TYPE_COLORS[s.type] ?? "#9a9a9a";
                const label = SOURCE_TYPE_LABELS[s.type] ?? s.type;
                return (
                  <div key={s.domain} className="flex items-center gap-3">
                    <span style={{ fontSize: 12, color: "#9a9a9a", fontWeight: 500, width: 16 }}>{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }} className="truncate">{s.domain}</span>
                        <span className="px-1.5 py-0.5 rounded-full flex-shrink-0" style={{ fontSize: 10, fontWeight: 500, background: color + "20", color }}>{label}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 rounded-full" style={{ background: "#e5e5e5" }}>
                          <div className="h-full rounded-full" style={{ width: `${(s.citations / sourcesData[0].citations) * 100}%`, background: color }} />
                        </div>
                        <span style={{ fontSize: 11, color: "#6a6a6a", width: 28, textAlign: "right" }}>{s.citations}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a" }}>Recent Activity</h3>
          <button onClick={() => navigate("/runs")} className="flex items-center gap-1 hover:underline" style={{ fontSize: 13, color: "#6a6a6a" }}>
            View all runs <ExternalLink size={12} />
          </button>
        </div>

        {loadingRuns ? (
          <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !recentRuns.length ? (
          <div className="flex flex-col items-center py-10 gap-2">
            <Clock size={28} style={{ color: "#d4cfc0" }} />
            <p style={{ fontSize: 14, color: "#9a9a9a" }}>No runs yet</p>
            <p style={{ fontSize: 12, color: "#b4b0a0" }}>Add prompts and tracking configs to start collecting data</p>
          </div>
        ) : (
          <div className="space-y-0">
            {recentRuns.slice(0, 5).map((run) => {
              const tc = tcMap.get(run.tracking_config_id);
              const prompt = tc ? promptMap.get(tc.prompt_id) : undefined;
              const platform = tc ? platformMap.get(tc.platform_id) : undefined;
              const status = run.status.toLowerCase();
              const platformColor = platform ? (PLATFORM_COLORS[platform.display_name] ?? "#9a9a9a") : "#9a9a9a";
              return (
                <div key={run.id} className="flex items-center gap-4 py-3" style={{ borderBottom: "1px solid #e5e5e5" }}>
                  {statusIcon(status)}
                  <div className="flex-1 min-w-0">
                    <p style={{ fontSize: 13, color: "#0a0a0a" }} className="truncate">{prompt?.text ?? "Tracking run"}</p>
                  </div>
                  {platform && (
                    <span className="px-2 py-0.5 rounded-full flex-shrink-0" style={{ fontSize: 11, fontWeight: 600, background: platformColor + "20", color: platformColor }}>
                      {platform.display_name}
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded-full flex-shrink-0"
                    style={{ fontSize: 11, fontWeight: 600, background: statusBg[status] ?? "#f5f0e0", color: statusText[status] ?? "#6a6a6a" }}>
                    {run.status.charAt(0) + run.status.slice(1).toLowerCase()}
                  </span>
                  <span style={{ fontSize: 12, color: "#9a9a9a", flexShrink: 0 }}>{formatRelativeTime(run.created_at)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
