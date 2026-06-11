import { useState } from "react";
import { useNavigate } from "react-router";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, CheckCircle, XCircle, Clock, ExternalLink } from "lucide-react";

const PLATFORM_COLORS: Record<string, string> = {
  ChatGPT: "#ff4d8b",
  Perplexity: "#1a3a3a",
  Gemini: "#b8a4ed",
  "AI Overviews": "#e8b94a",
  Copilot: "#ff6b5a",
};

// Mock visibility over time data
const visibilityData = [
  { date: "May 12", ChatGPT: 28, Perplexity: 41, Gemini: 22, "AI Overviews": 15, Copilot: 19 },
  { date: "May 15", ChatGPT: 31, Perplexity: 38, Gemini: 25, "AI Overviews": 18, Copilot: 21 },
  { date: "May 18", ChatGPT: 29, Perplexity: 44, Gemini: 27, "AI Overviews": 16, Copilot: 24 },
  { date: "May 21", ChatGPT: 34, Perplexity: 46, Gemini: 30, "AI Overviews": 20, Copilot: 22 },
  { date: "May 24", ChatGPT: 36, Perplexity: 43, Gemini: 28, "AI Overviews": 22, Copilot: 25 },
  { date: "May 27", ChatGPT: 33, Perplexity: 48, Gemini: 32, "AI Overviews": 19, Copilot: 28 },
  { date: "May 30", ChatGPT: 38, Perplexity: 51, Gemini: 34, "AI Overviews": 24, Copilot: 29 },
  { date: "Jun 2", ChatGPT: 40, Perplexity: 49, Gemini: 36, "AI Overviews": 26, Copilot: 31 },
  { date: "Jun 5", ChatGPT: 37, Perplexity: 53, Gemini: 35, "AI Overviews": 28, Copilot: 30 },
  { date: "Jun 8", ChatGPT: 42, Perplexity: 55, Gemini: 38, "AI Overviews": 30, Copilot: 33 },
  { date: "Jun 11", ChatGPT: 44, Perplexity: 58, Gemini: 40, "AI Overviews": 32, Copilot: 35 },
];

const competitorData = [
  { brand: "Acme Corp", visibility: 34.2, position: 2.8, sentiment: 72, trend: 5.2, isYou: true },
  { brand: "Rival AI", visibility: 41.8, position: 2.1, sentiment: 68, trend: -1.4, isYou: false },
  { brand: "CompeteBot", visibility: 28.5, position: 3.5, sentiment: 61, trend: 2.1, isYou: false },
  { brand: "DataSense", visibility: 22.1, position: 4.2, sentiment: 74, trend: -0.8, isYou: false },
  { brand: "InsightFlow", visibility: 18.9, position: 5.1, sentiment: 65, trend: 1.3, isYou: false },
];

const sourcesData = [
  { domain: "g2.com", citations: 142, type: "Review Site", typeColor: "#ff4d8b" },
  { domain: "reddit.com", citations: 118, type: "Reddit", typeColor: "#ff6b5a" },
  { domain: "trustpilot.com", citations: 94, type: "Review Site", typeColor: "#ff4d8b" },
  { domain: "techcrunch.com", citations: 76, type: "Editorial", typeColor: "#1a3a3a" },
  { domain: "capterra.com", citations: 63, type: "Review Site", typeColor: "#ff4d8b" },
  { domain: "producthunt.com", citations: 55, type: "UGC", typeColor: "#b8a4ed" },
  { domain: "hackernews.com", citations: 48, type: "UGC", typeColor: "#b8a4ed" },
];

const recentRuns = [
  { id: 1, prompt: "What's the best AI analytics tool for marketing teams?", platform: "Perplexity", status: "success", time: "2 min ago" },
  { id: 2, prompt: "Compare AI visibility tracking platforms", platform: "ChatGPT", status: "success", time: "12 min ago" },
  { id: 3, prompt: "How do I track brand mentions in ChatGPT?", platform: "Gemini", status: "running", time: "25 min ago" },
  { id: 4, prompt: "Best tools for AI answer engine optimization", platform: "AI Overviews", status: "success", time: "1 hr ago" },
  { id: 5, prompt: "What is AI visibility tracking?", platform: "Copilot", status: "failed", time: "2 hrs ago" },
];

