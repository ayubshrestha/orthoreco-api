import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type PatientTableRow } from "../api";
import { StatusPill } from "../components/StatusPill";

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
      <div className="card">
        <h2>Patients</h2>
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

        <table>
          <thead>
            <tr>
              <th>Patient ID</th>
              <th>Name</th>
              <th>Surgery</th>
              <th>Side</th>
              <th>Days post-op</th>
              <th>Gait / Reports</th>
              <th>Last report</th>
              <th>Recovery</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td>{p.patient_id}</td>
                <td>
                  {p.first_name} {p.last_name}
                  <div className="muted">{p.email}</div>
                </td>
                <td>{p.surgery_type}</td>
                <td>{p.surgery_side}</td>
                <td>{p.days_since_surgery ?? "—"}</td>
                <td>
                  {p.total_gait_records} / {p.total_reports}
                </td>
                <td>{p.last_report_date ?? "—"}</td>
                <td>
                  {p.latest_recovery_score ?? "—"}{" "}
                  <StatusPill status={p.latest_recovery_status} />
                </td>
                <td>
                  <Link to={`/patients/${p.patient_id}`}>View</Link>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} className="muted">
                  No patients found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
