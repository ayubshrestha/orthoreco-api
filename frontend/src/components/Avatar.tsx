type Props = {
  firstName: string;
  lastName: string;
  size?: number;
};

const PALETTE = [
  ["#fef3c7", "#92400e"],
  ["#dbeafe", "#1e40af"],
  ["#ede9fe", "#5b21b6"],
  ["#dcfce7", "#166534"],
  ["#fee2e2", "#991b1b"],
  ["#cffafe", "#155e75"],
  ["#fce7f3", "#9d174d"],
  ["#e0e7ff", "#3730a3"],
];

function pickColor(seed: string): [string, string] {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return PALETTE[h % PALETTE.length] as [string, string];
}

export function Avatar({ firstName, lastName, size = 28 }: Props) {
  const initials =
    (firstName?.[0] ?? "").toUpperCase() + (lastName?.[0] ?? "").toUpperCase();
  const [bg, fg] = pickColor(`${firstName}${lastName}`);
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
        borderRadius: "50%",
        background: bg,
        color: fg,
        fontWeight: 600,
        fontSize: size * 0.4,
        flexShrink: 0,
      }}
    >
      {initials || "?"}
    </span>
  );
}
