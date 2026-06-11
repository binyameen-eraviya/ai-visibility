import { useState } from "react";
import { Plus, X, Trash2 } from "lucide-react";

const inputStyle = {
  width: "100%",
  padding: "10px 14px",
  borderRadius: 12,
  border: "1px solid #e5e5e5",
  background: "#fffaf0",
  fontSize: 14,
  color: "#0a0a0a",
  outline: "none",
  fontFamily: "Inter, sans-serif",
};

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl p-6" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 20 }}>{title}</h3>
      {children}
    </div>
  );
}

function SaveButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-5 py-2.5 rounded-xl transition-colors mt-4"
      style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "#1f1f1f")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "#0a0a0a")}
    >
      Save Changes
    </button>
  );
}

export function ProjectSettingsPage() {
  const [name, setName] = useState("Acme Corp AI Visibility");
  const [url, setUrl] = useState("https://acmecorp.com");
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-2xl space-y-6">
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Project Settings</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Manage your project configuration</p>
      </div>

      <SectionCard title="General">
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Project Name</label>
            <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Website URL</label>
            <input style={inputStyle} value={url} onChange={(e) => setUrl(e.target.value)} />
          </div>
          <SaveButton />
        </div>
      </SectionCard>

      <SectionCard title="Danger Zone">
        <p style={{ fontSize: 13, color: "#6a6a6a", marginBottom: 16 }}>
          Permanently delete this project and all associated data. This action cannot be undone.
        </p>
        {!showConfirm ? (
          <button
            onClick={() => setShowConfirm(true)}
            className="px-4 py-2.5 rounded-xl"
            style={{ background: "#fee2e2", color: "#dc2626", fontSize: 14, fontWeight: 600, border: "1px solid #fecaca" }}
          >
            Delete Project
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span style={{ fontSize: 13, color: "#dc2626" }}>Are you sure? This cannot be undone.</span>
            <button className="px-3 py-2 rounded-lg" style={{ background: "#ef4444", color: "#fff", fontSize: 13, fontWeight: 600 }}>Delete</button>
            <button onClick={() => setShowConfirm(false)} className="px-3 py-2 rounded-lg" style={{ background: "#f5f0e0", fontSize: 13 }}>Cancel</button>
          </div>
        )}
      </SectionCard>
    </div>
  );
}

const BRANDS = [
  { id: 1, name: "Acme Corp", aliases: ["Acme", "ACME Corp", "acmecorp.com"], isPrimary: true, visibility: 34.2 },
  { id: 2, name: "Rival AI", aliases: ["RivalAI", "rival-ai.com"], isPrimary: false, visibility: 41.8 },
  { id: 3, name: "CompeteBot", aliases: ["Compete Bot"], isPrimary: false, visibility: 28.5 },
  { id: 4, name: "DataSense", aliases: [], isPrimary: false, visibility: 22.1 },
];

