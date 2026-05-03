import { useEffect, useState, type FormEvent } from "react";
import {
  createPatientNote,
  listPatientNotes,
  type PatientNote,
} from "../api";
import { Avatar } from "./Avatar";
import { IconSend } from "./Icons";

type Props = {
  patientId: string;
};

export function PatientNotes({ patientId }: Props) {
  const [notes, setNotes] = useState<PatientNote[]>([]);
  const [body, setBody] = useState("");
  const [sendEmail, setSendEmail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    refresh();
  }, [patientId]);

  function refresh() {
    listPatientNotes(patientId)
      .then(setNotes)
      .catch((e) =>
        setError(e?.response?.data?.detail ?? "Failed to load notes"),
      );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (!body.trim()) return;
    setSubmitting(true);
    try {
      await createPatientNote({
        patient_id: patientId,
        body,
        send_email: sendEmail,
      });
      setSuccess(sendEmail ? "Note saved and emailed to patient." : "Note saved.");
      setBody("");
      refresh();
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? "Failed to save note";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h2>Notes &amp; messages</h2>
      <p className="muted" style={{ marginTop: "-0.5rem", marginBottom: "0.85rem" }}>
        Leave a clinical note on this patient's chart. Optionally send the same
        text to the patient by email.
      </p>

      {error && <div className="error">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <form onSubmit={onSubmit}>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          placeholder="e.g. Pain trend is improving — keep current exercise plan and re-assess in 1 week."
          style={{
            width: "100%",
            resize: "vertical",
            fontSize: "0.875rem",
          }}
          required
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "0.6rem",
            flexWrap: "wrap",
            gap: "0.5rem",
          }}
        >
          <label
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.8125rem",
              color: "var(--text-muted)",
            }}
          >
            <input
              type="checkbox"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
            />
            Email this note to the patient
          </label>
          <button
            type="submit"
            className="brand"
            disabled={submitting || !body.trim()}
            style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
          >
            <IconSend size={14} />
            {submitting ? "Saving…" : sendEmail ? "Save & send" : "Save note"}
          </button>
        </div>
      </form>

      <div style={{ marginTop: "1.25rem" }}>
        {notes.length === 0 ? (
          <p className="muted">No notes on this chart yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {notes.map((n) => (
              <li
                key={n.id}
                style={{
                  display: "flex",
                  gap: "0.75rem",
                  padding: "0.85rem 0",
                  borderTop: "1px solid var(--border)",
                }}
              >
                <Avatar
                  firstName={n.doctor_name.split(" ")[0] ?? ""}
                  lastName={n.doctor_name.split(" ").slice(1).join(" ")}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.6rem",
                      fontSize: "0.8125rem",
                      marginBottom: "0.2rem",
                      flexWrap: "wrap",
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>Dr. {n.doctor_name}</span>
                    <span className="faint">·</span>
                    <span className="muted num-mono">
                      {new Date(n.created_at).toLocaleString()}
                    </span>
                    {n.sent_email && (
                      <span className="status-pill status-Good">Emailed</span>
                    )}
                  </div>
                  <div
                    style={{
                      whiteSpace: "pre-wrap",
                      fontSize: "0.875rem",
                      lineHeight: 1.55,
                    }}
                  >
                    {n.body}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
