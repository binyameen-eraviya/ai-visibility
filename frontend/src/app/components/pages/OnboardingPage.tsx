import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { Check, X, ChevronRight, Zap, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useCreateProject } from "../../../hooks/useProjects";
import { usePlatforms, useCountries } from "../../../hooks/useTrackingConfigs";
import { useProjectStore } from "../../../store/projectStore";
import api from "../../../config/api";

const STEPS = ["Create Project", "Add Your Brand", "Add Competitors", "Configure Tracking"];

interface CompetitorSuggestion {
  name: string;
  reason: string;
}

interface Suggestions {
  brand_name: string;
  brand_aliases: string[];
  industry: string;
  competitors: CompetitorSuggestion[];
  suggested_prompts: string[];
  prompt_topics: string[];
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function normalizeUrl(raw: string): string {
  const url = raw.trim();
  if (!url) return "";
  return /^https?:\/\//i.test(url) ? url : `https://${url}`;
}

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
} as const;

const labelStyle = { fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 } as const;
const autoNote = { fontSize: 12, color: "#9a9a9a", marginTop: 6, display: "flex", alignItems: "center", gap: 4 } as const;

export function OnboardingPage() {
  const navigate = useNavigate();
  const setActiveProjectId = useProjectStore((s) => s.setActiveProjectId);
  const createProject = useCreateProject();
  const { data: platforms = [] } = usePlatforms();
  const { data: countries = [] } = useCountries();

  const [step, setStep] = useState(0);

  // Step 1 — project
  const [projectName, setProjectName] = useState("");
  const [website, setWebsite] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);

  // Analysis
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeMsg, setAnalyzeMsg] = useState("Analyzing your website...");
  const [suggestions, setSuggestions] = useState<Suggestions | null>(null);

  // Step 2 — brand
  const [brandName, setBrandName] = useState("");
  const [aliases, setAliases] = useState("");
  const brandCreated = useRef(false);

  // Step 3 — competitors
  const [competitors, setCompetitors] = useState<CompetitorSuggestion[]>([]);
  const [newComp, setNewComp] = useState("");
  const createdComps = useRef<Set<string>>(new Set());

  // Step 4 — prompts + tracking
  const [promptOptions, setPromptOptions] = useState<string[]>([]);
  const [selectedPrompts, setSelectedPrompts] = useState<Set<string>>(new Set());
  const [customPrompt, setCustomPrompt] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [countryId, setCountryId] = useState("");
  const [frequency, setFrequency] = useState("daily");

  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");

  // Default platform/country selections once reference data arrives.
  useEffect(() => {
    if (platforms.length && selectedPlatforms.length === 0) {
      setSelectedPlatforms(platforms.map((p) => p.id));
    }
  }, [platforms, selectedPlatforms.length]);
  useEffect(() => {
    if (countries.length && !countryId) {
      setCountryId((countries.find((c) => c.code === "US") ?? countries[0]).id);
    }
  }, [countries, countryId]);

  function applySuggestions(s: Suggestions) {
    setSuggestions(s);
    if (s.brand_name) setBrandName(s.brand_name);
    if (s.brand_aliases?.length) setAliases(s.brand_aliases.join(", "));
    if (s.competitors?.length) setCompetitors(s.competitors.map((c) => ({ name: c.name, reason: c.reason })));
    if (s.suggested_prompts?.length) {
      setPromptOptions(s.suggested_prompts);
      setSelectedPrompts(new Set(s.suggested_prompts));
    }
  }

  async function runAnalysis(url: string) {
    setAnalyzing(true);
    setAnalyzeMsg("Analyzing your website...");
    const slowTimer = setTimeout(() => setAnalyzeMsg("This is taking longer than usual..."), 10000);
    try {
      const { data } = await api.post<Suggestions>("/api/analyze-website", { url }, { timeout: 30000 });
      clearTimeout(slowTimer);
      applySuggestions(data);
      if (data.brand_name) {
        setAnalyzeMsg(`Found your brand: ${data.brand_name}`);
        await sleep(900);
      }
      if (data.competitors?.length) {
        setAnalyzeMsg(`Identified ${data.competitors.length} competitors`);
        await sleep(900);
      }
    } catch {
      // Analysis is best-effort — fall through to manual entry.
      clearTimeout(slowTimer);
    } finally {
      setAnalyzing(false);
      setStep(1);
    }
  }

  async function handleStep0Continue() {
    if (!projectName.trim()) return;
    setError("");
    const normUrl = normalizeUrl(website);
    setAnalyzing(!!normUrl);
    setAnalyzeMsg("Setting up your project...");
    try {
      const project = await createProject.mutateAsync({ name: projectName.trim(), website_url: normUrl || undefined });
      setProjectId(project.id);
      setActiveProjectId(project.id);
      if (normUrl) {
        await runAnalysis(normUrl);
      } else {
        setStep(1);
      }
    } catch (err: any) {
      setAnalyzing(false);
      setError(err?.response?.data?.detail || "Couldn't create your project. Please try again.");
    }
  }

  async function handleStep1Continue() {
    setError("");
    if (projectId && brandName.trim() && !brandCreated.current) {
      setSubmitting(true);
      try {
        await api.post(`/api/projects/${projectId}/brands`, {
          name: brandName.trim(),
          aliases: aliases.split(",").map((a) => a.trim()).filter(Boolean),
          is_primary: true,
        });
        brandCreated.current = true;
      } catch (err: any) {
        setSubmitting(false);
        setError(err?.response?.data?.detail || "Couldn't save your brand.");
        return;
      }
      setSubmitting(false);
    }
    setStep(2);
  }

  async function handleStep2Continue() {
    setError("");
    if (projectId) {
      setSubmitting(true);
      try {
        for (const c of competitors) {
          const key = c.name.trim().toLowerCase();
          if (!key || createdComps.current.has(key)) continue;
          await api.post(`/api/projects/${projectId}/brands`, { name: c.name.trim(), aliases: [], is_primary: false });
          createdComps.current.add(key);
        }
      } catch (err: any) {
        setSubmitting(false);
        setError(err?.response?.data?.detail || "Couldn't save competitors.");
        return;
      }
      setSubmitting(false);
    }
    setStep(3);
  }

  async function handleStartTracking() {
    if (!projectId) {
      navigate("/dashboard");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const prompts = Array.from(selectedPrompts).map((p) => p.trim()).filter(Boolean);
      const promptIds: string[] = [];
      for (let i = 0; i < prompts.length; i++) {
        setProgress(`Creating prompts (${i + 1}/${prompts.length})...`);
        const { data } = await api.post(`/api/projects/${projectId}/prompts`, { text: prompts[i] });
        promptIds.push(data.id);
      }

      if (promptIds.length && selectedPlatforms.length && countryId) {
        setProgress("Configuring platforms...");
        const configs = [];
        for (const promptId of promptIds) {
          for (const platformId of selectedPlatforms) {
            configs.push({ prompt_id: promptId, platform_id: platformId, country_id: countryId, frequency: frequency.toUpperCase() });
          }
        }
        await api.post(`/api/projects/${projectId}/tracking-configs/bulk`, { configs });
      }

      toast.success("Your AI visibility tracking is set up!");
      navigate("/dashboard");
    } catch (err: any) {
      setSubmitting(false);
      setProgress("");
      setError(err?.response?.data?.detail || "Something went wrong while setting up tracking.");
    }
  }

  const togglePrompt = (p: string) =>
    setSelectedPrompts((prev) => {
      const next = new Set(prev);
      next.has(p) ? next.delete(p) : next.add(p);
      return next;
    });

  const addCustomPrompt = () => {
    const p = customPrompt.trim();
    if (!p || promptOptions.includes(p)) return;
    setPromptOptions((prev) => [...prev, p]);
    setSelectedPrompts((prev) => new Set(prev).add(p));
    setCustomPrompt("");
  };

  const togglePlatform = (id: string) =>
    setSelectedPlatforms((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const platformColor = (name: string) =>
    ({ chatgpt: "#ff4d8b", perplexity: "#1a3a3a", gemini: "#b8a4ed", ai_overview: "#e8b94a", copilot: "#ff6b5a" } as Record<string, string>)[name] ?? "#1a3a3a";

  const primaryDisabled = submitting || analyzing || (step === 0 && (!projectName.trim() || createProject.isPending));

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ background: "#fffaf0", fontFamily: "Inter, sans-serif" }}>
      {/* Logo */}
      <div className="flex items-center gap-2 mb-10">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "#1a3a3a" }}>
          <Zap size={16} color="#fff" />
        </div>
        <span style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>AIScope</span>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-0 mb-10">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ background: i < step ? "#22c55e" : i === step ? "#1a3a3a" : "#ebe6d6", color: i <= step ? "#fff" : "#6a6a6a", fontSize: 13, fontWeight: 600 }}
              >
                {i < step ? <Check size={14} /> : i + 1}
              </div>
              <span style={{ fontSize: 11, color: i === step ? "#0a0a0a" : "#9a9a9a", marginTop: 4, fontWeight: i === step ? 500 : 400, whiteSpace: "nowrap" }}>{s}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{ width: 48, height: 1, background: i < step ? "#22c55e" : "#e5e5e5", margin: "0 4px", marginBottom: 16 }} />
            )}
          </div>
        ))}
      </div>

      {/* Card */}
      <div className="w-full max-w-md rounded-2xl p-8" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        {analyzing ? (
          <div className="flex flex-col items-center justify-center text-center" style={{ minHeight: 200, gap: 14 }}>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: "#1a3a3a" }} />
              <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: "#1a3a3a", animationDelay: "150ms" }} />
              <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ background: "#1a3a3a", animationDelay: "300ms" }} />
            </div>
            <p style={{ fontSize: 15, fontWeight: 500, color: "#0a0a0a" }}>{analyzeMsg}</p>
            <p style={{ fontSize: 13, color: "#9a9a9a" }}>We're pre-filling your setup with smart defaults.</p>
          </div>
        ) : (
          <>
            {/* Step 0 — Create Project */}
            {step === 0 && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Create your first project</h2>
                <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>Add your website and we'll analyze it to pre-fill the rest.</p>
                <div className="space-y-4">
                  <div>
                    <label style={labelStyle}>Project name</label>
                    <input style={inputStyle} value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Acme Corp AI Visibility" />
                  </div>
                  <div>
                    <label style={labelStyle}>Website URL</label>
                    <input style={inputStyle} value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="acmecorp.com" />
                    <div style={autoNote}><Sparkles size={12} /> We'll auto-detect your brand, competitors, and prompts.</div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 1 — Brand */}
            {step === 1 && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Add your brand</h2>
                <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>We'll look for these names in AI answers.</p>
                <div className="space-y-4">
                  <div>
                    <label style={labelStyle}>Brand name</label>
                    <input style={inputStyle} value={brandName} onChange={(e) => setBrandName(e.target.value)} placeholder="Acme Corp" />
                    {suggestions?.brand_name && <div style={autoNote}><Sparkles size={12} /> Auto-detected from your website</div>}
                  </div>
                  <div>
                    <label style={labelStyle}>Aliases <span style={{ color: "#9a9a9a", fontWeight: 400 }}>(comma-separated)</span></label>
                    <input style={inputStyle} value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="Acme, ACME Corp, acmecorp.com" />
                  </div>
                </div>
              </div>
            )}

            {/* Step 2 — Competitors */}
            {step === 2 && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Add competitors</h2>
                <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: suggestions?.competitors?.length ? 8 : 24 }}>Who are you competing against in AI answers?</p>
                {suggestions?.competitors?.length ? (
                  <div style={autoNote} className="mb-4"><Sparkles size={12} /> Suggested based on your industry{suggestions.industry ? `: ${suggestions.industry}` : ""}</div>
                ) : null}
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      style={{ ...inputStyle, flex: 1 }}
                      value={newComp}
                      onChange={(e) => setNewComp(e.target.value)}
                      placeholder="Competitor brand name"
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && newComp.trim()) {
                          setCompetitors([...competitors, { name: newComp.trim(), reason: "Added manually" }]);
                          setNewComp("");
                        }
                      }}
                    />
                    <button
                      onClick={() => { if (newComp.trim()) { setCompetitors([...competitors, { name: newComp.trim(), reason: "Added manually" }]); setNewComp(""); } }}
                      className="px-4 py-2 rounded-xl"
                      style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 500, whiteSpace: "nowrap" }}
                    >
                      Add
                    </button>
                  </div>
                  <div className="space-y-2 mt-2">
                    {competitors.map((c, i) => (
                      <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }} title={c.reason}>
                        <div className="flex-1 min-w-0">
                          <div style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }}>{c.name}</div>
                          {c.reason && <div style={{ fontSize: 11, color: "#9a9a9a" }} className="truncate">{c.reason}</div>}
                        </div>
                        <button onClick={() => setCompetitors(competitors.filter((_, j) => j !== i))} style={{ color: "#9a9a9a" }}><X size={14} /></button>
                      </div>
                    ))}
                    {competitors.length === 0 && <p style={{ fontSize: 13, color: "#9a9a9a" }}>No competitors yet — add a few above.</p>}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3 — Configure Tracking */}
            {step === 3 && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Configure tracking</h2>
                <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 20 }}>Choose the prompts and platforms to monitor.</p>

                {/* Suggested prompts */}
                <div className="mb-5">
                  <label style={labelStyle}>Suggested prompts</label>
                  {suggestions?.prompt_topics?.length ? (
                    <div style={{ ...autoNote, marginTop: 0, marginBottom: 8 }}><Sparkles size={12} /> Topics: {suggestions.prompt_topics.join(", ")}</div>
                  ) : null}
                  <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                    {promptOptions.length === 0 && <p style={{ fontSize: 13, color: "#9a9a9a" }}>No suggestions — add your own prompts below.</p>}
                    {promptOptions.map((p) => {
                      const checked = selectedPrompts.has(p);
                      return (
                        <button
                          key={p}
                          onClick={() => togglePrompt(p)}
                          className="w-full flex items-start gap-2 px-3 py-2 rounded-lg text-left transition-colors"
                          style={{ background: checked ? "#fffaf0" : "transparent", border: `1px solid ${checked ? "#e5e5e5" : "transparent"}` }}
                        >
                          <span
                            className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 mt-0.5"
                            style={{ background: checked ? "#1a3a3a" : "#ebe6d6", color: "#fff" }}
                          >
                            {checked && <Check size={11} />}
                          </span>
                          <span style={{ fontSize: 13, color: "#0a0a0a" }}>{p}</span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex gap-2 mt-2">
                    <input
                      style={{ ...inputStyle, flex: 1 }}
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      placeholder="Add your own prompt..."
                      onKeyDown={(e) => { if (e.key === "Enter") addCustomPrompt(); }}
                    />
                    <button onClick={addCustomPrompt} className="px-4 py-2 rounded-xl" style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 500 }}>Add</button>
                  </div>
                  <p style={{ fontSize: 12, color: "#9a9a9a", marginTop: 6 }}>{selectedPrompts.size} selected</p>
                </div>

                {/* Platforms */}
                <div className="mb-5">
                  <label style={labelStyle}>Platforms</label>
                  <div className="flex flex-wrap gap-2">
                    {platforms.map((p) => {
                      const active = selectedPlatforms.includes(p.id);
                      const color = platformColor(p.name);
                      return (
                        <button
                          key={p.id}
                          onClick={() => togglePlatform(p.id)}
                          className="px-3 py-1.5 rounded-full flex items-center gap-1.5 transition-all"
                          style={{ background: active ? color : "#fffaf0", border: `1px solid ${active ? color : "#e5e5e5"}`, color: active ? (["#1a3a3a", "#ff4d8b", "#ff6b5a"].includes(color) ? "#fff" : "#0a0a0a") : "#3a3a3a", fontSize: 13, fontWeight: 500 }}
                        >
                          {active && <Check size={12} />}
                          {p.display_name}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Country */}
                <div className="mb-5">
                  <label style={labelStyle}>Country</label>
                  <select style={inputStyle} value={countryId} onChange={(e) => setCountryId(e.target.value)}>
                    {countries.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>

                {/* Frequency */}
                <div>
                  <label style={labelStyle}>Frequency</label>
                  <div className="flex gap-2">
                    {["daily", "weekly"].map((f) => (
                      <button
                        key={f}
                        onClick={() => setFrequency(f)}
                        className="flex-1 py-2 rounded-xl transition-all capitalize"
                        style={{ fontSize: 14, fontWeight: 500, background: frequency === f ? "#1a3a3a" : "#fffaf0", color: frequency === f ? "#fff" : "#3a3a3a", border: `1px solid ${frequency === f ? "#1a3a3a" : "#e5e5e5"}` }}
                      >
                        {f} {f === "daily" && <span style={{ fontSize: 11, opacity: 0.7 }}>recommended</span>}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="rounded-xl px-4 py-2.5 mt-4" style={{ background: "#fdecec", border: "1px solid #f5b5b5", fontSize: 13, color: "#b42318" }}>{error}</div>
            )}

            {/* Progress */}
            {submitting && progress && (
              <div className="rounded-xl px-4 py-2.5 mt-4" style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 13, color: "#6a6a6a" }}>{progress}</div>
            )}

            {/* Footer buttons */}
            <div className="flex gap-3 mt-8">
              {step > 0 && (
                <button
                  onClick={() => setStep(step - 1)}
                  disabled={submitting}
                  className="flex-1 py-2.5 rounded-xl transition-colors disabled:opacity-60"
                  style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}
                >
                  Back
                </button>
              )}
              <button
                onClick={() => {
                  if (step === 0) return handleStep0Continue();
                  if (step === 1) return handleStep1Continue();
                  if (step === 2) return handleStep2Continue();
                  return handleStartTracking();
                }}
                disabled={primaryDisabled}
                className="flex-1 py-2.5 rounded-xl flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
                style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
              >
                {step < 3 ? (
                  <>{submitting ? "Saving..." : "Continue"} <ChevronRight size={16} /></>
                ) : submitting ? (
                  "Setting up..."
                ) : (
                  "Start Tracking"
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
