import { useEffect, useState } from "react";
import { Plus, X, Trash2, Building2, Users } from "lucide-react";
import { toast } from "sonner";
import { useProjectStore } from "../../../store/projectStore";
import { useAuthStore } from "../../../store/authStore";
import { useProject, useUpdateProject } from "../../../hooks/useProjects";
import { useBrands, useCreateBrand, useDeleteBrand } from "../../../hooks/useBrands";
import {
  usePlatforms,
  useCountries,
  useTrackingConfigs,
  useCreateTrackingConfig,
  useToggleTrackingConfig,
} from "../../../hooks/useTrackingConfigs";
import { usePrompts } from "../../../hooks/usePrompts";
import { Skeleton } from "../ui/skeleton";

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

function SaveButton({
  onClick, disabled, label = "Save Changes",
}: { onClick?: () => void; disabled?: boolean; label?: string }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-5 py-2.5 rounded-xl transition-colors mt-4 disabled:opacity-60"
      style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "#1f1f1f")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "#0a0a0a")}
    >
      {label}
    </button>
  );
}

export function ProjectSettingsPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId) ?? undefined;
  const { data: project, isLoading } = useProject(activeProjectId);
  const updateProject = useUpdateProject(activeProjectId);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);

  // Hydrate the form once the project loads.
  useEffect(() => {
    if (project) {
      setName(project.name);
      setUrl(project.website_url ?? "");
    }
  }, [project]);

  const handleSave = async () => {
    if (!activeProjectId) return;
    try {
      await updateProject.mutateAsync({ name, website_url: url || undefined });
      toast.success("Project updated");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to update project");
    }
  };

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-2xl space-y-6">
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Project Settings</h1>
        <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Manage your project configuration</p>
      </div>

      <SectionCard title="General">
        {isLoading ? (
          <div className="space-y-3">{[0, 1].map((i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !activeProjectId ? (
          <p style={{ fontSize: 14, color: "#9a9a9a" }}>Select a project to edit its settings.</p>
        ) : (
          <div className="space-y-4">
            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Project Name</label>
              <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Website URL</label>
              <input style={inputStyle} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" />
            </div>
            <SaveButton onClick={handleSave} disabled={updateProject.isPending || !name.trim()} label={updateProject.isPending ? "Saving..." : "Save Changes"} />
          </div>
        )}
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

function AddCompetitorModal({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const [name, setName] = useState("");
  const [aliases, setAliases] = useState("");
  const createBrand = useCreateBrand(projectId);

  const handleSave = async () => {
    if (!name.trim()) return;
    try {
      await createBrand.mutateAsync({
        name: name.trim(),
        aliases: aliases.split(",").map((a) => a.trim()).filter(Boolean),
        is_primary: false,
      });
      toast.success("Competitor added");
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add competitor");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.3)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl p-6"
        style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>Add Competitor</h3>
          <button onClick={onClose} style={{ color: "#6a6a6a" }}><X size={18} /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Brand name</label>
            <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="Rival AI" />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>
              Aliases <span style={{ color: "#9a9a9a", fontWeight: 400 }}>(comma-separated)</span>
            </label>
            <input style={inputStyle} value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="RivalAI, rival-ai.com" />
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-xl" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}>
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={createBrand.isPending || !name.trim()}
              className="flex-1 py-2.5 rounded-xl disabled:opacity-60"
              style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
            >
              {createBrand.isPending ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function BrandsPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const { data: brands = [], isLoading } = useBrands(activeProjectId ?? undefined);
  const deleteBrand = useDeleteBrand(activeProjectId ?? undefined);
  const [showModal, setShowModal] = useState(false);

  const handleDelete = async (brandId: string) => {
    try {
      await deleteBrand.mutateAsync(brandId);
      toast.success("Competitor removed");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to remove competitor");
    }
  };

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-2xl space-y-6">
      {showModal && activeProjectId && (
        <AddCompetitorModal projectId={activeProjectId} onClose={() => setShowModal(false)} />
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Brands</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Manage your brand and competitors</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          disabled={!activeProjectId}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl disabled:opacity-60"
          style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
        >
          <Plus size={14} />
          Add Competitor
        </button>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-2xl" />
          ))}
        </div>
      )}

      {!isLoading && brands.length === 0 && (
        <div className="rounded-2xl p-10 flex flex-col items-center gap-3" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <Building2 size={32} style={{ color: "#d4cfc0" }} />
          <p style={{ fontSize: 14, color: "#9a9a9a" }}>No brands yet</p>
          {activeProjectId && (
            <button onClick={() => setShowModal(true)} className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#0a0a0a", color: "#fff" }}>
              Add your first brand
            </button>
          )}
        </div>
      )}

      <div className="space-y-3">
        {brands.map((brand) => (
          <div key={brand.id} className="rounded-2xl p-5" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: brand.is_primary ? "#1a3a3a" : "#ebe6d6" }}
                >
                  <span style={{ fontSize: 14, fontWeight: 700, color: brand.is_primary ? "#fff" : "#6a6a6a" }}>
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
                        background: brand.is_primary ? "#dcfce7" : "#f5f0e0",
                        color: brand.is_primary ? "#16a34a" : "#9a9a9a",
                        letterSpacing: "0.5px",
                      }}
                    >
                      {brand.is_primary ? "YOUR BRAND" : "COMPETITOR"}
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
                {!brand.is_primary && (
                  <button onClick={() => handleDelete(brand.id)} style={{ color: "#d4cfc0" }} title="Remove">
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

const PLATFORM_COLORS: Record<string, string> = {
  chatgpt: "#ff4d8b",
  perplexity: "#1a3a3a",
  gemini: "#b8a4ed",
  ai_overviews: "#e8b94a",
  copilot: "#ff6b5a",
};

function AddTrackingConfigModal({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const { data: prompts = [] } = usePrompts(projectId);
  const { data: platforms = [] } = usePlatforms();
  const { data: countries = [] } = useCountries();
  const createConfig = useCreateTrackingConfig(projectId);

  const [promptId, setPromptId] = useState("");
  const [platformId, setPlatformId] = useState("");
  const [countryId, setCountryId] = useState("");
  const [frequency, setFrequency] = useState("daily");

  const handleSave = async () => {
    if (!promptId || !platformId || !countryId) return;
    try {
      await createConfig.mutateAsync({
        prompt_id: promptId,
        platform_id: platformId,
        country_id: countryId,
        frequency,
      });
      toast.success("Tracking configuration added");
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add configuration");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.3)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl p-6"
        style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>Add Configuration</h3>
          <button onClick={onClose} style={{ color: "#6a6a6a" }}><X size={18} /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Prompt</label>
            <select value={promptId} onChange={(e) => setPromptId(e.target.value)} className="w-full px-4 py-2.5 rounded-xl outline-none" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}>
              <option value="">Select a prompt</option>
              {prompts.map((p) => <option key={p.id} value={p.id}>{p.text}</option>)}
            </select>
            {prompts.length === 0 && (
              <p style={{ fontSize: 12, color: "#9a9a9a", marginTop: 6 }}>Add a prompt first on the Prompts page.</p>
            )}
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Platform</label>
            <select value={platformId} onChange={(e) => setPlatformId(e.target.value)} className="w-full px-4 py-2.5 rounded-xl outline-none" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}>
              <option value="">Select a platform</option>
              {platforms.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Country</label>
            <select value={countryId} onChange={(e) => setCountryId(e.target.value)} className="w-full px-4 py-2.5 rounded-xl outline-none" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a", fontFamily: "Inter, sans-serif" }}>
              <option value="">Select a country</option>
              {countries.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Frequency</label>
            <div className="flex gap-2">
              {["daily", "weekly"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFrequency(f)}
                  className="flex-1 py-2 rounded-xl transition-all capitalize"
                  style={{
                    fontSize: 14,
                    fontWeight: 500,
                    background: frequency === f ? "#1a3a3a" : "#f5f0e0",
                    color: frequency === f ? "#fff" : "#3a3a3a",
                    border: `1px solid ${frequency === f ? "#1a3a3a" : "#e5e5e5"}`,
                  }}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} className="flex-1 py-2.5 rounded-xl" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}>
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={createConfig.isPending || !promptId || !platformId || !countryId}
              className="flex-1 py-2.5 rounded-xl disabled:opacity-60"
              style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
            >
              {createConfig.isPending ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function TrackingPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const { data: configs = [], isLoading } = useTrackingConfigs(activeProjectId ?? undefined);
  const { data: prompts = [] } = usePrompts(activeProjectId ?? undefined);
  const { data: platforms = [] } = usePlatforms();
  const { data: countries = [] } = useCountries();
  const toggleConfig = useToggleTrackingConfig(activeProjectId ?? undefined);
  const [showModal, setShowModal] = useState(false);

  const promptText = (id: string) => prompts.find((p) => p.id === id)?.text ?? "Unknown prompt";
  const platform = (id: string) => platforms.find((p) => p.id === id);
  const country = (id: string) => countries.find((c) => c.id === id);

  const handleToggle = async (id: string) => {
    try {
      await toggleConfig.mutateAsync(id);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to update configuration");
    }
  };

  return (
    <div style={{ fontFamily: "Inter, sans-serif" }} className="max-w-3xl space-y-6">
      {showModal && activeProjectId && (
        <AddTrackingConfigModal projectId={activeProjectId} onClose={() => setShowModal(false)} />
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>Tracking</h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 2 }}>Configure which prompts to track and where</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          disabled={!activeProjectId}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl disabled:opacity-60"
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

        {isLoading && (
          <div className="p-4 space-y-3">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        )}

        {!isLoading && configs.length === 0 && (
          <div className="flex flex-col items-center py-16 gap-3">
            <p style={{ fontSize: 14, color: "#9a9a9a" }}>No tracking configurations yet</p>
            {activeProjectId && (
              <button onClick={() => setShowModal(true)} className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#0a0a0a", color: "#fff" }}>
                Add your first configuration
              </button>
            )}
          </div>
        )}

        {configs.map((c) => {
          const p = platform(c.platform_id);
          const ctry = country(c.country_id);
          const colorKey = p?.name ?? "";
          return (
            <div key={c.id} className="grid px-4 py-3 items-center" style={{ gridTemplateColumns: "1fr 110px 80px 80px 80px", borderBottom: "1px solid #e5e5e5" }}>
              <span style={{ fontSize: 13, color: "#0a0a0a" }} className="line-clamp-1 pr-4">{promptText(c.prompt_id)}</span>
              <span
                className="px-2 py-0.5 rounded-full w-fit"
                style={{ fontSize: 11, fontWeight: 600, background: (PLATFORM_COLORS[colorKey] || "#9a9a9a") + "20", color: PLATFORM_COLORS[colorKey] || "#9a9a9a" }}
              >
                {p?.display_name ?? "—"}
              </span>
              <span style={{ fontSize: 13, color: "#3a3a3a" }}>{ctry?.code ?? "—"}</span>
              <span
                className="px-2 py-0.5 rounded-full w-fit capitalize"
                style={{ fontSize: 11, fontWeight: 600, background: c.frequency === "daily" ? "#dcfce7" : "#f5f0e0", color: c.frequency === "daily" ? "#16a34a" : "#9a9a9a" }}
              >
                {c.frequency}
              </span>
              <button
                onClick={() => handleToggle(c.id)}
                disabled={toggleConfig.isPending}
                className="w-10 h-6 rounded-full transition-all relative disabled:opacity-60"
                style={{ background: c.is_active ? "#1a3a3a" : "#d4cfc0" }}
              >
                <span
                  className="w-4 h-4 rounded-full absolute top-1 transition-all"
                  style={{ background: "#fff", left: c.is_active ? 20 : 4 }}
                />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function AccountSettingsPage() {
  const user = useAuthStore((s) => s.user);
  const initials =
    (user?.name ?? "")
      .split(" ")
      .map((p) => p.charAt(0))
      .join("")
      .slice(0, 2)
      .toUpperCase() || "?";

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
              {initials}
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: "#0a0a0a" }}>{user?.name ?? "—"}</div>
              <div style={{ fontSize: 13, color: "#6a6a6a", textTransform: "capitalize" }}>{user?.role?.toLowerCase() ?? ""}</div>
            </div>
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Full Name</label>
            <input style={{ ...inputStyle, color: "#9a9a9a" }} value={user?.name ?? ""} readOnly />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Email</label>
            <input style={{ ...inputStyle, color: "#9a9a9a" }} value={user?.email ?? ""} readOnly />
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Change Password">
        <p style={{ fontSize: 14, color: "#9a9a9a" }}>Password change coming soon.</p>
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
