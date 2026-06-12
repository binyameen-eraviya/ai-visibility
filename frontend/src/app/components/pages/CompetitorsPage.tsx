import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Users } from "lucide-react";
import { useProjectStore } from "../../../store/projectStore";
import { useBrands, type Brand } from "../../../hooks/useBrands";
import { useDailyMetrics, type DailyMetric } from "../../../hooks/useReports";
import { Skeleton } from "../ui/skeleton";
import { BrandIcon } from "../../../utils/favicon";

function aggregateByBrand(metrics: DailyMetric[], brands: Brand[]) {
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
        name: brand?.name ?? "Unknown",
        isYou: brand?.is_primary ?? false,
        faviconUrl: brand?.favicon_url ?? undefined,
        domain: brand?.website_url ?? undefined,
        visibility: Math.round((ms.reduce((s, m) => s + m.visibility_pct, 0) / ms.length) * 10) / 10,
        position: withPos.length ? Math.round((withPos.reduce((s, m) => s + (m.avg_position ?? 0), 0) / withPos.length) * 10) / 10 : null,
        sentiment: withSent.length ? Math.round(withSent.reduce((s, m) => s + (m.avg_sentiment ?? 0), 0) / withSent.length) : null,
      };
    })
    .sort((a, b) => b.visibility - a.visibility);
}

export function CompetitorsPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId) ?? undefined;
  const { data: metrics = [], isLoading } = useDailyMetrics(activeProjectId);
  const { data: brands = [] } = useBrands(activeProjectId);

  const brandStats = useMemo(() => aggregateByBrand(metrics, brands), [metrics, brands]);
  const shareData = useMemo(() => brandStats.map((b) => ({ name: b.name, value: b.visibility, isYou: b.isYou })), [brandStats]);
  const hasData = metrics.length > 0;

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div className="mb-6">
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Competitors</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>See how you stack up in AI answers</p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-56 w-full rounded-2xl" />
          <Skeleton className="h-32 w-full rounded-2xl" />
        </div>
      ) : !hasData ? (
        <div className="rounded-2xl p-16 flex flex-col items-center gap-3" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <Users size={36} style={{ color: "#d4cfc0" }} />
          <p style={{ fontSize: 15, fontWeight: 500, color: "#9a9a9a" }}>No data yet</p>
          <p style={{ fontSize: 13, color: "#b4b0a0" }}>Competitor rankings appear once tracking runs collect data</p>
        </div>
      ) : (
        <>
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
                  {shareData.map((d, i) => <Cell key={i} fill={d.isYou ? "#1a3a3a" : "#d4cfc0"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Brand comparison cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {brandStats.map((b) => (
              <div
                key={b.name}
                className="rounded-2xl p-4"
                style={{ background: b.isYou ? "#1a3a3a" : "#f5f0e0", border: b.isYou ? "none" : "1px solid #e5e5e5" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <BrandIcon
                    name={b.name}
                    faviconUrl={b.faviconUrl}
                    domain={b.domain}
                    size={28}
                    radius={8}
                    bg={b.isYou ? "rgba(255,255,255,0.15)" : "#ebe6d6"}
                    color={b.isYou ? "#fff" : "#6a6a6a"}
                  />
                  <span style={{ fontSize: 12, fontWeight: 600, color: b.isYou ? "#fff" : "#0a0a0a" }} className="truncate">{b.name}</span>
                </div>
                {b.isYou && (
                  <div className="mb-2">
                    <span className="px-1.5 py-0.5 rounded" style={{ fontSize: 9, fontWeight: 700, background: "rgba(255,255,255,0.2)", color: "#fff", letterSpacing: "1px" }}>YOU</span>
                  </div>
                )}
                <div style={{ fontSize: 26, fontWeight: 700, color: b.isYou ? "#fff" : "#0a0a0a", lineHeight: 1, marginBottom: 2 }}>{b.visibility}%</div>
                <div style={{ fontSize: 11, color: b.isYou ? "rgba(255,255,255,0.6)" : "#9a9a9a", marginBottom: 8 }}>visibility</div>
                <div className="mt-2 space-y-1">
                  <div style={{ fontSize: 11, color: b.isYou ? "rgba(255,255,255,0.5)" : "#9a9a9a" }}>
                    Pos: <strong style={{ color: b.isYou ? "rgba(255,255,255,0.8)" : "#3a3a3a" }}>{b.position != null ? `#${b.position}` : "—"}</strong>
                  </div>
                  <div style={{ fontSize: 11, color: b.isYou ? "rgba(255,255,255,0.5)" : "#9a9a9a" }}>
                    Sentiment: <strong style={{ color: b.isYou ? "rgba(255,255,255,0.8)" : "#3a3a3a" }}>{b.sentiment != null ? `${b.sentiment}/100` : "—"}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
