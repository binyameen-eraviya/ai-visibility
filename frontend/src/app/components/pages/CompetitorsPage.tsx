import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { TrendingUp, TrendingDown, AlertCircle } from "lucide-react";

const BRANDS = [
  { name: "Acme Corp", visibility: 34.2, position: 2.8, sentiment: 72, trend: 5.2, isYou: true },
  { name: "Rival AI", visibility: 41.8, position: 2.1, sentiment: 68, trend: -1.4, isYou: false },
  { name: "CompeteBot", visibility: 28.5, position: 3.5, sentiment: 61, trend: 2.1, isYou: false },
  { name: "DataSense", visibility: 22.1, position: 4.2, sentiment: 74, trend: -0.8, isYou: false },
  { name: "InsightFlow", visibility: 18.9, position: 5.1, sentiment: 65, trend: 1.3, isYou: false },
];

const PROMPTS_MATRIX = [
  { text: "Best AI analytics tool for marketing", "Acme Corp": true, "Rival AI": true, "CompeteBot": false, "DataSense": false, "InsightFlow": false },
  { text: "Compare AI visibility tracking platforms", "Acme Corp": true, "Rival AI": true, "CompeteBot": true, "DataSense": false, "InsightFlow": false },
  { text: "How to track brand mentions in ChatGPT", "Acme Corp": false, "Rival AI": true, "CompeteBot": true, "DataSense": false, "InsightFlow": false },
  { text: "Best tools for AI answer engine optimization", "Acme Corp": true, "Rival AI": false, "CompeteBot": false, "DataSense": true, "InsightFlow": false },
  { text: "What is AI visibility tracking", "Acme Corp": true, "Rival AI": true, "CompeteBot": true, "DataSense": true, "InsightFlow": true },
  { text: "How do marketing teams measure AI presence", "Acme Corp": false, "Rival AI": true, "CompeteBot": false, "DataSense": false, "InsightFlow": true },
  { text: "AI monitoring tools for agencies", "Acme Corp": false, "Rival AI": true, "CompeteBot": true, "DataSense": false, "InsightFlow": false },
  { text: "Perplexity brand monitoring solutions", "Acme Corp": true, "Rival AI": false, "CompeteBot": false, "DataSense": true, "InsightFlow": false },
];

const gapPrompts = PROMPTS_MATRIX.filter((p) => !p["Acme Corp"] && (p["Rival AI"] || p["CompeteBot"] || p["DataSense"] || p["InsightFlow"]));

const shareData = BRANDS.map((b) => ({ name: b.name, value: b.visibility, isYou: b.isYou }));

