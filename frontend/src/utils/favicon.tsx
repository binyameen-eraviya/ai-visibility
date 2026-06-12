import { useState } from "react";

/** Google's favicon service URL for a bare domain. */
export function getFaviconUrl(domain: string, size: number = 32): string {
  return `https://www.google.com/s2/favicons?domain=${cleanDomain(domain)}&sz=${size}`;
}

/** Strip scheme / www / path from a URL or domain, returning the bare host. */
export function cleanDomain(input?: string): string {
  if (!input) return "";
  let d = input.trim().toLowerCase();
  d = d.replace(/^https?:\/\//, "").split("/")[0];
  if (d.startsWith("www.")) d = d.slice(4);
  return d;
}

// Deterministic, pleasant fallback color from a brand name.
function colorForName(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
  return `hsl(${h}, 42%, 42%)`;
}

interface BrandIconProps {
  name: string;
  domain?: string;       // bare domain or full URL; favicon is built from this
  faviconUrl?: string;   // explicit favicon URL (e.g. a stored favicon_url)
  size?: number;
  radius?: number;
  bg?: string;           // fallback circle background (defaults to a name color)
  color?: string;        // fallback letter color
}

/**
 * Brand favicon with graceful fallback to a colored circle showing the brand's
 * first letter. Used across onboarding, the sidebar, competitor cards, the
 * brands page, and the dashboard for consistent brand display.
 */
export function BrandIcon({ name, domain, faviconUrl, size = 32, radius, bg, color }: BrandIconProps) {
  const [failed, setFailed] = useState(false);
  const r = radius ?? Math.round(size * 0.28);
  const src = faviconUrl || (domain ? getFaviconUrl(domain, Math.max(64, size * 2)) : "");
  const letter = (name?.trim()?.[0] ?? "?").toUpperCase();

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={name}
        width={size}
        height={size}
        onError={() => setFailed(true)}
        style={{
          width: size,
          height: size,
          borderRadius: r,
          objectFit: "cover",
          background: "#fff",
          border: "1px solid #e5e5e5",
          flexShrink: 0,
          display: "block",
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: r,
        background: bg ?? colorForName(name || "?"),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <span style={{ fontSize: Math.round(size * 0.42), fontWeight: 700, color: color ?? "#fff" }}>
        {letter}
      </span>
    </div>
  );
}
