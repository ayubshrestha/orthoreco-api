import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type PatientDetail } from "../api";
import { StatusPill } from "../components/StatusPill";
import { IconArrowLeft, IconCalendar } from "../components/Icons";
import { PatientNotes } from "../components/PatientNotes";

export function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const [data, setData] = useState<PatientDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (!patientId) return;
    setData(null);
    api
      .get<PatientDetail>(`/dashboard/admin/patients/${patientId}`, {
        params: { days },
      })
      .then((r) => setData(r.data))
      .catch((e) => setError(e?.response?.data?.detail ?? "Failed to load"));
  }, [patientId, days]);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <p className="muted">Loading…</p>;

  const { profile, recent_gait, recent_reports } = data;

  return (
    <>
      <Link to="/patients" className="back-link">
        <IconArrowLeft size={14} /> Back to patients
      </Link>

      <div className="page-header">
        <div>
          <h1>
            {profile.first_name} {profile.last_name}
          </h1>
          <div className="subtitle">
            <code>{profile.patient_id}</code> · {profile.surgery_type} (
            {profile.surgery_side})
          </div>
        </div>
        <Link
          to={`/appointments?patient_id=${profile.patient_id}`}
          className="invite-cta"
        >
          <IconCalendar size={14} /> Invite to appointment
        </Link>
      </div>

      <div className="card">
        <h2>Profile</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "0.75rem",
          }}
        >
          <Field label="Email" value={profile.email} />
          <Field label="Gender" value={profile.gender} />
          <Field label="DOB" value={profile.date_of_birth ?? "—"} />
          <Field label="Surgery" value={profile.surgery_type} />
          <Field label="Side" value={profile.surgery_side} />
          <Field label="Surgery date" value={profile.surgery_date ?? "—"} />
          <Field
            label="Days post-op"
            value={profile.days_since_surgery?.toString() ?? "—"}
          />
          <Field
            label="Latest recovery"
            value={
              <>
                {profile.latest_recovery_score ?? "—"}{" "}
                <StatusPill status={profile.latest_recovery_status} />
              </>
            }
          />
        </div>

        <div className="toolbar" style={{ marginTop: "1rem" }}>
          <label className="muted">
            History window:&nbsp;
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
            >
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={90}>90 days</option>
              <option value={180}>180 days</option>
            </select>
          </label>
        </div>
      </div>

      <PatientNotes patientId={profile.patient_id} />

      <div className="card">
        <h2>Daily activity (steps & active minutes)</h2>
        {recent_gait.length === 0 ? (
          <p className="muted">No gait data in this window.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={recent_gait}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="record_date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="step_count"
                stroke="#2563eb"
                name="Steps"
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="active_minutes"
                stroke="#16a34a"
                name="Active min"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card">
        <h2>Walking quality (speed & cadence)</h2>
        {recent_gait.length === 0 ? (
          <p className="muted">No gait data in this window.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={recent_gait}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="record_date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="walking_speed"
                stroke="#7c3aed"
                name="Speed (m/s)"
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cadence"
                stroke="#ea580c"
                name="Cadence (spm)"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card">
        <h2>Recovery score trend</h2>
        {recent_reports.length === 0 ? (
          <p className="muted">No check-ins in this window.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={recent_reports}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="report_date" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="recovery_score"
                stroke="#0ea5e9"
                name="Recovery score"
                dot
              />
              <Line
                type="monotone"
                dataKey="pain_score"
                stroke="#dc2626"
                name="Pain"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="confidence_score"
                stroke="#16a34a"
                name="Confidence"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="card">
        <h2>Recent check-ins</h2>
        {recent_reports.length === 0 ? (
          <p className="muted">No check-ins in this window.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th className="num">Pain</th>
                  <th className="num">Stiffness</th>
                  <th className="num">Walking</th>
                  <th className="num">Confidence</th>
                  <th>Swelling</th>
                  <th>Exercise</th>
                  <th className="num">Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {[...recent_reports].reverse().map((r) => (
                  <tr key={r.report_date}>
                    <td className="num-mono">{r.report_date}</td>
                    <td className="num num-mono">{r.pain_score}</td>
                    <td className="num num-mono">{r.stiffness_score}</td>
                    <td className="num num-mono">{r.walking_difficulty}</td>
                    <td className="num num-mono">{r.confidence_score}</td>
                    <td>
                      {r.swelling_flag ? (
                        <span className="status-pill status-NeedsAttention">Yes</span>
                      ) : (
                        <span className="faint">No</span>
                      )}
                    </td>
                    <td>
                      {r.exercise_completed ? (
                        <span className="status-pill status-Good">Yes</span>
                      ) : (
                        <span className="faint">No</span>
                      )}
                    </td>
                    <td className="num num-mono" style={{ fontWeight: 500 }}>
                      {r.recovery_score}
                    </td>
                    <td>
                      <StatusPill status={r.recovery_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function Field({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div>
      <div className="kpi-label">{label}</div>
      <div style={{ fontSize: "0.95rem", marginTop: "0.15rem" }}>{value}</div>
    </div>
  );
}
