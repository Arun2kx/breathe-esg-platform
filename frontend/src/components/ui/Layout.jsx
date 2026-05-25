import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  ClipboardCheck,
  ScrollText,
  Leaf,
} from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload Data", icon: Upload },
  { to: "/review", label: "Review Records", icon: ClipboardCheck },
  { to: "/audit", label: "Audit Log", icon: ScrollText },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-surface-900 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-surface-700/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-esg-500 rounded flex items-center justify-center">
              <Leaf size={15} className="text-white" />
            </div>
            <div>
              <div className="text-white font-semibold text-sm leading-tight">BreatheESG</div>
              <div className="text-surface-400 text-xs">Data Platform</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-esg-600/30 text-esg-300 font-medium"
                    : "text-surface-400 hover:bg-surface-800 hover:text-surface-200"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-surface-700/50">
          <div className="text-surface-500 text-xs">v0.1 · Internship Prototype</div>
          <p className="text-xs text-surface-400 mt-1">
  Built by Arun Banoth
</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
