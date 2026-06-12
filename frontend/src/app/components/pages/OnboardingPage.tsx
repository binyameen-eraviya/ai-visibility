import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { Check, X, ChevronRight, ChevronDown, Zap, Sparkles, Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useCreateProject, useUpdateProject } from "../../../hooks/useProjects";
import { usePlatforms, useCountries } from "../../../hooks/useTrackingConfigs";
import { useProjectStore } from "../../../store/projectStore";
import { BrandIcon, getFaviconUrl, cleanDomain } from "../../../utils/favicon";
import api from "../../../config/api";

const TOTAL_STEPS = 6;
const STEP_TITLES = [
  "Project Details",
  "Brand Profile",
  "Competitors",
  "Topics",
  "Prompts",
  "Tracking",
];

interface CompetitorSuggestion {
  name: string;
  domain: string;
  reason: string;
}
interface PromptSuggestion {
  topic: string;
  text: string;
}
interface Suggestions {
  brand_name: string;
  brand_aliases: string[];
  brand_description: string;
  industry: string;
  location: string;
  company_scale: string;
  brand_identity: string[];
  products_services: string[];
  competitors: CompetitorSuggestion[];
  suggested_topics: string[];
  suggested_prompts: PromptSuggestion[];
  favicon_url: string;
}

// A small set of languages; English is always the default (we intentionally do
// NOT auto-pick a language from location -- that produced wrong-language prompts).
const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "pt", name: "Portuguese" },
  { code: "ar", name: "Arabic" },
  { code: "hi", name: "Hindi" },
  { code: "zh", name: "Chinese" },
  { code: "ja", name: "Japanese" },
];

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
const subtitleStyle = { fontSize: 12, color: "#9a9a9a", marginBottom: 8 } as const;
const autoNote = { fontSize: 12, color: "#9a9a9a", marginTop: 6, display: "flex", alignItems: "center", gap: 4 } as const;

const platformColor = (name: string) =>
  ({ chatgpt: "#ff4d8b", perplexity: "#1a3a3a", gemini: "#b8a4ed", ai_overview: "#e8b94a", copilot: "#ff6b5a" } as Record<string, string>)[name] ?? "#1a3a3a";

// The 5 AI surfaces shown in the "running prompts" animation.
const AI_MODELS = [
  { label: "ChatGPT", color: "#ff4d8b" },
  { label: "Perplexity", color: "#1a3a3a" },
  { label: "Gemini", color: "#b8a4ed" },
  { label: "AI Overviews", color: "#e8b94a" },
  { label: "Copilot", color: "#ff6b5a" },
];

// --- small reusable bits ----------------------------------------------------

function TagChips({ values, onChange, placeholder }: { values: string[]; onChange: (v: string[]) => void; placeholder: string }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const t = draft.trim();
    if (t && !values.includes(t)) onChange([...values, t]);
    setDraft("");
  };
  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2">
        {values.map((v) => (
          <span key={v} className="flex items-center gap-1 px-2.5 py-1 rounded-full" style={{ background: "#ebe6d6", fontSize: 12, color: "#0a0a0a" }}>
            {v}
            <button onClick={() => onChange(values.filter((x) => x !== v))} style={{ color: "#6a6a6a" }}><X size={11} /></button>
          </span>
        ))}
        {values.length === 0 && <span style={{ fontSize: 12, color: "#9a9a9a" }}>None yet</span>}
      </div>
      <div className="flex gap-2">
        <input
          style={{ ...inputStyle, flex: 1, padding: "8px 12px" }}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
        />
        <button onClick={add} className="px-3 rounded-xl" style={{ background: "#ebe6d6", color: "#0a0a0a", fontSize: 13, fontWeight: 500 }}><Plus size={14} /></button>
      </div>
    </div>
  );
}

function StepHeader({ step, title, subtitle }: { step: number; title: string; subtitle: string }) {
  return (
    <div className="mb-6">
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "1.5px", color: "#9a9a9a", marginBottom: 8 }}>
        STEP {step + 1}/{TOTAL_STEPS}
      </div>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: "#0a0a0a", marginBottom: 4 }}>{title}</h2>
      <p style={{ fontSize: 14, color: "#6a6a6a" }}>{subtitle}</p>
    </div>
  );
}

