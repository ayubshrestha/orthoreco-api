import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api";

export function Layout() {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">Orthoreco · Clinician Dashboard</div>
        <nav>
          <NavLink to="/" end>Overview</NavLink>
          <NavLink to="/patients">Patients</NavLink>
        </nav>
        <button onClick={handleLogout}>Log out</button>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
