import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api";

const SIDEBAR_KEY = "orthoreco_sidebar_collapsed";

export function Layout() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem(SIDEBAR_KEY) === "1",
  );

  function toggle() {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0");
      return next;
    });
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-head">
          <span className="brand-mark">OR</span>
          {!collapsed && <span className="brand-text">Orthoreco</span>}
          <button
            className="sidebar-toggle"
            onClick={toggle}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand" : "Collapse"}
          >
            {collapsed ? "›" : "‹"}
          </button>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end title="Overview">
            <span className="icon">▦</span>
            {!collapsed && <span>Overview</span>}
          </NavLink>
          <NavLink to="/patients" title="Patients">
            <span className="icon">☰</span>
            {!collapsed && <span>Patients</span>}
          </NavLink>
        </nav>

        <div className="sidebar-foot">
          <button
            className="sidebar-logout"
            onClick={handleLogout}
            title="Log out"
          >
            <span className="icon">⎋</span>
            {!collapsed && <span>Log out</span>}
          </button>
        </div>
      </aside>

      <div className="content-area">
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
