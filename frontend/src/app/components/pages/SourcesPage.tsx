import { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { ExternalLink } from "lucide-react";

const SOURCE_TYPES = [
  { name: "Review Sites", value: 42, color: "#ff4d8b" },
  { name: "Reddit", value: 22, color: "#ff6b5a" },
  { name: "Editorial", value: 18, color: "#1a3a3a" },
  { name: "Corporate", value: 12, color: "#b8a4ed" },
  { name: "UGC / Other", value: 6, color: "#e8b94a" },
];

const SOURCES = [
  { domain: "g2.com", citations: 142, type: "Review Sites", typeColor: "#ff4d8b", trend: 12, platforms: ["ChatGPT", "Perplexity", "Gemini"] },
  { domain: "reddit.com", citations: 118, type: "Reddit", typeColor: "#ff6b5a", trend: -4, platforms: ["ChatGPT", "Perplexity", "Copilot"] },
  { domain: "trustpilot.com", citations: 94, type: "Review Sites", typeColor: "#ff4d8b", trend: 8, platforms: ["Perplexity", "Gemini", "AI Overviews"] },
  { domain: "techcrunch.com", citations: 76, type: "Editorial", typeColor: "#1a3a3a", trend: 2, platforms: ["ChatGPT", "Gemini"] },
  { domain: "capterra.com", citations: 63, type: "Review Sites", typeColor: "#ff4d8b", trend: 15, platforms: ["Perplexity", "AI Overviews", "Copilot"] },
  { domain: "producthunt.com", citations: 55, type: "UGC / Other", typeColor: "#e8b94a", trend: 6, platforms: ["ChatGPT", "Perplexity"] },
  { domain: "hackernews.com", citations: 48, type: "UGC / Other", typeColor: "#e8b94a", trend: -2, platforms: ["ChatGPT"] },
  { domain: "venturebeat.com", citations: 41, type: "Editorial", typeColor: "#1a3a3a", trend: 4, platforms: ["Perplexity", "Gemini"] },
  { domain: "softwareadvice.com", citations: 35, type: "Review Sites", typeColor: "#ff4d8b", trend: 9, platforms: ["AI Overviews", "Copilot"] },
  { domain: "acmecorp.com", citations: 28, type: "Corporate", typeColor: "#b8a4ed", trend: 21, platforms: ["ChatGPT", "Perplexity", "Gemini", "AI Overviews", "Copilot"] },
];

const PLATFORM_COLORS: Record<string, string> = {
  ChatGPT: "#ff4d8b",
  Perplexity: "#1a3a3a",
  Gemini: "#b8a4ed",
  "AI Overviews": "#e8b94a",
  Copilot: "#ff6b5a",
};

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl px-3 py-2" style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 12 }}>
      <strong style={{ color: payload[0].name }}>{payload[0].name}</strong>: {payload[0].value}%
    </div>
  );
};

export function SourcesPage() {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState("All Types");

  const types = ["All Types", ...SOURCE_TYPES.map((t) => t.name)];
  const filtered = SOURCES.filter((s) => typeFilter === "All Types" || s.type === typeFilter);

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div className="mb-6">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Sources</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>See which websites AI trusts in your niche</p>
      </div>

      {/* Top section: donut + callout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
        <div className="lg:col-span-3 rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Citation Distribution by Source Type</h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width={200} height={180}>
              <PieChart>
                <Pie
                  data={SOURCE_TYPES}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {SOURCE_TYPES.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 flex-1">
              {SOURCE_TYPES.map((t) => (
                <div key={t.name} className="flex items-center gap-3">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: t.color }} />
                  <span style={{ fontSize: 13, color: "#0a0a0a", flex: 1 }}>{t.name}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a" }}>{t.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 rounded-2xl p-6 flex flex-col justify-center" style={{ background: "#1a3a3a" }}>
          <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase", color: "rgba(255,255,255,0.6)", marginBottom: 8 }}>
            #1 Most Cited
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#fff", letterSpacing: "-0.5px", marginBottom: 4 }}>
            g2.com
          </div>
          <div style={{ fontSize: 14, color: "rgba(255,255,255,0.7)", marginBottom: 16 }}>
            142 citations across all AI platforms
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 11, background: "#ff4d8b20", color: "#ff4d8b" }}>Review Sites</span>
            <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>+12 this month</span>
          </div>
          <div className="mt-4" style={{ fontSize: 13, color: "rgba(255,255,255,0.6)" }}>
            Tip: Publishing on G2 increases your chance of being cited in AI answers.
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-xl outline-none"
          style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 13, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
        >
          {types.map((t) => <option key={t}>{t}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div
          className="grid px-4 py-3"
          style={{ gridTemplateColumns: "1fr 120px 120px 80px 160px", borderBottom: "1px solid #e5e5e5" }}
        >
          {["Domain", "Citations", "Source Type", "Trend", "Platforms"].map((h) => (
            <span key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
          ))}
        </div>

        {filtered.map((s, i) => (
          <div key={s.domain}>
            <div
              className="grid px-4 py-3 items-center cursor-pointer hover:bg-[#ebe6d6] transition-colors"
              style={{ gridTemplateColumns: "1fr 120px 120px 80px 160px", borderBottom: "1px solid #e5e5e5" }}
              onClick={() => setExpanded(expanded === s.domain ? null : s.domain)}
            >
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 12, color: "#9a9a9a", width: 20 }}>{i + 1}</span>
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold"
                  style={{ background: "#ebe6d6", color: "#3a3a3a" }}
                >
                  {s.domain.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{s.domain}</div>
                  <a href="#" style={{ fontSize: 11, color: "#9a9a9a" }} className="flex items-center gap-0.5">
                    <ExternalLink size={10} /> view
                  </a>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full" style={{ background: "#e5e5e5", maxWidth: 60 }}>
                  <div className="h-full rounded-full" style={{ width: `${(s.citations / 142) * 100}%`, background: s.typeColor }} />
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{s.citations}</span>
              </div>
              <span className="px-2 py-0.5 rounded-full w-fit" style={{ fontSize: 11, fontWeight: 500, background: s.typeColor + "20", color: s.typeColor }}>
                {s.type}
              </span>
              <span style={{ fontSize: 13, fontWeight: 500, color: s.trend > 0 ? "#22c55e" : "#ef4444" }}>
                {s.trend > 0 ? "+" : ""}{s.trend}
              </span>
              <div className="flex gap-1 flex-wrap">
                {s.platforms.map((p) => (
                  <div
                    key={p}
                    className="w-2 h-2 rounded-full"
                    style={{ background: PLATFORM_COLORS[p] }}
                    title={p}
                  />
                ))}
              </div>
            </div>

            {expanded === s.domain && (
              <div className="px-8 py-4" style={{ background: "#fffaf0", borderBottom: "1px solid #e5e5e5" }}>
                <p style={{ fontSize: 13, color: "#6a6a6a", marginBottom: 12 }}>
                  <strong style={{ color: "#0a0a0a" }}>{s.domain}</strong> has been cited {s.citations} times. This domain appears in answers on{" "}
                  {s.platforms.join(", ")}.
                </p>
                <div className="flex gap-2 flex-wrap">
                  {s.platforms.map((p) => (
                    <span key={p} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full" style={{ background: PLATFORM_COLORS[p] + "20", color: PLATFORM_COLORS[p], fontSize: 12 }}>
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: PLATFORM_COLORS[p] }} />
                      {p}
                    </span>
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
