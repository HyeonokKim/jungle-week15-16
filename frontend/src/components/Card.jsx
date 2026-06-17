export default function Card({ children, className = "" }) {
  return <section className={`rounded-md border border-smoke bg-white ${className}`}>{children}</section>;
}
