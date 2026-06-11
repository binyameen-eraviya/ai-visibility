import { useState } from "react";
import { useNavigate } from "react-router";
import { Check, X, ChevronRight, Zap } from "lucide-react";

const PLATFORMS = [
  { id: "chatgpt", label: "ChatGPT", color: "#ff4d8b" },
  { id: "perplexity", label: "Perplexity", color: "#1a3a3a" },
  { id: "gemini", label: "Gemini", color: "#b8a4ed" },
  { id: "ai-overviews", label: "AI Overviews", color: "#e8b94a" },
  { id: "copilot", label: "Copilot", color: "#ff6b5a" },
];

const STEPS = ["Create Project", "Add Your Brand", "Add Competitors", "Configure Tracking"];

export function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [projectName, setProjectName] = useState("");
  const [website, setWebsite] = useState("");
  const [brandName, setBrandName] = useState("");
  const [aliases, setAliases] = useState("");
  const [competitors, setCompetitors] = useState<string[]>(["Rival AI", "CompeteBot"]);
  const [newComp, setNewComp] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["chatgpt", "perplexity"]);

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
                style={{
                  background: i < step ? "#22c55e" : i === step ? "#1a3a3a" : "#ebe6d6",
                  color: i <= step ? "#fff" : "#6a6a6a",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {i < step ? <Check size={14} /> : i + 1}
              </div>
              <span style={{ fontSize: 11, color: i === step ? "#0a0a0a" : "#9a9a9a", marginTop: 4, fontWeight: i === step ? 500 : 400, whiteSpace: "nowrap" }}>
                {s}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{ width: 48, height: 1, background: i < step ? "#22c55e" : "#e5e5e5", margin: "0 4px", marginBottom: 16 }} />
            )}
          </div>
        ))}
      </div>

      {/* Card */}
      <div className="w-full max-w-md rounded-2xl p-8" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>

        {/* Step 0 */}
        {step === 0 && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Create your first project</h2>
            <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>What brand do you want to track across AI?</p>
            <div className="space-y-4">
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Project name</label>
                <input style={inputStyle} value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Acme Corp AI Visibility" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Website URL</label>
                <input style={inputStyle} value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://acmecorp.com" />
              </div>
            </div>
          </div>
        )}

        {/* Step 1 */}
        {step === 1 && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Add your brand</h2>
            <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>We'll look for these names in AI answers.</p>
            <div className="space-y-4">
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>Brand name</label>
                <input style={inputStyle} value={brandName} onChange={(e) => setBrandName(e.target.value)} placeholder="Acme Corp" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>
                  Aliases <span style={{ color: "#9a9a9a", fontWeight: 400 }}>(comma-separated)</span>
                </label>
                <input style={inputStyle} value={aliases} onChange={(e) => setAliases(e.target.value)} placeholder="Acme, ACME Corp, acmecorp.com" />
              </div>
            </div>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Add competitors</h2>
            <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>Who are you competing against in AI answers?</p>
            <div className="space-y-3">
              <div className="flex gap-2">
                <input
                  style={{ ...inputStyle, flex: 1 }}
                  value={newComp}
                  onChange={(e) => setNewComp(e.target.value)}
                  placeholder="Competitor brand name"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && newComp.trim()) {
                      setCompetitors([...competitors, newComp.trim()]);
                      setNewComp("");
                    }
                  }}
                />
                <button
                  onClick={() => { if (newComp.trim()) { setCompetitors([...competitors, newComp.trim()]); setNewComp(""); } }}
                  className="px-4 py-2 rounded-xl"
                  style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 500, whiteSpace: "nowrap" }}
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {competitors.map((c, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
                    style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 13 }}
                  >
                    <span style={{ color: "#0a0a0a" }}>{c}</span>
                    <button onClick={() => setCompetitors(competitors.filter((_, j) => j !== i))} style={{ color: "#9a9a9a" }}>
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 3 */}
        {step === 3 && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Configure tracking</h2>
            <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>Choose where to monitor your AI visibility.</p>
            <div className="space-y-5">
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 8 }}>Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {PLATFORMS.map((p) => {
                    const active = selectedPlatforms.includes(p.id);
                    return (
                      <button
                        key={p.id}
                        onClick={() => setSelectedPlatforms(active ? selectedPlatforms.filter((x) => x !== p.id) : [...selectedPlatforms, p.id])}
                        className="px-3 py-1.5 rounded-full flex items-center gap-1.5 transition-all"
                        style={{
                          background: active ? p.color : "#fffaf0",
                          border: `1px solid ${active ? p.color : "#e5e5e5"}`,
                          color: active ? (["#1a3a3a", "#ff4d8b", "#ff6b5a"].includes(p.color) ? "#fff" : "#0a0a0a") : "#3a3a3a",
                          fontSize: 13,
                          fontWeight: 500,
                        }}
                      >
                        {active && <Check size={12} />}
                        {p.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 8 }}>Country</label>
                <select
                  style={{ ...inputStyle }}
                  defaultValue="US"
                >
                  <option value="US">🇺🇸 United States</option>
                  <option value="GB">🇬🇧 United Kingdom</option>
                  <option value="CA">🇨🇦 Canada</option>
                  <option value="AU">🇦🇺 Australia</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 8 }}>Frequency</label>
                <div className="flex gap-2">
                  {["Daily", "Weekly"].map((f) => (
                    <button
                      key={f}
                      className="flex-1 py-2 rounded-xl transition-all"
                      style={{
                        fontSize: 14,
                        fontWeight: 500,
                        background: f === "Daily" ? "#1a3a3a" : "#fffaf0",
                        color: f === "Daily" ? "#fff" : "#3a3a3a",
                        border: `1px solid ${f === "Daily" ? "#1a3a3a" : "#e5e5e5"}`,
                      }}
                    >
                      {f} {f === "Daily" && <span style={{ fontSize: 11, opacity: 0.7 }}>recommended</span>}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer buttons */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="flex-1 py-2.5 rounded-xl transition-colors"
              style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 14, fontWeight: 500, color: "#0a0a0a" }}
            >
              Back
            </button>
          )}
          <button
            onClick={() => step < 3 ? setStep(step + 1) : navigate("/dashboard")}
            className="flex-1 py-2.5 rounded-xl flex items-center justify-center gap-2 transition-colors"
            style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "#1f1f1f")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "#0a0a0a")}
          >
            {step < 3 ? (
              <>Continue <ChevronRight size={16} /></>
            ) : (
              "Start Tracking"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
