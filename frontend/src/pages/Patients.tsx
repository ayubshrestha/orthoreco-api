import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type PatientTableRow } from "../api";
import { StatusPill } from "../components/StatusPill";
import { Avatar } from "../components/Avatar";

export function PatientsPage() {
  const [rows, setRows] = useState<PatientTableRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [surgeryType, setSurgeryType] = useState("");

  useEffect(() => {
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (surgeryType) params.surgery_type = surgeryType;

    api
      .get<PatientTableRow[]>("/dashboard/admin/patients", { params })
      .then((r) => setRows(r.data))
      .catch((e) => setError(e?.response?.data?.detail ?? "Failed to load"));
  }, [search, surgeryType]);

  const surgeryOptions = useMemo(
    () => Array.from(new Set(rows.map((r) => r.surgery_type))).sort(),
    [rows],
  );

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Patients</h1>
          <div className="subtitle">
            Browse the cohort and drill into a patient's recovery history.
          </div>
        </div>
      </div>

      <div className="card">
        <h2>All patients</h2>
        <div className="toolbar">
          <input
            placeholder="Search by name, email, or patient_id"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            value={surgeryType}
            onChange={(e) => setSurgeryType(e.target.value)}
          >
            <option value="">All surgery types</option>
            {surgeryOptions.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Surgery</th>
                <th className="num">Days post-op</th>
                <th className="num">Records</th>
                <th>Last report</th>
                <th>Recovery</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div className="cell-primary">
                      <Avatar firstName={p.first_name} lastName={p.last_name} />
                      <div className="cell-stack">
                        <span className="primary">
                          {p.first_name} {p.last_name}
                        </span>
                        <span className="secondary">
                          {p.email} · <code>{p.patient_id}</code>
                        </span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div className="cell-stack">
                      <span className="primary">{p.surgery_type}</span>
                      <span className="secondary">{p.surgery_side}</span>
                    </div>
                  </td>
                  <td className="num num-mono">
                    {p.days_since_surgery ?? "—"}
                  </td>
                  <td className="num num-mono">
                    {p.total_gait_records}
                    <span className="faint"> / </span>
                    {p.total_reports}
                  </td>
                  <td>
                    {p.last_report_date ? (
                      <span className="num-mono">{p.last_report_date}</span>
                    ) : (
                      <span className="faint">—</span>
                    )}
                  </td>
                  <td>
                    <div className="cell-primary">
                      {p.latest_recovery_score != null && (
                        <span className="num-mono" style={{ fontWeight: 500 }}>
                          {p.latest_recovery_score}
                        </span>
                      )}
                      <StatusPill status={p.latest_recovery_status} />
                    </div>
                  </td>
                  <td>
                    <div className="cell-actions">
                      <Link to={`/patients/${p.patient_id}`}>View</Link>
                      <Link
                        to={`/appointments?patient_id=${p.patient_id}`}
                        className="brand"
                      >
                        Invite
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="empty-cell">
                    No patients found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