export function CompetitorsPage() {
  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div className="mb-6">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Competitors</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>See how you stack up in AI answers</p>
      </div>

      {/* Share of Voice chart */}
      <div className="rounded-2xl p-6 mb-4" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Share of Voice — AI Visibility %</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={shareData} layout="vertical" margin={{ left: 0, right: 24, top: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#9a9a9a" }} axisLine={false} tickLine={false} unit="%" />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "#3a3a3a" }} axisLine={false} tickLine={false} width={90} />
            <Tooltip
              contentStyle={{ background: "#fffaf0", border: "1px solid #e5e5e5", borderRadius: 12, fontSize: 12 }}
              formatter={(v: any) => [`${v}%`, "Visibility"]}
            />
            <Bar dataKey="value" radius={[0, 6, 6, 0]}>
              {shareData.map((d, i) => (
                <Cell key={i} fill={d.isYou ? "#1a3a3a" : "#d4cfc0"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Brand comparison cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        {BRANDS.map((b) => (
          <div
            key={b.name}
            className="rounded-2xl p-4"
            style={{
              background: b.isYou ? "#1a3a3a" : "#f5f0e0",
              border: b.isYou ? "none" : "1px solid #e5e5e5",
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ background: b.isYou ? "rgba(255,255,255,0.15)" : "#ebe6d6" }}
              >
                <span style={{ fontSize: 11, fontWeight: 700, color: b.isYou ? "#fff" : "#6a6a6a" }}>
                  {b.name.charAt(0)}
                </span>
              </div>
              <span style={{ fontSize: 12, fontWeight: 600, color: b.isYou ? "#fff" : "#0a0a0a" }} className="truncate">
                {b.name}
              </span>
            </div>
            {b.isYou && (
              <div className="mb-2">
                <span className="px-1.5 py-0.5 rounded" style={{ fontSize: 9, fontWeight: 700, background: "rgba(255,255,255,0.2)", color: "#fff", letterSpacing: "1px" }}>
                  YOU
                </span>
              </div>
            )}
            <div style={{ fontSize: 26, fontWeight: 700, color: b.isYou ? "#fff" : "#0a0a0a", lineHeight: 1, marginBottom: 2 }}>
              {b.visibility}%
            </div>
            <div style={{ fontSize: 11, color: b.isYou ? "rgba(255,255,255,0.6)" : "#9a9a9a", marginBottom: 8 }}>visibility</div>
            <div className="flex items-center gap-1">
              {b.trend >= 0 ? <TrendingUp size={11} color={b.isYou ? "#4ade80" : "#22c55e"} /> : <TrendingDown size={11} color="#ef4444" />}
              <span style={{ fontSize: 11, color: b.trend >= 0 ? (b.isYou ? "#4ade80" : "#22c55e") : "#ef4444", fontWeight: 500 }}>
                {b.trend >= 0 ? "+" : ""}{b.trend}%
              </span>
            </div>
            <div className="mt-2 space-y-1">
              <div style={{ fontSize: 11, color: b.isYou ? "rgba(255,255,255,0.5)" : "#9a9a9a" }}>
                Pos: <strong style={{ color: b.isYou ? "rgba(255,255,255,0.8)" : "#3a3a3a" }}>#{b.position}</strong>
              </div>
              <div style={{ fontSize: 11, color: b.isYou ? "rgba(255,255,255,0.5)" : "#9a9a9a" }}>
                Sentiment: <strong style={{ color: b.isYou ? "rgba(255,255,255,0.8)" : "#3a3a3a" }}>{b.sentiment}/100</strong>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Gap Analysis callout */}
      {gapPrompts.length > 0 && (
        <div
          className="rounded-2xl p-5 mb-6 flex items-start gap-4"
          style={{ background: "#fff3f3", border: "1px solid #fecaca" }}
        >
          <AlertCircle size={20} color="#ef4444" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", marginBottom: 4 }}>
              You're missing from {gapPrompts.length} prompts where competitors appear
            </div>
            <div style={{ fontSize: 13, color: "#6a6a6a" }}>
              Rivals like Rival AI and CompeteBot are getting visibility on these queries while you're absent. Consider creating content targeting these topics.
            </div>
          </div>
        </div>
      )}

      {/* Competitor Matrix */}
      <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="px-4 py-4" style={{ borderBottom: "1px solid #e5e5e5" }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a" }}>Competitor Matrix</h3>
          <p style={{ fontSize: 13, color: "#6a6a6a", marginTop: 2 }}>Which brands appear for each prompt</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-max">
            <thead>
              <tr style={{ borderBottom: "1px solid #e5e5e5" }}>
                <th className="text-left px-4 py-3" style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase", minWidth: 240 }}>
                  Prompt
                </th>
                {BRANDS.map((b) => (
                  <th key={b.name} className="px-4 py-3 text-center" style={{ fontSize: 11, fontWeight: 600, color: b.isYou ? "#1a3a3a" : "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase", minWidth: 100 }}>
                    {b.name.split(" ")[0]}
                    {b.isYou && <div style={{ fontSize: 8, color: "#1a3a3a" }}>YOU</div>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {PROMPTS_MATRIX.map((row, i) => {
                const youMissing = !row["Acme Corp"] && Object.values(row).slice(1).some(Boolean);
                return (
                  <tr
                    key={i}
                    style={{
                      borderBottom: "1px solid #e5e5e5",
                      background: youMissing ? "#fff8f8" : "transparent",
                    }}
                  >
                    <td className="px-4 py-3" style={{ fontSize: 13, color: "#0a0a0a", maxWidth: 240 }}>
                      <span className="line-clamp-1">{row.text}</span>
                    </td>
                    {BRANDS.map((b) => {
                      const mentioned = row[b.name as keyof typeof row] as boolean;
                      return (
                        <td key={b.name} className="px-4 py-3 text-center">
                          <span
                            className="inline-flex items-center justify-center w-6 h-6 rounded-full"
                            style={{
                              background: mentioned ? (b.isYou ? "#dcfce7" : "#f5f0e0") : "#fee2e2",
                              color: mentioned ? (b.isYou ? "#16a34a" : "#6a6a6a") : "#ef4444",
                              fontSize: 12,
                              fontWeight: 700,
                            }}
                          >
                            {mentioned ? "✓" : "✗"}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
