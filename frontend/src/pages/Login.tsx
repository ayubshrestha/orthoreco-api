import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? "Login failed";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Orthoreco</h1>
        <p>Clinician / admin sign-in</p>

        {error && <div className="error">{error}</div>}

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" className="primary" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>

        <p className="muted" style={{ marginTop: "1rem" }}>
          Demo: <code>admin@demo.com</code> / <code>admin123</code><br />
          Demo: <code>doctor@demo.com</code> / <code>doctor123</code>
        </p>

        <p className="muted" style={{ marginTop: "0.5rem" }}>
          New doctor? <Link to="/register-doctor">Create an account</Link>
        </p>
      </form>
    </div>
  );
}
