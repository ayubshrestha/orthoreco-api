import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerClinician } from "../api";

export function RegisterDoctorPage() {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [gender, setGender] = useState("Other");
  const [licenseId, setLicenseId] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerClinician({
        first_name: firstName,
        last_name: lastName,
        gender,
        license_id: licenseId,
        email,
        password,
      });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? "Registration failed";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Doctor sign-up</h1>
        <p>Register a new clinician account</p>

        {error && <div className="error">{error}</div>}
        {success && (
          <div
            className="error"
            style={{ background: "#dcfce7", color: "#166534" }}
          >
            Account created. Redirecting to sign-in…
          </div>
        )}

        <label htmlFor="firstName">First name</label>
        <input
          id="firstName"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
        />

        <label htmlFor="lastName">Last name</label>
        <input
          id="lastName"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
        />

        <label htmlFor="gender">Gender</label>
        <select
          id="gender"
          value={gender}
          onChange={(e) => setGender(e.target.value)}
          style={{ width: "100%", marginBottom: "1rem" }}
        >
          <option value="Female">Female</option>
          <option value="Male">Male</option>
          <option value="Other">Other</option>
        </select>

        <label htmlFor="licenseId">License / professional ID</label>
        <input
          id="licenseId"
          value={licenseId}
          onChange={(e) => setLicenseId(e.target.value)}
          required
        />

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
          minLength={6}
        />

        <button type="submit" className="primary" disabled={loading || success}>
          {loading ? "Creating account…" : "Create doctor account"}
        </button>

        <p className="muted" style={{ marginTop: "1rem" }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
