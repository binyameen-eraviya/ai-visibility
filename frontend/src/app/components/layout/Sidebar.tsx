import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import {
  LayoutDashboard,
  MessageSquare,
  Link,
  Users,
  History,
  Settings,
  ChevronDown,
  LogOut,
  PanelLeftClose,
  PanelLeft,
  Plus,
  Zap,
} from "lucide-react";
import { useProjects } from "../../../hooks/useProjects";
import { useProjectStore } from "../../../store/projectStore";
import { useAuthStore } from "../../../store/authStore";
import { BrandIcon } from "../../../utils/favicon";

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: MessageSquare, label: "Prompts", path: "/prompts" },
  { icon: Link, label: "Sources", path: "/sources" },
  { icon: Users, label: "Competitors", path: "/competitors" },
  { icon: History, label: "Run History", path: "/runs" },
];

const SETTINGS_ITEMS = [
  { label: "Project", path: "/settings/project" },
  { label: "Brands", path: "/settings/brands" },
  { label: "Tracking", path: "/settings/tracking" },
  { label: "Account", path: "/settings/account" },
  { label: "Organization", path: "/settings/organization" },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const initials = (user?.name ?? "")
    .split(" ")
    .map((p) => p.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase() || "?";
  const { data: projects = [] } = useProjects();
  const { activeProjectId, setActiveProjectId } = useProjectStore();
  const [projectOpen, setProjectOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    if (!activeProjectId && projects.length > 0) {
      setActiveProjectId(projects[0].id);
    }
  }, [activeProjectId, projects, setActiveProjectId]);

  const activeProject = projects.find((p) => p.id === activeProjectId) ?? projects[0];

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <aside
      style={{ width: collapsed ? 64 : 240, background: "#faf5e8", borderRight: "1px solid #e5e5e5" }}
      className="h-screen flex flex-col flex-shrink-0 transition-all duration-200 relative z-10"
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b" style={{ borderColor: "#e5e5e5" }}>
        <div className="flex items-center gap-2 overflow-hidden">
          <div
            className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "#1a3a3a" }}
          >
            <Zap size={16} color="#fff" />
          </div>
          {!collapsed && (
            <span style={{ fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 16, color: "#0a0a0a", letterSpacing: "-0.3px" }}>
              AIScope
            </span>
          )}
        </div>
        <button
          onClick={onToggle}
          className="ml-auto p-1 rounded-md hover:bg-[#ebe6d6] transition-colors"
          style={{ color: "#6a6a6a" }}
        >
          {collapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      {/* Project Switcher */}
      <div className="px-3 py-3 border-b" style={{ borderColor: "#e5e5e5" }}>
        {collapsed ? (
          <div className="mx-auto w-fit cursor-pointer" title={activeProject?.name ?? "No project"}>
            <BrandIcon
              name={activeProject?.name ?? "?"}
              faviconUrl={activeProject?.favicon_url ?? undefined}
              domain={activeProject?.website_url ?? undefined}
              size={32}
              radius={8}
            />
          </div>
        ) : (
          <div className="relative">
            <button
              onClick={() => setProjectOpen(!projectOpen)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#ebe6d6] transition-colors text-left"
              style={{ background: "#f5f0e0" }}
            >
              <BrandIcon
                name={activeProject?.name ?? "?"}
                faviconUrl={activeProject?.favicon_url ?? undefined}
                domain={activeProject?.website_url ?? undefined}
                size={24}
                radius={6}
              />
              <span style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }} className="flex-1 truncate">
                {activeProject?.name ?? "No project"}
              </span>
              <ChevronDown size={14} color="#6a6a6a" className={`transition-transform ${projectOpen ? "rotate-180" : ""}`} />
            </button>
            {projectOpen && (
              <div
                className="absolute top-full left-0 right-0 mt-1 rounded-lg overflow-hidden shadow-lg z-50"
                style={{ background: "#fffaf0", border: "1px solid #e5e5e5" }}
              >
                {projects.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => { setActiveProjectId(p.id); setProjectOpen(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#f5f0e0] transition-colors text-left"
                  >
                    <BrandIcon
                      name={p.name}
                      faviconUrl={p.favicon_url ?? undefined}
                      domain={p.website_url ?? undefined}
                      size={20}
                      radius={5}
                    />
                    <span style={{ fontSize: 13, color: "#0a0a0a" }}>{p.name}</span>
                  </button>
                ))}
                {projects.length === 0 && (
                  <div className="px-3 py-2" style={{ fontSize: 13, color: "#9a9a9a" }}>
                    No projects yet
                  </div>
                )}
                <div style={{ borderTop: "1px solid #e5e5e5" }}>
                  <button
                    onClick={() => { setProjectOpen(false); navigate("/onboarding"); }}
                    className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#f5f0e0] transition-colors text-left"
                  >
                    <Plus size={14} color="#6a6a6a" />
                    <span style={{ fontSize: 13, color: "#6a6a6a" }}>New Project</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 overflow-y-auto">
        <div className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.path);
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className="w-full flex items-center gap-3 px-2.5 py-2 rounded-lg transition-colors relative"
                style={{
                  background: active ? "#f5f0e0" : "transparent",
                  color: active ? "#0a0a0a" : "#3a3a3a",
                  borderLeft: active ? "3px solid #1a3a3a" : "3px solid transparent",
                }}
                title={collapsed ? item.label : undefined}
              >
                <item.icon size={16} style={{ flexShrink: 0 }} />
                {!collapsed && (
                  <span style={{ fontSize: 14, fontWeight: active ? 500 : 400 }}>{item.label}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Settings section */}
        <div className="mt-4">
          <div style={{ height: "1px", background: "#e5e5e5", margin: "8px 0" }} />
          {!collapsed && (
            <button
              onClick={() => setSettingsOpen(!settingsOpen)}
              className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-[#ebe6d6] transition-colors"
              style={{ color: "#6a6a6a" }}
            >
              <Settings size={14} />
              <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: "1px", textTransform: "uppercase" }}>
                Settings
              </span>
              <ChevronDown size={12} className={`ml-auto transition-transform ${settingsOpen ? "rotate-180" : ""}`} />
            </button>
          )}
          {collapsed && (
            <button
              onClick={() => navigate("/settings/project")}
              className="w-full flex items-center justify-center py-2 rounded-lg hover:bg-[#ebe6d6] transition-colors"
              style={{ color: "#6a6a6a" }}
              title="Settings"
            >
              <Settings size={16} />
            </button>
          )}
          {!collapsed && settingsOpen && (
            <div className="mt-1 space-y-0.5 pl-4">
              {SETTINGS_ITEMS.map((item) => {
                const active = location.pathname === item.path;
                return (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    className="w-full text-left px-2.5 py-1.5 rounded-md transition-colors"
                    style={{
                      fontSize: 13,
                      color: active ? "#0a0a0a" : "#6a6a6a",
                      fontWeight: active ? 500 : 400,
                      background: active ? "#f5f0e0" : "transparent",
                    }}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </nav>

      {/* User */}
      <div className="px-3 py-3 border-t" style={{ borderColor: "#e5e5e5" }}>
        {collapsed ? (
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center mx-auto cursor-pointer"
            style={{ background: "#1a3a3a", color: "#fff", fontSize: 12, fontWeight: 600 }}
            title={user?.name ?? "Account"}
          >
            {initials}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ background: "#1a3a3a", color: "#fff", fontSize: 11, fontWeight: 600 }}
            >
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <div style={{ fontSize: 13, fontWeight: 500, color: "#0a0a0a" }} className="truncate">{user?.name ?? "Account"}</div>
              <div style={{ fontSize: 11, color: "#6a6a6a" }} className="truncate">{user?.email ?? ""}</div>
            </div>
            <button
              className="p-1.5 rounded-md hover:bg-[#ebe6d6] transition-colors"
              style={{ color: "#6a6a6a" }}
              title="Sign out"
              onClick={logout}
            >
              <LogOut size={14} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