export function BrandsPage() {
  const [brands, setBrands] = useState(BRANDS);

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Brands</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Manage your brand and competitors</p>
        </div>
        <button
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl"
          style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
        >
          <Plus size={14} />
          Add Competitor
        </button>
      </div>

      <div className="space-y-3">
        {brands.map((brand) => (
          <div key={brand.id} className="rounded-2xl p-5" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: brand.isPrimary ? "#1a3a3a" : "#ebe6d6" }}
                >
                  <span style={{ fontSize: 14, fontWeight: 700, color: brand.isPrimary ? "#fff" : "#6a6a6a" }}>
                    {brand.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a" }}>{brand.name}</span>
                    <span
                      className="px-2 py-0.5 rounded-full"
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        background: brand.isPrimary ? "#dcfce7" : "#f5f0e0",
                        color: brand.isPrimary ? "#16a34a" : "#9a9a9a",
                        letterSpacing: "0.5px",
                      }}
                    >
                      {brand.isPrimary ? "YOUR BRAND" : "COMPETITOR"}
                    </span>
                  </div>
                  {brand.aliases.length > 0 && (
                    <div style={{ fontSize: 12, color: "#6a6a6a", marginTop: 2 }}>
                      Aliases: {brand.aliases.join(", ")}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a" }}>{brand.visibility}%</span>
                {!brand.isPrimary && (
                  <button style={{ color: "#d4cfc0" }} title="Remove">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const TRACKING_CONFIGS = [
  { id: 1, prompt: "Best AI analytics tool for marketing", platform: "ChatGPT", country: "🇺🇸 US", frequency: "Daily", active: true },
  { id: 2, prompt: "Best AI analytics tool for marketing", platform: "Perplexity", country: "🇺🇸 US", frequency: "Daily", active: true },
  { id: 3, prompt: "Compare AI visibility tracking platforms", platform: "Gemini", country: "🇺🇸 US", frequency: "Daily", active: true },
  { id: 4, prompt: "What is AI visibility tracking?", platform: "AI Overviews", country: "🇺🇸 US", frequency: "Weekly", active: false },
  { id: 5, prompt: "How to track brand mentions in ChatGPT", platform: "Copilot", country: "🇬🇧 GB", frequency: "Daily", active: true },
];

const PLATFORM_COLORS: Record<string, string> = {
  ChatGPT: "#ff4d8b",
  Perplexity: "#1a3a3a",
  Gemini: "#b8a4ed",
  "AI Overviews": "#e8b94a",
  Copilot: "#ff6b5a",
};

export function TrackingPage() {
  const [configs, setConfigs] = useState(TRACKING_CONFIGS);

  const toggle = (id: number) =>
    setConfigs(configs.map((c) => (c.id === id ? { ...c, active: !c.active } : c)));

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Tracking</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Configure which prompts to track and where</p>
        </div>
        <button
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl"
          style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
        >
          <Plus size={14} />
          Add Configuration
        </button>
      </div>

      <div className="rounded-2xl overflow-hidden" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        <div className="grid px-4 py-3" style={{ gridTemplateColumns: "1fr 110px 80px 80px 80px", borderBottom: "1px solid #e5e5e5" }}>
          {["Prompt", "Platform", "Country", "Frequency", "Active"].map((h) => (
            <span key={h} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
          ))}
        </div>
        {configs.map((c) => (
          <div key={c.id} className="grid px-4 py-3 items-center" style={{ gridTemplateColumns: "1fr 110px 80px 80px 80px", borderBottom: "1px solid #e5e5e5" }}>
            <span style={{ fontSize: 13, color: "#0a0a0a" }} className="line-clamp-1 pr-4">{c.prompt}</span>
            <span
              className="px-2 py-0.5 rounded-full w-fit"
              style={{ fontSize: 11, fontWeight: 600, background: (PLATFORM_COLORS[c.platform] || "#9a9a9a") + "20", color: PLATFORM_COLORS[c.platform] || "#9a9a9a" }}
            >
              {c.platform}
            </span>
            <span style={{ fontSize: 13, color: "#3a3a3a" }}>{c.country}</span>
            <span
              className="px-2 py-0.5 rounded-full w-fit"
              style={{ fontSize: 11, fontWeight: 600, background: c.frequency === "Daily" ? "#dcfce7" : "#f5f0e0", color: c.frequency === "Daily" ? "#16a34a" : "#9a9a9a" }}
            >
              {c.frequency}
            </span>
            <button
              onClick={() => toggle(c.id)}
              className="w-10 h-6 rounded-full transition-all relative"
              style={{ background: c.active ? "#1a3a3a" : "#d4cfc0" }}
            >
              <span
                className="w-4 h-4 rounded-full absolute top-1 transition-all"
                style={{ background: "#fff", left: c.active ? 20 : 4 }}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AccountSettingsPage() {
  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-2xl space-y-6">
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Account Settings</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Manage your profile and password</p>
      </div>

      <SectionCard title="Profile">
        <div className="space-y-4">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ background: "#1a3a3a", color: "#fff", fontSize: 22, fontWeight: 600 }}>
              AK
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a" }}>Alex Kim</div>
              <div style={{ fontSize: 13, color: "#6a6a6a" }}>Marketing Lead</div>
            </div>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Full Name</label>
            <input style={inputStyle} defaultValue="Alex Kim" />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Email</label>
            <input style={{ ...inputStyle, color: "#9a9a9a" }} defaultValue="alex@acmecorp.com" readOnly />
          </div>
          <SaveButton />
        </div>
      </SectionCard>

      <SectionCard title="Change Password">
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Current Password</label>
            <input style={inputStyle} type="password" placeholder="••••••••" />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>New Password</label>
            <input style={inputStyle} type="password" placeholder="••••••••" />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Confirm New Password</label>
            <input style={inputStyle} type="password" placeholder="••••••••" />
          </div>
          <SaveButton />
        </div>
      </SectionCard>
    </div>
  );
}

const MEMBERS = [
  { id: 1, name: "Alex Kim", email: "alex@acmecorp.com", role: "Admin", joined: "Jan 12, 2026" },
  { id: 2, name: "Jordan Lee", email: "jordan@acmecorp.com", role: "Member", joined: "Feb 3, 2026" },
  { id: 3, name: "Sam Rivera", email: "sam@acmecorp.com", role: "Member", joined: "Mar 18, 2026" },
];

export function OrgSettingsPage() {
  const [members, setMembers] = useState(MEMBERS);

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-3xl space-y-6">
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Organization Settings</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Manage your organization and team</p>
      </div>

      <SectionCard title="Organization">
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Organization Name</label>
            <input style={inputStyle} defaultValue="Acme Corp" />
          </div>
          <SaveButton />
        </div>
      </SectionCard>

      <SectionCard title="Team Members">
        <div className="flex justify-end mb-4">
          <button
            className="flex items-center gap-2 px-4 py-2 rounded-xl"
            style={{ background: "#0a0a0a", color: "#fff", fontSize: 13, fontWeight: 600 }}
          >
            <Plus size={14} />
            Invite Member
          </button>
        </div>
        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid #e5e5e5" }}>
          <div className="grid px-4 py-3" style={{ gridTemplateColumns: "1fr 1fr 100px 100px 40px", borderBottom: "1px solid #e5e5e5" }}>
            {["Name", "Email", "Role", "Joined", ""].map((h, i) => (
              <span key={i} style={{ fontSize: 11, fontWeight: 600, color: "#9a9a9a", letterSpacing: "0.5px", textTransform: "uppercase" }}>{h}</span>
            ))}
          </div>
          {members.map((m) => (
            <div key={m.id} className="grid px-4 py-3 items-center" style={{ gridTemplateColumns: "1fr 1fr 100px 100px 40px", borderBottom: "1px solid #e5e5e5" }}>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: "#1a3a3a", color: "#fff", fontSize: 10, fontWeight: 700 }}>
                  {m.name.split(" ").map((n) => n.charAt(0)).join("")}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{m.name}</span>
              </div>
              <span style={{ fontSize: 13, color: "#6a6a6a" }}>{m.email}</span>
              <select
                defaultValue={m.role}
                className="outline-none rounded-lg px-2 py-1"
                style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 12, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}
              >
                <option>Admin</option>
                <option>Member</option>
                <option>Viewer</option>
              </select>
              <span style={{ fontSize: 12, color: "#9a9a9a" }}>{m.joined}</span>
              <button style={{ color: "#d4cfc0" }} title="Remove">
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
