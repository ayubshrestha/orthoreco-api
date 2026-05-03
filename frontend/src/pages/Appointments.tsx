import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  api,
  createAppointment,
  listMyAppointments,
  type Appointment,
  type PatientTableRow,
} from "../api";
import { Avatar } from "../components/Avatar";

export function AppointmentsPage() {
  const [params] = useSearchParams();
  const prefillPatient = params.get("patient_id") ?? "";

  const [patients, setPatients] = useState<PatientTableRow[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [patientId, setPatientId] = useState(prefillPatient);
  const [scheduledFor, setScheduledFor] = useState(defaultSchedule());
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [sendEmail, setSendEmail] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get<PatientTableRow[]>("/dashboard/admin/patients")
      .then((r) => setPatients(r.data))
      .catch((e) => setError(e?.response?.data?.detail ?? "Failed to load patients"));
    refreshAppointments();
  }, []);

  useEffect(() => {
    if (prefillPatient) setPatientId(prefillPatient);
  }, [prefillPatient]);

  function refreshAppointments() {
    listMyAppointments()
      .then(setAppointments)
      .catch((e) => setError(e?.response?.data?.detail ?? "Failed to load appointments"));
  }

  const riskFirst = useMemo(() => {
    return [...patients].sort((a, b) => {
      const order = { "Needs Attention": 0, Moderate: 1, Good: 2 } as Record<string, number>;
      const av = order[a.latest_recovery_status ?? ""] ?? 3;
      const bv = order[b.latest_recovery_status ?? ""] ?? 3;
      return av - bv;
    });
  }, [patients]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const created = await createAppointment({
        patient_id: patientId,
        scheduled_for: new Date(scheduledFor).toISOString(),
        location: location || undefined,
        notes: notes || undefined,
        send_email: sendEmail,
      });
      setSuccess(
        `Appointment created for ${created.patient_first_name} ${created.patient_last_name}` +
          (created.invitation_sent ? " — invitation email queued." : "."),
      );
      setNotes("");
      refreshAppointments();
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? "Failed to create appointment";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Appointments</h1>
          <div className="subtitle">
            Schedule follow-ups and email invitations to patients — at-risk
            patients are listed first.
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Schedule an appointment</h2>
        <p className="muted" style={{ marginBottom: "1rem" }}>
          Pick a patient and propose a time. The patient will be emailed an
          invitation. Use this for at-risk patients to bring them in for a
          follow-up.
        </p>

        {error && <div className="error">{error}</div>}
        {success && <div className="success-banner">{success}</div>}

        <form onSubmit={onSubmit}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "0.75rem",
            }}
          >
            <label>
              <div className="kpi-label">Patient</div>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                required
                style={{ width: "100%" }}
              >
                <option value="">Select a patient…</option>
                {riskFirst.map((p) => (
                  <option key={p.patient_id} value={p.patient_id}>
                    {p.first_name} {p.last_name} ({p.patient_id})
                    {p.latest_recovery_status
                      ? ` — ${p.latest_recovery_status}`
                      : ""}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <div className="kpi-label">Date & time</div>
              <input
                type="datetime-local"
                value={scheduledFor}
                onChange={(e) => setScheduledFor(e.target.value)}
                required
                style={{ width: "100%" }}
              />
            </label>

            <label>
              <div className="kpi-label">Location</div>
              <input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Clinic Room 3"
                style={{ width: "100%" }}
              />
            </label>
          </div>

          <label style={{ display: "block", marginTop: "0.75rem" }}>
            <div className="kpi-label">Notes</div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                border: "1px solid #cbd5e0",
                borderRadius: "6px",
                font: "inherit",
              }}
              placeholder="Reason for visit, recovery concerns, etc."
            />
          </label>

          <label
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              marginTop: "0.75rem",
            }}
          >
            <input
              type="checkbox"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
            />
            Send patient email invitation
          </label>

          <div style={{ marginTop: "1rem" }}>
            <button type="submit" className="brand" disabled={submitting}>
              {submitting ? "Scheduling…" : "Schedule appointment"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>My appointments</h2>
        {appointments.length === 0 ? (
          <p className="muted">No appointments scheduled yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Patient</th>
                  <th>Location</th>
                  <th>Status</th>
                  <th>Invite</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a) => {
                  const dt = new Date(a.scheduled_for);
                  return (
                    <tr key={a.id}>
                      <td>
                        <div className="cell-stack">
                          <span className="primary num-mono">
                            {dt.toLocaleDateString()}
                          </span>
                          <span className="secondary num-mono">
                            {dt.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="cell-primary">
                          <Avatar
                            firstName={a.patient_first_name}
                            lastName={a.patient_last_name}
                          />
                          <div className="cell-stack">
                            <Link
                              to={`/patients/${a.patient_patient_id}`}
                              className="primary"
                            >
                              {a.patient_first_name} {a.patient_last_name}
                            </Link>
                            <span className="secondary">
                              {a.patient_email}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td>{a.location ?? <span className="faint">—</span>}</td>
                      <td>
                        <span className={`status-pill status-${capStatus(a.status)}`}>
                          {a.status}
                        </span>
                      </td>
                      <td>
                        {a.invitation_sent ? (
                          <span className="status-pill status-Good">Sent</span>
                        ) : (
                          <span className="faint">—</span>
                        )}
                      </td>
                      <td className="muted">
                        {a.notes ?? <span className="faint">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function capStatus(s: string): string {
  // Map appointment status string to a status pill variant
  const lc = s.toLowerCase();
  if (lc === "confirmed" || lc === "completed") return "Good";
  if (lc === "cancelled") return "NeedsAttention";
  return "Moderate"; // pending
}

function defaultSchedule(): string {
  const d = new Date();
  d.setDate(d.getDate() + 3);
  d.setHours(10, 0, 0, 0);
  // Format YYYY-MM-DDTHH:mm for <input type="datetime-local">
  const pad = (n: number) => n.toString().padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}
