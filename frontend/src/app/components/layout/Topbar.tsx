import { useState } from "react";
import { useLocation } from "react-router";
import { Bell, Calendar } from "lucide-react";

const DATE_RANGES = ["7d", "30d", "90d", "Custom"];

const BREADCRUMBS: Record<string, string[]> = {
  "/dashboard": ["Dashboard"],
  "/prompts": ["Prompts"],
  "/sources": ["Sources"],
  "/competitors": ["Competitors"],
  "/runs": ["Run History"],
  "/settings/project": ["Settings", "Project"],
  "/settings/brands": ["Settings", "Brands"],
  "/settings/tracking": ["Settings", "Tracking"],
  "/settings/account": ["Settings", "Account"],
  "/settings/organization": ["Settings", "Organization"],
};

export function Topbar() {
  const location = useLocation();
  const [activeRange, setActiveRange] = useState("30d");
  const crumbs = BREADCRUMBS[location.pathname] || ["Dashboard"];

  return (
    <header
      className="h-16 flex items-center px-6 flex-shrink-0"
      style={{ borderBottom: "1px solid #e5e5e5", background: "#fffaf0" }}
    >
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 flex-1">
        {crumbs.map((crumb, i) => (
          <span key={i} className="flex items-center gap-2">
            {i > 0 && <span style={{ color: "#9a9a9a", fontSize: 14 }}>/</span>}
            <span
              style={{
                fontSize: 14,
                fontWeight: i === crumbs.length - 1 ? 600 : 400,
                color: i === crumbs.length - 1 ? "#0a0a0a" : "#6a6a6a",
              }}
            >
              {crumb}
            </span>
          </span>
        ))}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Date range */}
        <div
          className="flex items-center gap-1 p-1 rounded-full"
          style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}
        >
          {DATE_RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setActiveRange(r)}
              className="px-3 py-1 rounded-full transition-all"
              style={{
                fontSize: 12,
                fontWeight: 500,
                background: activeRange === r ? "#fffaf0" : "transparent",
                color: activeRange === r ? "#0a0a0a" : "#6a6a6a",
                border: activeRange === r ? "1px solid #e5e5e5" : "1px solid transparent",
              }}
            >
              {r === "Custom" ? <Calendar size={12} /> : r}
            </button>
          ))}
        </div>

        {/* Notification bell */}
        <button
          className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-[#f5f0e0] transition-colors relative"
          style={{ color: "#6a6a6a" }}
        >
          <Bell size={16} />
          <span
            className="absolute top-1 right-1 w-2 h-2 rounded-full"
            style={{ background: "#ff4d8b" }}
          />
        </button>

        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center"
          style={{ background: "#1a3a3a", color: "#fff", fontSize: 11, fontWeight: 600 }}
        >
          AK
        </div>
      </div>
    </header>
  );
}
