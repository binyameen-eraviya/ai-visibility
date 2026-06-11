import { useMemo, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { Link2 } from "lucide-react";
import { useProjectStore } from "../../../store/projectStore";
import { useSourceMetrics, type SourceMetric } from "../../../hooks/useReports";
import { Skeleton } from "../ui/skeleton";

const SOURCE_TYPE_COLORS: Record<string, string> = {
  REVIEW_SITE: "#ff4d8b", REDDIT: "#ff6b5a", EDITORIAL: "#1a3a3a",
  CORPORATE: "#22c55e", UGC: "#b8a4ed", REFERENCE: "#e8b94a", OTHER: "#9a9a9a",
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  REVIEW_SITE: "Review Site", REDDIT: "Reddit", EDITORIAL: "Editorial",
  CORPORATE: "Corporate", UGC: "UGC", REFERENCE: "Reference", OTHER: "Other",
};

function aggregateByDomain(metrics: SourceMetric[]) {
  const byDomain = new Map<string, { citations: number; type: string }>();
  for (const m of metrics) {
    if (!byDomain.has(m.domain)) byDomain.set(m.domain, { citations: 0, type: m.source_type });
    byDomain.get(m.domain)!.citations += m.citation_count;
  }
  return Array.from(byDomain.entries())
    .map(([domain, { citations, type }]) => ({ domain, citations, type }))
    .sort((a, b) => b.citations - a.citations);
}

function aggregateByType(metrics: SourceMetric[]) {
  const byType = new Map<string, number>();
  let total = 0;
  for (const m of metrics) {
    byType.set(m.source_type, (byType.get(m.source_type) ?? 0) + m.citation_count);
    total += m.citation_count;
  }
  return Array.from(byType.entries())
    .map(([type, count]) => ({
      type,
      name: SOURCE_TYPE_LABELS[type] ?? type,
      color: SOURCE_TYPE_COLORS[type] ?? "#9a9a9a",
      value: total ? Math.round((count / total) * 100) : 0,
    }))
    .sort((a, b) => b.value - a.value);
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl px-3 py-2" style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 12 }}>
      <strong style={{ color: payload[0].payload.color }}>{payload[0].name}</strong>: {payload[0].value}%
    </div>
  );
};

export function SourcesPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId) ?? undefined;
  const { data: metrics = [], isLoading } = useSourceMetrics(activeProjectId);
  const [typeFilter, setTypeFilter] = useState("All Types");

  const domains = useMemo(() => aggregateByDomain(metrics), [metrics]);
  const typeDist = useMemo(() => aggregateByType(metrics), [metrics]);
  const hasData = metrics.length > 0;

  const typeOptions = ["All Types", ...typeDist.map((t) => t.name)];
  const filtered = domains.filter(
    (d) => typeFilter === "All Types" || (SOURCE_TYPE_LABELS[d.type] ?? d.type) === typeFilter
  );
  const topCitations = domains[0]?.citations ?? 1;

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div className="mb-6">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Sources</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>See which websites AI trusts in your niche</p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      ) : !hasData ? (
        <div className="rounded-2xl p-16 flex flex-col items-center gap-3" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <Link2 size={36} style={{ color: "#d4cfc0" }} />
          <p style={{ fontSize: 15, fontWeight: 500, color: "#9a9a9a" }}>No data yet</p>
          <p style={{ fontSize: 13, color: "#b4b0a0" }}>Cited sources appear here once scrape runs complete</p>
        </div>
      ) : (
        <>
          {/* Top section: donut + #1 callout */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
            <div className="lg:col-span-3 rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a", marginBottom: 16 }}>Citation Distribution by Source Type</h3>
              <div className="flex items-center gap-6">
                <ResponsiveContainer width={200} height={180}>
                  <PieChart>
                    <Pie data={typeDist} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                      {typeDist.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2 flex-1">
                  {typeDist.map((t) => (
                    <div key={t.type} className="flex items-center gap-3">
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
                {domains[0].domain}
              </div>
              <div style={{ fontSize: 14, color: "rgba(255,255,255,0.7)", marginBottom: 16 }}>
                {domains[0].citations} citations across all AI platforms
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 11, background: (SOURCE_TYPE_COLORS[domains[0].type] ?? "#9a9a9a") + "33", color: "#fff" }}>
                  {SOURCE_TYPE_LABELS[domains[0].type] ?? domains[0].type}
                </span>
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
              {typeOptions.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>

          {/* Table */}
          <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
            <div className="grid px-4 py-3" style={{ gridTemplateColumns: "1fr 160px 140px", borderBottom: "1px solid #e5e5e5" }}>
              {["Domain", "Citations", "Source Type"].map((h) => (
                <span key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
              ))}
            </div>
            {filtered.map((s, i) => {
              const color = SOURCE_TYPE_COLORS[s.type] ?? "#9a9a9a";
              return (
                <div key={s.domain} className="grid px-4 py-3 items-center" style={{ gridTemplateColumns: "1fr 160px 140px", borderBottom: "1px solid #e5e5e5" }}>
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: 12, color: "#9a9a9a", width: 20 }}>{i + 1}</span>
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold" style={{ background: "#ebe6d6", color: "#3a3a3a" }}>
                      {s.domain.charAt(0).toUpperCase()}
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{s.domain}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 rounded-full" style={{ background: "#e5e5e5", width: 60 }}>
                      <div className="h-full rounded-full" style={{ width: `${(s.citations / topCitations) * 100}%`, background: color }} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{s.citations}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full w-fit" style={{ fontSize: 11, fontWeight: 500, background: color + "20", color }}>
                    {SOURCE_TYPE_LABELS[s.type] ?? s.type}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