const sparkData = [3, 5, 4, 7, 6, 8, 9, 7, 10, 11, 10, 12];

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 64, h = 24;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");
  return (
    <svg width={w} height={h} style={{ display: "block" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MetricCard({
  label, value, trend, trendLabel, bg, textColor, sparkColor,
}: {
  label: string; value: string; trend: number; trendLabel: string;
  bg: string; textColor: string; sparkColor: string;
}) {
  const up = trend >= 0;
  return (
    <div className="rounded-2xl p-6 flex flex-col gap-3" style={{ background: bg }}>
      <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase", color: textColor, opacity: 0.7 }}>
        {label}
      </div>
      <div style={{ fontSize: 36, fontWeight: 600, color: textColor, lineHeight: 1, letterSpacing: "-0.5px" }}>
        {value}
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          {up ? <TrendingUp size={14} style={{ color: up ? "#22c55e" : "#ef4444" }} /> : <TrendingDown size={14} style={{ color: "#ef4444" }} />}
          <span style={{ fontSize: 12, color: up ? "#22c55e" : "#ef4444", fontWeight: 500 }}>
            {up ? "+" : ""}{trend}%
          </span>
          <span style={{ fontSize: 12, color: textColor, opacity: 0.6 }}>{trendLabel}</span>
        </div>
        <Sparkline data={sparkData} color={sparkColor} />
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
  success: "#dcfce7",
  failed: "#fee2e2",
  running: "#fef9c3",
};
const statusText: Record<string, string> = {
  success: "#16a34a",
  failed: "#dc2626",
  running: "#ca8a04",
};

export function DashboardPage() {
  const navigate = useNavigate();
  const [activePlatforms, setActivePlatforms] = useState(Object.keys(PLATFORM_COLORS));

  const togglePlatform = (p: string) =>
    setActivePlatforms((prev) =>
      prev.includes(p) ? (prev.length > 1 ? prev.filter((x) => x !== p) : prev) : [...prev, p]
    );

  return (
    <div className="space-y-6" style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Visibility"
          value="34.2%"
          trend={5.2}
          trendLabel="vs last period"
          bg="#1a3a3a"
          textColor="#ffffff"
          sparkColor="rgba(255,255,255,0.7)"
        />
        <MetricCard
          label="Avg Position"
          value="2.8"
          trend={-0.3}
          trendLabel="vs last period"
          bg="#b8a4ed"
          textColor="#0a0a0a"
          sparkColor="#7c63c4"
        />
        <MetricCard
          label="Sentiment"
          value="72/100"
          trend={3.1}
          trendLabel="vs last period"
          bg="#ffb084"
          textColor="#0a0a0a"
          sparkColor="#c05e20"
        />
        <MetricCard
          label="Share of Voice"
          value="18.5%"
          trend={1.8}
          trendLabel="vs #1 competitor"
          bg="#e8b94a"
          textColor="#0a0a0a"
          sparkColor="#8a6500"
        />
      </div>

      {/* Main visibility chart */}
      <div className="rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a" }}>AI Visibility Over Time</h3>
            <p style={{ fontSize: 13, color: "#6a6a6a", marginTop: 2 }}>% of prompts where your brand is mentioned</p>
          </div>
          {/* Platform toggle pills */}
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(PLATFORM_COLORS).map(([platform, color]) => {
              const active = activePlatforms.includes(platform);
              return (
                <button
                  key={platform}
                  onClick={() => togglePlatform(platform)}
                  className="px-2.5 py-1 rounded-full flex items-center gap-1.5 transition-all"
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
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
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={visibilityData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
            <defs>
              {Object.entries(PLATFORM_COLORS).map(([p, c]) => (
                <linearGradient key={p} id={`grad-${p}`} x1="0" y1="0" x2="0" y2="1">
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
                <Area
                  key={platform}
                  type="monotone"
                  dataKey={platform}
                  stroke={color}
                  strokeWidth={2}
                  fill={`url(#grad-${platform})`}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ) : null
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom 2-col */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Competitors */}
        <div className="lg:col-span-3 rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Top Competitors</h3>
          <div className="space-y-0">
            <div className="grid gap-2 pb-2" style={{ gridTemplateColumns: "1fr 80px 70px 70px 64px", borderBottom: "1px solid #e5e5e5" }}>
              {["Brand", "Visibility", "Position", "Sentiment", "30d"].map((h) => (
                <span key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
              ))}
            </div>
            {competitorData.map((c) => (
              <div
                key={c.brand}
                className="grid gap-2 py-3 items-center"
                style={{
                  gridTemplateColumns: "1fr 80px 70px 70px 64px",
                  borderBottom: "1px solid #e5e5e5",
                  borderLeft: c.isYou ? "3px solid #1a3a3a" : "3px solid transparent",
                  paddingLeft: c.isYou ? 8 : 0,
                }}
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                    style={{ background: c.isYou ? "#1a3a3a" : "#ebe6d6" }}
                  >
                    <span style={{ fontSize: 10, fontWeight: 700, color: c.isYou ? "#fff" : "#6a6a6a" }}>
                      {c.brand.charAt(0)}
                    </span>
                  </div>
                  <span style={{ fontSize: 13, fontWeight: c.isYou ? 600 : 400, color: "#0a0a0a" }}>{c.brand}</span>
                  {c.isYou && (
                    <span className="px-1.5 py-0.5 rounded text-xs" style={{ background: "#1a3a3a", color: "#fff", fontSize: 10 }}>You</span>
                  )}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{c.visibility}%</span>
                <span style={{ fontSize: 13, color: "#3a3a3a" }}>#{c.position}</span>
                <div className="flex items-center gap-1">
                  <div className="w-16 h-1.5 rounded-full" style={{ background: "#e5e5e5" }}>
                    <div className="h-full rounded-full" style={{ width: `${c.sentiment}%`, background: c.sentiment > 70 ? "#22c55e" : c.sentiment > 50 ? "#f59e0b" : "#ef4444" }} />
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {c.trend >= 0 ? <TrendingUp size={12} color="#22c55e" /> : <TrendingDown size={12} color="#ef4444" />}
                  <span style={{ fontSize: 12, color: c.trend >= 0 ? "#22c55e" : "#ef4444", fontWeight: 500 }}>
                    {c.trend >= 0 ? "+" : ""}{c.trend}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Sources */}
        <div className="lg:col-span-2 rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Top Cited Sources</h3>
          <div className="space-y-3">
            {sourcesData.map((s, i) => (
              <div key={s.domain} className="flex items-center gap-3">
                <span style={{ fontSize: 12, color: "#9a9a9a", fontWeight: 500, width: 16 }}>{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }} className="truncate">{s.domain}</span>
                    <span
                      className="px-1.5 py-0.5 rounded-full flex-shrink-0"
                      style={{ fontSize: 10, fontWeight: 500, background: s.typeColor + "20", color: s.typeColor }}
                    >
                      {s.type}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1 rounded-full" style={{ background: "#e5e5e5" }}>
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${(s.citations / sourcesData[0].citations) * 100}%`, background: s.typeColor }}
                      />
                    </div>
                    <span style={{ fontSize: 11, color: "#6a6a6a", width: 28, textAlign: "right" }}>{s.citations}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a" }}>Recent Activity</h3>
          <button
            onClick={() => navigate("/runs")}
            className="flex items-center gap-1 hover:underline"
            style={{ fontSize: 13, color: "#6a6a6a" }}
          >
            View all runs <ExternalLink size={12} />
          </button>
        </div>
        <div className="space-y-0">
          {recentRuns.map((run) => (
            <div
              key={run.id}
              className="flex items-center gap-4 py-3"
              style={{ borderBottom: "1px solid #e5e5e5" }}
            >
              {statusIcon(run.status)}
              <div className="flex-1 min-w-0">
                <p style={{ fontSize: 13, color: "#0a0a0a" }} className="truncate">{run.prompt}</p>
              </div>
              <span
                className="px-2 py-0.5 rounded-full flex-shrink-0"
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  background: PLATFORM_COLORS[run.platform] + "20",
                  color: PLATFORM_COLORS[run.platform],
                }}
              >
                {run.platform}
              </span>
              <span
                className="px-2 py-0.5 rounded-full flex-shrink-0"
                style={{ fontSize: 11, fontWeight: 600, background: statusBg[run.status], color: statusText[run.status] }}
              >
                {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
              </span>
              <span style={{ fontSize: 12, color: "#9a9a9a", flexShrink: 0 }}>{run.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
