import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { logout } from "../api";
import {
  IconCalendar,
  IconChevronLeft,
  IconChevronRight,
  IconClose,
  IconHome,
  IconLogout,
  IconMenu,
  IconUsers,
} from "./Icons";

const SIDEBAR_KEY = "orthoreco_sidebar_collapsed";
const MOBILE_BREAKPOINT = 720;

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();

  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.innerWidth < MOBILE_BREAKPOINT,
  );
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem(SIDEBAR_KEY) === "1",
  );
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    function onResize() {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  function toggleCollapsed() {
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

  const shellClass = [
    "app-shell",
    collapsed && !isMobile ? "sidebar-collapsed" : "",
    isMobile ? "is-mobile" : "",
    isMobile && mobileOpen ? "mobile-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const showLabels = !collapsed || isMobile;

  return (
    <div className={shellClass}>
      {isMobile && (
        <header className="mobile-topbar">
          <button
            className="mobile-toggle"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            <IconMenu size={18} />
          </button>
          <span className="mobile-title">Orthoreco</span>
        </header>
      )}

      {isMobile && mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className="sidebar">
        <div className="sidebar-head">
          <span className="brand-mark">OR</span>
          {showLabels && <span className="brand-text">Orthoreco</span>}
          {!isMobile && (
            <button
              className="sidebar-toggle"
              onClick={toggleCollapsed}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={collapsed ? "Expand" : "Collapse"}
            >
              {collapsed ? <IconChevronRight size={14} /> : <IconChevronLeft size={14} />}
            </button>
          )}
          {isMobile && (
            <button
              className="sidebar-toggle"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
            >
              <IconClose size={14} />
            </button>
          )}
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end title="Overview">
            <span className="icon-slot"><IconHome size={16} /></span>
            {showLabels && <span>Overview</span>}
          </NavLink>
          <NavLink to="/patients" title="Patients">
            <span className="icon-slot"><IconUsers size={16} /></span>
            {showLabels && <span>Patients</span>}
          </NavLink>
          <NavLink to="/appointments" title="Appointments">
            <span className="icon-slot"><IconCalendar size={16} /></span>
            {showLabels && <span>Appointments</span>}
          </NavLink>
        </nav>

        <div className="sidebar-foot">
          <button
            className="sidebar-logout"
            onClick={handleLogout}
            title="Log out"
          >
            <span className="icon-slot"><IconLogout size={16} /></span>
            {showLabels && <span>Log out</span>}
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