// Clean white full-screen loader (used for "Generating topics..." + running runs).
function FullScreenLoader({ title, sub, withProgress }: { title: string; sub?: string; withProgress?: boolean }) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center" style={{ background: "#fffaf0" }}>
      <Sparkles size={36} color="#1a3a3a" className="animate-pulse" />
      <p style={{ fontSize: 17, fontWeight: 600, color: "#0a0a0a", marginTop: 18 }}>{title}</p>
      {sub && <p style={{ fontSize: 13, color: "#9a9a9a", marginTop: 6 }}>{sub}</p>}
      {withProgress && (
        <div style={{ width: 240, height: 6, borderRadius: 4, background: "#ebe6d6", marginTop: 20, overflow: "hidden" }}>
          <div className="onb-progress" style={{ height: "100%", background: "#1a3a3a", borderRadius: 4 }} />
        </div>
      )}
      <style>{`
        @keyframes onbFill { 0% { width: 5%; } 90% { width: 92%; } 100% { width: 96%; } }
        .onb-progress { animation: onbFill 1.6s ease-out forwards; }
        @keyframes onbSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

// Brand favicon centered with 5 AI model icons orbiting it.
function RunningAnimation({ brandName, faviconUrl, domain }: { brandName: string; faviconUrl?: string; domain?: string }) {
  const R = 96;
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center" style={{ background: "#fffaf0" }}>
      <div style={{ position: "relative", width: R * 2 + 80, height: R * 2 + 80 }}>
        <div className="onb-orbit" style={{ position: "absolute", inset: 0 }}>
          {AI_MODELS.map((m, i) => {
            const angle = (i / AI_MODELS.length) * 2 * Math.PI - Math.PI / 2;
            const x = Math.cos(angle) * R;
            const y = Math.sin(angle) * R;
            return (
              <div
                key={m.label}
                title={m.label}
                style={{
                  position: "absolute", left: "50%", top: "50%",
                  transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                  width: 44, height: 44, borderRadius: 12, background: m.color,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 4px 14px rgba(0,0,0,0.12)",
                }}
                className="animate-pulse"
              >
                <span style={{ fontSize: 15, fontWeight: 700, color: ["#1a3a3a", "#ff4d8b", "#ff6b5a"].includes(m.color) ? "#fff" : "#0a0a0a" }}>
                  {m.label.charAt(0)}
                </span>
              </div>
            );
          })}
        </div>
        {/* Center brand */}
        <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-50%)" }}>
          <BrandIcon name={brandName} faviconUrl={faviconUrl} domain={domain} size={64} radius={16} />
        </div>
      </div>
      <p style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginTop: 28 }}>Running your prompts across AI platforms...</p>
      <p style={{ fontSize: 13, color: "#9a9a9a", marginTop: 6 }}>This usually takes a few seconds.</p>
      <style>{`
        @keyframes onbOrbit { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .onb-orbit { animation: onbOrbit 8s linear infinite; }
      `}</style>
    </div>
  );
}

// --- main -------------------------------------------------------------------

export function OnboardingPage() {
  const navigate = useNavigate();
  const setActiveProjectId = useProjectStore((s) => s.setActiveProjectId);
  const createProject = useCreateProject();
  const { data: platforms = [] } = usePlatforms();
  const { data: countries = [] } = useCountries();

  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState("");

  // Step 1 — project + auto-detected context
  const [projectName, setProjectName] = useState("");
  const [website, setWebsite] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [countryId, setCountryId] = useState("");
  const [languageCode, setLanguageCode] = useState("en");
  const [timezone, setTimezone] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestions | null>(null);

  // Step 2 — brand profile
  const [brandName, setBrandName] = useState("");
  const [aliases, setAliases] = useState("");
  const [description, setDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [brandIdentity, setBrandIdentity] = useState<string[]>([]);
  const [productsServices, setProductsServices] = useState<string[]>([]);

  // Step 3 — competitors
  const [competitors, setCompetitors] = useState<CompetitorSuggestion[]>([]);
  const [newComp, setNewComp] = useState("");

  // Step 4 — topics
  const [allTopics, setAllTopics] = useState<string[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<Set<string>>(new Set());
  const [customTopic, setCustomTopic] = useState("");
  const [topicsLoading, setTopicsLoading] = useState(false);

  // Step 5 — prompts (grouped by topic)
  const [prompts, setPrompts] = useState<PromptSuggestion[]>([]);
  const [selectedPrompts, setSelectedPrompts] = useState<Set<string>>(new Set());
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const [customPromptByTopic, setCustomPromptByTopic] = useState<Record<string, string>>({});

  // Step 6 — tracking + results
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [frequency, setFrequency] = useState("daily");
  const [running, setRunning] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const brandDomain = cleanDomain(website);
  const brandFavicon = suggestions?.favicon_url || (brandDomain ? getFaviconUrl(brandDomain, 64) : "");

  // Auto-detect timezone (client-side) + country (backend best-effort) on mount.
  useEffect(() => {
    try {
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone || "");
    } catch { /* ignore */ }
    (async () => {
      try {
        const { data } = await api.get("/api/detect-location");
        if (data?.country_code) {
          const match = countries.find((c) => c.code === data.country_code);
          if (match) setCountryId(match.id);
        }
      } catch { /* best-effort */ }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countries.length]);

  // Defaults once reference data arrives.
  useEffect(() => {
    if (platforms.length && selectedPlatforms.length === 0) setSelectedPlatforms(platforms.map((p) => p.id));
  }, [platforms, selectedPlatforms.length]);
  useEffect(() => {
    if (countries.length && !countryId) setCountryId((countries.find((c) => c.code === "US") ?? countries[0]).id);
  }, [countries, countryId]);

  function applySuggestions(s: Suggestions) {
    setSuggestions(s);
    if (s.brand_name && !projectName.trim()) setProjectName(s.brand_name);
    setBrandName((cur) => cur || s.brand_name || "");
    if (s.brand_aliases?.length) setAliases(s.brand_aliases.join(", "));
    setDescription((cur) => cur || s.brand_description || "");
    setIndustry((cur) => cur || s.industry || "");
    if (s.brand_identity?.length) setBrandIdentity(s.brand_identity);
    if (s.products_services?.length) setProductsServices(s.products_services);
    if (s.competitors?.length) setCompetitors(s.competitors);
    if (s.suggested_topics?.length) {
      setAllTopics(s.suggested_topics);
      setSelectedTopics(new Set(s.suggested_topics));
    }
    if (s.suggested_prompts?.length) {
      setPrompts(s.suggested_prompts);
      setSelectedPrompts(new Set(s.suggested_prompts.map((p) => p.text)));
    }
  }

  // Analyze the website when the URL field loses focus (debounced via blur).
  async function handleUrlBlur() {
    const url = normalizeUrl(website);
    if (!url || analyzing || analyzed) return;
    setAnalyzing(true);
    try {
      const { data } = await api.post<Suggestions>("/api/analyze-website", { url }, { timeout: 30000 });
      applySuggestions(data);
      setAnalyzed(true);
    } catch {
      /* best-effort: user can fill in manually */
    } finally {
      setAnalyzing(false);
    }
  }

  // STEP 1 -> 2: create the project with detected context.
  async function continueStep0() {
    if (!projectName.trim()) return;
    setError("");
    setSubmitting(true);
    try {
      const normUrl = normalizeUrl(website);
      const project = await createProject.mutateAsync({
        name: projectName.trim(),
        website_url: normUrl || undefined,
        detected_location: countries.find((c) => c.id === countryId)?.name || undefined,
        detected_language: languageCode,
        detected_timezone: timezone || undefined,
        favicon_url: brandFavicon || undefined,
      });
      setProjectId(project.id);
      setActiveProjectId(project.id);
      setStep(1);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't create your project. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const updateProject = useUpdateProject(projectId ?? undefined);
  const brandCreated = useRef(false);

  // STEP 2 -> 3: persist brand profile on the project + create the primary brand.
  async function continueStep1() {
    setError("");
    if (!projectId) { setStep(2); return; }
    setSubmitting(true);
    try {
      await updateProject.mutateAsync({
        description: description.trim() || undefined,
        industry: industry.trim() || undefined,
        brand_identity: brandIdentity,
        products_services: productsServices,
      });
      if (brandName.trim() && !brandCreated.current) {
        await api.post(`/api/projects/${projectId}/brands`, {
          name: brandName.trim(),
          aliases: aliases.split(",").map((a) => a.trim()).filter(Boolean),
          is_primary: true,
          website_url: normalizeUrl(website) || undefined,
          favicon_url: brandFavicon || undefined,
        });
        brandCreated.current = true;
      }
      setStep(2);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't save your brand profile.");
    } finally {
      setSubmitting(false);
    }
  }

  const createdComps = useRef<Set<string>>(new Set());

  // STEP 3 -> 4: create competitor brands (with domain + favicon).
  async function continueStep2() {
    setError("");
    if (!projectId) { goToTopics(); return; }
    setSubmitting(true);
    try {
      for (const c of competitors) {
        const key = c.name.trim().toLowerCase();
        if (!key || createdComps.current.has(key)) continue;
        await api.post(`/api/projects/${projectId}/brands`, {
          name: c.name.trim(),
          aliases: [],
          is_primary: false,
          website_url: c.domain ? `https://${c.domain}` : undefined,
          favicon_url: c.domain ? getFaviconUrl(c.domain, 64) : undefined,
        });
        createdComps.current.add(key);
      }
      goToTopics();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't save competitors.");
    } finally {
      setSubmitting(false);
    }
  }

  function goToTopics() {
    setTopicsLoading(true);
    setStep(3);
    setTimeout(() => setTopicsLoading(false), 1200);
  }

  const topicIds = useRef<Record<string, string>>({});

  // STEP 4 -> 5: create the selected topics (best-effort) so prompts can group.
  async function continueStep3() {
    setError("");
    if (projectId) {
      for (const name of selectedTopics) {
        if (topicIds.current[name]) continue;
        try {
          const { data } = await api.post(`/api/projects/${projectId}/topics`, { name });
          topicIds.current[name] = data.id;
        } catch { /* non-fatal: prompt just won't be grouped */ }
      }
    }
    // Expand the first topic that has prompts.
    const firstTopic = visibleTopics()[0] ?? null;
    setExpandedTopic(firstTopic);
    setStep(4);
  }

  // Topics that actually have selected prompts (plus any selected topics).
  function visibleTopics(): string[] {
    const fromPrompts = prompts.map((p) => p.topic || "General");
    const all = [...selectedTopics, ...fromPrompts];
    return Array.from(new Set(all.filter(Boolean)));
  }

  function promptsForTopic(topic: string): PromptSuggestion[] {
    return prompts.filter((p) => (p.topic || "General") === topic);
  }

  const togglePrompt = (text: string) =>
    setSelectedPrompts((prev) => {
      const next = new Set(prev);
      next.has(text) ? next.delete(text) : next.add(text);
      return next;
    });

  const addCustomPrompt = (topic: string) => {
    const text = (customPromptByTopic[topic] || "").trim();
    if (!text || prompts.some((p) => p.text === text)) return;
    setPrompts((prev) => [...prev, { topic, text }]);
    setSelectedPrompts((prev) => new Set(prev).add(text));
    setCustomPromptByTopic((prev) => ({ ...prev, [topic]: "" }));
  };

  const togglePlatform = (id: string) =>
    setSelectedPlatforms((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  // STEP 6: create prompts + tracking configs, fire sample runs, show results.
  async function handleStartTracking() {
    if (!projectId) { navigate("/dashboard"); return; }
    setError("");
    setSubmitting(true);
    try {
      const chosen = prompts.filter((p) => selectedPrompts.has(p.text));
      const promptIds: string[] = [];
      for (let i = 0; i < chosen.length; i++) {
        setProgress(`Creating prompts (${i + 1}/${chosen.length})...`);
        const topicId = topicIds.current[chosen[i].topic] || undefined;
        const { data } = await api.post(`/api/projects/${projectId}/prompts`, { text: chosen[i].text, topic_id: topicId });
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

      // Fire a few sample runs (prefer Gemini -- API-based, fast/reliable).
      setSubmitting(false);
      setProgress("");
      setRunning(true);
      const samplePlatform = platforms.find((p) => p.name === "gemini" && selectedPlatforms.includes(p.id))
        ?? platforms.find((p) => selectedPlatforms.includes(p.id));
      if (samplePlatform) {
        for (const promptId of promptIds.slice(0, 3)) {
          api.post(`/api/projects/${projectId}/prompts/${promptId}/run`, { platform_id: samplePlatform.id }).catch(() => {});
        }
      }
      await sleep(4200);
      setRunning(false);
      setShowResults(true);
    } catch (err: any) {
      setSubmitting(false);
      setProgress("");
      setError(err?.response?.data?.detail || "Something went wrong while setting up tracking.");
    }
  }

  // --- render -------------------------------------------------------------

  if (running) {
    return <RunningAnimation brandName={brandName || projectName || "Brand"} faviconUrl={brandFavicon} domain={brandDomain} />;
  }

  if (showResults) {
    const rows = [
      { name: brandName || projectName, domain: brandDomain, faviconUrl: brandFavicon, isYou: true },
      ...competitors.map((c) => ({ name: c.name, domain: c.domain, faviconUrl: c.domain ? getFaviconUrl(c.domain, 64) : undefined, isYou: false })),
    ];
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ background: "#fffaf0", fontFamily: "Inter, sans-serif" }}>
        <div className="w-full max-w-lg rounded-2xl p-8" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <div className="flex items-center gap-2 mb-6">
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>Your AI Search Analytics for</h2>
            <BrandIcon name={brandName || projectName} faviconUrl={brandFavicon} domain={brandDomain} size={26} radius={7} />
            <span style={{ fontSize: 18, fontWeight: 700, color: "#0a0a0a" }}>{brandName || projectName}</span>
          </div>
          <div className="space-y-2 mb-6">
            {rows.map((r, i) => (
              <div
                key={r.name + i}
                className="flex items-center gap-3 px-4 py-3 rounded-xl"
                style={{ background: "#fffaf0", border: r.isYou ? "2px solid #1a3a3a" : "1px solid #e5e5e5" }}
              >
                <span style={{ fontSize: 13, fontWeight: 700, color: "#9a9a9a", width: 18 }}>{i + 1}</span>
                <BrandIcon name={r.name} faviconUrl={r.faviconUrl} domain={r.domain} size={28} radius={8} />
                <span style={{ fontSize: 14, fontWeight: 600, color: "#0a0a0a", flex: 1 }} className="truncate">{r.name}</span>
                {r.isYou && <span className="px-2 py-0.5 rounded-full" style={{ fontSize: 10, fontWeight: 700, background: "#1a3a3a", color: "#fff", letterSpacing: "0.5px" }}>YOU</span>}
                <span style={{ fontSize: 13, color: "#9a9a9a" }}>pending</span>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 12, color: "#9a9a9a", marginBottom: 18, textAlign: "center" }}>
            Sample runs are processing — your real metrics will appear on the dashboard shortly.
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="w-full py-3 rounded-xl flex items-center justify-center gap-2"
            style={{ background: "#0a0a0a", color: "#fff", fontSize: 15, fontWeight: 600 }}
          >
            View Dashboard <ChevronRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  if (topicsLoading) {
    return <FullScreenLoader title="Generating topics..." sub="Grouping what buyers research about your category." withProgress />;
  }

  const primaryDisabled = submitting || analyzing || (step === 0 && (!projectName.trim() || createProject.isPending));
  const primaryLabel =
    step === 4 ? "Looks good" : step === 5 ? "Start Tracking" : submitting ? "Saving..." : "Continue";

  const onPrimary = () => {
    if (step === 0) return continueStep0();
    if (step === 1) return continueStep1();
    if (step === 2) return continueStep2();
    if (step === 3) return continueStep3();
    if (step === 4) return setStep(5);
    return handleStartTracking();
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 py-10" style={{ background: "#fffaf0", fontFamily: "Inter, sans-serif" }}>
      {/* Logo */}
      <div className="flex items-center gap-2 mb-8">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "#1a3a3a" }}>
          <Zap size={16} color="#fff" />
        </div>
        <span style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a" }}>AIScope</span>
      </div>

      {/* Card */}
      <div className="w-full max-w-md rounded-2xl p-8" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
        {/* STEP 1 — Project Details */}
        {step === 0 && (
          <div>
            <StepHeader step={0} title={STEP_TITLES[0]} subtitle="Add your website and we'll analyze it to pre-fill the rest." />
            <div className="space-y-4">
              <div>
                <label style={labelStyle}>Project name</label>
                <input style={inputStyle} value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Acme Corp AI Visibility" />
              </div>
              <div>
                <label style={labelStyle}>Website URL</label>
                <div className="flex items-center gap-2">
                  <input
                    style={{ ...inputStyle, flex: 1 }}
                    value={website}
                    onChange={(e) => { setWebsite(e.target.value); setAnalyzed(false); }}
                    onBlur={handleUrlBlur}
                    placeholder="acmecorp.com"
                  />
                  <div style={{ width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    {analyzing ? (
                      <Loader2 size={18} className="animate-spin" color="#6a6a6a" />
                    ) : brandDomain ? (
                      <BrandIcon name={brandName || projectName || "?"} faviconUrl={brandFavicon} domain={brandDomain} size={32} radius={8} />
                    ) : null}
                  </div>
                </div>
                <div style={autoNote}><Sparkles size={12} /> We'll auto-detect your brand, competitors, and prompts.</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label style={labelStyle}>Location</label>
                  <select style={inputStyle} value={countryId} onChange={(e) => setCountryId(e.target.value)}>
                    {countries.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Language</label>
                  <select style={inputStyle} value={languageCode} onChange={(e) => setLanguageCode(e.target.value)}>
                    {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label style={labelStyle}>Timezone</label>
                <input style={{ ...inputStyle, color: "#9a9a9a" }} value={timezone || "Detecting..."} readOnly />
                <div style={autoNote}><Sparkles size={12} /> Auto-detected from your browser</div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2 — Brand Profile */}
        {step === 1 && (
          <div>
            <StepHeader step={1} title={STEP_TITLES[1]} subtitle="We pulled this from your website — verify and edit." />
            <div className="flex items-center gap-3 mb-5">
              <BrandIcon name={brandName || "?"} faviconUrl={brandFavicon} domain={brandDomain} size={40} radius={12} />
              <input
                style={{ ...inputStyle, fontWeight: 600, fontSize: 16 }}
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="Brand name"
              />
            </div>
            <div className="space-y-4">
              <div>
                <label style={labelStyle}>About your brand</label>
                <div style={subtitleStyle}>Context about your brand that helps generate better prompts.</div>
                <textarea
                  style={{ ...inputStyle, minHeight: 80, resize: "vertical" }}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What your brand does and who it's for..."
                />
              </div>
              <div>
                <label style={labelStyle}>Industry</label>
                <div style={subtitleStyle}>Your brand's industry.</div>
                <input style={inputStyle} value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="e.g. FinTech" />
              </div>
              <div>
                <label style={labelStyle}>Brand identity</label>
                <div style={subtitleStyle}>Adjectives that describe your brand.</div>
                <TagChips values={brandIdentity} onChange={setBrandIdentity} placeholder="Add an adjective..." />
              </div>
              <div>
                <label style={labelStyle}>Products &amp; Services</label>
                <div style={subtitleStyle}>What your brand offers.</div>
                <TagChips values={productsServices} onChange={setProductsServices} placeholder="Add a product or service..." />
              </div>
              <div>
                <label style={labelStyle}>Aliases <span style={{ color: "#9a9a9a", fontWeight: 400 }}>(comma-separated)</span></label>
                <input style={inputStyle} value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="Acme, ACME Corp" />
              </div>
            </div>
          </div>
        )}

        {/* STEP 3 — Competitors */}
        {step === 2 && (
          <div>
            <StepHeader step={2} title={STEP_TITLES[2]} subtitle="Who you compete with in AI answers." />
            <div className="flex gap-2 mb-3">
              <input
                style={{ ...inputStyle, flex: 1 }}
                value={newComp}
                onChange={(e) => setNewComp(e.target.value)}
                placeholder="Competitor brand or domain"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && newComp.trim()) {
                    const v = newComp.trim();
                    const looksDomain = v.includes(".");
                    setCompetitors([...competitors, { name: looksDomain ? cleanDomain(v) : v, domain: looksDomain ? cleanDomain(v) : "", reason: "Added manually" }]);
                    setNewComp("");
                  }
                }}
              />
              <button
                onClick={() => { if (newComp.trim()) { const v = newComp.trim(); const d = v.includes(".") ? cleanDomain(v) : ""; setCompetitors([...competitors, { name: d || v, domain: d, reason: "Added manually" }]); setNewComp(""); } }}
                className="px-4 py-2 rounded-xl"
                style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 500, whiteSpace: "nowrap" }}
              >
                Add
              </button>
            </div>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {competitors.map((c, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl" style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }}>
                  <BrandIcon name={c.name} domain={c.domain} size={32} radius={9} />
                  <div className="flex-1 min-w-0">
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a" }} className="truncate">{c.name}</div>
                    {c.reason && <div style={{ fontSize: 11, color: "#9a9a9a" }} className="truncate">{c.reason}</div>}
                  </div>
                  <button onClick={() => setCompetitors(competitors.filter((_, j) => j !== i))} style={{ color: "#9a9a9a" }}><X size={14} /></button>
                </div>
              ))}
              {competitors.length === 0 && <p style={{ fontSize: 13, color: "#9a9a9a" }}>No competitors yet — add a few above.</p>}
            </div>
          </div>
        )}

        {/* STEP 4 — Topics */}
        {step === 3 && (
          <div>
            <StepHeader step={3} title={STEP_TITLES[3]} subtitle="Pick the themes to track. We'll group prompts under these." />
            <div className="flex items-center justify-between mb-3">
              <span style={{ fontSize: 12, color: "#9a9a9a" }}>{selectedTopics.size}/{allTopics.length} selected</span>
            </div>
            <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {allTopics.map((t) => {
                const checked = selectedTopics.has(t);
                return (
                  <button
                    key={t}
                    onClick={() => setSelectedTopics((prev) => { const n = new Set(prev); n.has(t) ? n.delete(t) : n.add(t); return n; })}
                    className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left"
                    style={{ background: checked ? "#fffaf0" : "transparent", border: `1px solid ${checked ? "#e5e5e5" : "transparent"}` }}
                  >
                    <span className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0" style={{ background: checked ? "#1a3a3a" : "#ebe6d6", color: "#fff" }}>
                      {checked && <Check size={11} />}
                    </span>
                    <span style={{ fontSize: 13, color: "#0a0a0a" }}>{t}</span>
                  </button>
                );
              })}
              {allTopics.length === 0 && <p style={{ fontSize: 13, color: "#9a9a9a" }}>No topics yet — add your own below.</p>}
            </div>
            <div className="flex gap-2 mt-3">
              <input
                style={{ ...inputStyle, flex: 1 }}
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                placeholder="+ Add custom topic"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && customTopic.trim() && !allTopics.includes(customTopic.trim())) {
                    setAllTopics([...allTopics, customTopic.trim()]);
                    setSelectedTopics((prev) => new Set(prev).add(customTopic.trim()));
                    setCustomTopic("");
                  }
                }}
              />
            </div>
          </div>
        )}

        {/* STEP 5 — Prompts (accordion by topic) */}
        {step === 4 && (
          <div>
            <StepHeader step={4} title={STEP_TITLES[4]} subtitle="Review the prompts we'll run for each topic." />
            <div className="flex items-center justify-between mb-3">
              <span style={{ fontSize: 12, color: "#9a9a9a" }}>{selectedPrompts.size}/{prompts.length} selected</span>
            </div>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {visibleTopics().map((topic) => {
                const tPrompts = promptsForTopic(topic);
                const open = expandedTopic === topic;
                const selCount = tPrompts.filter((p) => selectedPrompts.has(p.text)).length;
                return (
                  <div key={topic} className="rounded-xl overflow-hidden" style={{ border: "1px solid #e5e5e5", background: "#fffaf0" }}>
                    <button
                      onClick={() => setExpandedTopic(open ? null : topic)}
                      className="w-full flex items-center gap-2 px-3 py-2.5 text-left"
                    >
                      <ChevronDown size={14} color="#6a6a6a" style={{ transform: open ? "none" : "rotate(-90deg)", transition: "transform 0.15s" }} />
                      <span style={{ fontSize: 13, fontWeight: 600, color: "#0a0a0a", flex: 1 }}>{topic}</span>
                      <span style={{ fontSize: 11, color: "#9a9a9a" }}>{selCount}/{tPrompts.length}</span>
                    </button>
                    {open && (
                      <div className="px-3 pb-3 space-y-1.5">
                        {tPrompts.map((p) => {
                          const checked = selectedPrompts.has(p.text);
                          return (
                            <button
                              key={p.text}
                              onClick={() => togglePrompt(p.text)}
                              className="w-full flex items-start gap-2 px-2 py-1.5 rounded-lg text-left"
                              style={{ background: checked ? "#f5f0e0" : "transparent" }}
                            >
                              <span className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: checked ? "#1a3a3a" : "#ebe6d6", color: "#fff" }}>
                                {checked && <Check size={11} />}
                              </span>
                              <span style={{ fontSize: 13, color: "#0a0a0a" }}>{p.text}</span>
                            </button>
                          );
                        })}
                        <div className="flex gap-2 mt-1">
                          <input
                            style={{ ...inputStyle, flex: 1, padding: "7px 11px", fontSize: 13 }}
                            value={customPromptByTopic[topic] || ""}
                            onChange={(e) => setCustomPromptByTopic((prev) => ({ ...prev, [topic]: e.target.value }))}
                            placeholder="+ Add custom prompt"
                            onKeyDown={(e) => { if (e.key === "Enter") addCustomPrompt(topic); }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              {prompts.length === 0 && <p style={{ fontSize: 13, color: "#9a9a9a" }}>No prompts yet — go back to add topics, or add prompts on the dashboard.</p>}
            </div>
          </div>
        )}

        {/* STEP 6 — Tracking */}
        {step === 5 && (
          <div>
            <StepHeader step={5} title={STEP_TITLES[5]} subtitle="Choose where and how often to track, then go." />
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
                      className="px-3 py-1.5 rounded-full flex items-center gap-1.5"
                      style={{ background: active ? color : "#fffaf0", border: `1px solid ${active ? color : "#e5e5e5"}`, color: active ? (["#1a3a3a", "#ff4d8b", "#ff6b5a"].includes(color) ? "#fff" : "#0a0a0a") : "#3a3a3a", fontSize: 13, fontWeight: 500 }}
                    >
                      {active && <Check size={12} />}
                      {p.display_name}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="mb-5">
              <label style={labelStyle}>Country</label>
              <select style={inputStyle} value={countryId} onChange={(e) => setCountryId(e.target.value)}>
                {countries.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Frequency</label>
              <div className="flex gap-2">
                {["daily", "weekly"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setFrequency(f)}
                    className="flex-1 py-2 rounded-xl capitalize"
                    style={{ fontSize: 14, fontWeight: 500, background: frequency === f ? "#1a3a3a" : "#fffaf0", color: frequency === f ? "#fff" : "#3a3a3a", border: `1px solid ${frequency === f ? "#1a3a3a" : "#e5e5e5"}` }}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Error / progress */}
        {error && (
          <div className="rounded-xl px-4 py-2.5 mt-4" style={{ background: "#fdecec", border: "1px solid #f5b5b5", fontSize: 13, color: "#b42318" }}>{error}</div>
        )}
        {submitting && progress && (
          <div className="rounded-xl px-4 py-2.5 mt-4" style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 13, color: "#6a6a6a" }}>{progress}</div>
        )}

        {/* Footer */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              disabled={submitting}
              className="flex-1 py-2.5 rounded-xl disabled:opacity-60"
              style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}
            >
              Back
            </button>
          )}
          <button
            onClick={onPrimary}
            disabled={primaryDisabled}
            className="flex-1 py-2.5 rounded-xl flex items-center justify-center gap-2 disabled:opacity-60"
            style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
          >
            {step < 5 ? <>{primaryLabel} <ChevronRight size={16} /></> : submitting ? "Setting up..." : "Start Tracking"}
          </button>
        </div>
      </div>
    </div>
  );
}
