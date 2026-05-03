type Props = { status: string | null };

export function StatusPill({ status }: Props) {
  if (!status) return <span className="muted">—</span>;
  const cls = status.replace(/\s+/g, "");
  return <span className={`status-pill status-${cls}`}>{status}</span>;
}
