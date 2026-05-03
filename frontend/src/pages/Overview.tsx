import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import { api, type Analytics } from "../api";
import { StatusPill } from "../components/StatusPill";
import { Link } from "react-router-dom";

const BUCKET_COLORS: Record<string, string> = {
  Good: "#16a34a",
  Moderate: "#eab308",
  "Needs Attention": "#dc2626",
  "No data": "#94a3b8",
};

export function OverviewPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Analytics>("/dashboard/admin/analytics")
      .then((r) => setData(r.data))
      .catch((e) => setError(e?.response?.data?.detail ?? "Failed to load"));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <p className="muted">Loading analytics…</p>;

  return (
    <>
      <div className="kpi-grid">
        <Kpi label="Patients" value={data.total_patients} />
        <Kpi label="Clinicians" value={data.total_clinicians} />
        <Kpi label="Gait records" value={data.total_gait_records} />
        <Kpi label="Reports" value={data.total_reports} />
        <Kpi label="Avg recovery" value={data.average_recovery_score} />
        <Kpi label="Active (7d)" value={data.patients_active_last_7_days} />
      </div>

      <div className="charts-grid">
        <div className="card">
          <h2>Recovery distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={data.recovery_distribution}
                dataKey="patient_count"
                nameKey="bucket"
                outerRadius={90}
                label
              >
                {data.recovery_distribution.map((b) => (
                  <Cell
                    key={b.bucket}
                    fill={BUCKET_COLORS[b.bucket] ?? "#94a3b8"}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2>Surgery type breakdown</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.surgery_type_breakdown}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="surgery_type" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="patient_count" fill="#4f6ef7" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h2>Top risk patients</h2>
        {data.top_risk_patients.length === 0 ? (
          <p className="muted">No patients flagged as needing attention.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Surgery</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Last report</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.top_risk_patients.map((p) => (
                  <tr key={p.patient_id}>
                    <td>
                      {p.first_name} {p.last_name}{" "}
                      <span className="muted">({p.patient_id})</span>
                    </td>
                    <td>{p.surgery_type}</td>
                    <td>{p.latest_recovery_score}</td>
                    <td>
                      <StatusPill status={p.latest_recovery_status} />
                    </td>
                    <td>{p.last_report_date}</td>
                    <td>
                      <Link to={`/patients/${p.patient_id}`}>View</Link>
                      {" · "}
                      <Link to={`/appointments?patient_id=${p.patient_id}`}>
                        Invite
                      </Link>
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

function Kpi({ label, value }: { label: string; value: number }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  );
}
