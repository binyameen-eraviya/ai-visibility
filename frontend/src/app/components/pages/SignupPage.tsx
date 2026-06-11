import { useState } from "react";
import { useNavigate } from "react-router";
import { Zap } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";

// Defined at module scope (NOT inside SignupPage). A component defined inside
// the render function gets a new identity on every render, which makes React
// unmount/remount the <input> on each keystroke and drop focus.
function Field({
  label, type = "text", placeholder, value, onChange,
}: {
  label: string;
  type?: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 rounded-xl outline-none transition-all"
        style={{ background: "#fffaf0", border: "1px solid #e5e5e5", fontSize: 14, color: "#0a0a0a" }}
        onFocus={(e) => (e.target.style.borderColor = "#1a3a3a")}
        onBlur={(e) => (e.target.style.borderColor = "#e5e5e5")}
      />
    </div>
  );
}

export function SignupPage() {
  const navigate = useNavigate();
  const signup = useAuthStore((s) => s.signup);
  const [form, setForm] = useState({ name: "", email: "", org: "", password: "", confirm: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await signup({
        user_name: form.name,
        email: form.email,
        password: form.password,
        organization_name: form.org,
      });
      navigate("/onboarding");
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Unable to create your account. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: "#fffaf0", fontFamily: "Inter, sans-serif" }}
    >
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ background: "#1a3a3a" }}>
            <Zap size={22} color="#fff" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>AIScope</h1>
        </div>

        <div className="rounded-2xl p-8" style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>Create account</h2>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>Start tracking your AI visibility today.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div
                className="rounded-xl px-4 py-2.5"
                style={{ background: "#fdecec", border: "1px solid #f5b5b5", fontSize: 13, color: "#b42318" }}
              >
                {error}
              </div>
            )}
            <Field label="Your name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="Alex Kim" />
            <Field label="Work email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} placeholder="alex@acmecorp.com" />
            <Field label="Organization name" value={form.org} onChange={(v) => setForm({ ...form, org: v })} placeholder="Acme Corp" />
            <Field label="Password" type="password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} placeholder="••••••••" />
            <Field label="Confirm password" type="password" value={form.confirm} onChange={(v) => setForm({ ...form, confirm: v })} placeholder="••••••••" />

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl transition-colors mt-2 disabled:opacity-60"
              style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
              onMouseEnter={(e) => ((e.target as HTMLElement).style.background = "#1f1f1f")}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.background = "#0a0a0a")}
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p style={{ fontSize: 13, color: "#6a6a6a", textAlign: "center", marginTop: 20 }}>
            Already have an account?{" "}
            <button onClick={() => navigate("/login")} style={{ color: "#0a0a0a", fontWeight: 500 }} className="hover:underline">
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
