import { useState } from "react";
import { useNavigate } from "react-router";
import { Zap, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "../../../store/authStore";

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Unable to sign in. Please check your credentials and try again."
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
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
            style={{ background: "#1a3a3a" }}
          >
            <Zap size={22} color="#fff" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 600, color: "#0a0a0a", letterSpacing: "-0.3px" }}>
            AIScope
          </h1>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginTop: 4 }}>
            AI visibility tracking for modern brands
          </p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl p-8"
          style={{ background: "#f5f0e0", border: "1px solid #e5e5e5" }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#0a0a0a", marginBottom: 6 }}>
            Sign in
          </h2>
          <p style={{ fontSize: 14, color: "#6a6a6a", marginBottom: 24 }}>
            Welcome back. Enter your credentials below.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div
                className="rounded-xl px-4 py-2.5"
                style={{ background: "#fdecec", border: "1px solid #f5b5b5", fontSize: 13, color: "#b42318" }}
              >
                {error}
              </div>
            )}
            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alex@acmecorp.com"
                className="w-full px-4 py-2.5 rounded-xl outline-none transition-all"
                style={{
                  background: "#fffaf0",
                  border: "1px solid #e5e5e5",
                  fontSize: 14,
                  color: "#0a0a0a",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#1a3a3a")}
                onBlur={(e) => (e.target.style.borderColor = "#e5e5e5")}
              />
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a", display: "block", marginBottom: 6 }}>
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 rounded-xl outline-none transition-all pr-10"
                  style={{
                    background: "#fffaf0",
                    border: "1px solid #e5e5e5",
                    fontSize: 14,
                    color: "#0a0a0a",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#1a3a3a")}
                  onBlur={(e) => (e.target.style.borderColor = "#e5e5e5")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: "#9a9a9a" }}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => navigate("/forgot-password")}
                style={{ fontSize: 13, color: "#6a6a6a" }}
                className="hover:underline"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl transition-colors disabled:opacity-60"
              style={{ background: "#0a0a0a", color: "#fff", fontSize: 14, fontWeight: 600 }}
              onMouseEnter={(e) => ((e.target as HTMLElement).style.background = "#1f1f1f")}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.background = "#0a0a0a")}
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p style={{ fontSize: 13, color: "#6a6a6a", textAlign: "center", marginTop: 20 }}>
            Don't have an account?{" "}
            <button
              onClick={() => navigate("/signup")}
              style={{ color: "#0a0a0a", fontWeight: 500 }}
              className="hover:underline"
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
