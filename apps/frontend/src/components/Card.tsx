export default function Card({
  title,
  aside,
  children,
}: {
  title: string
  aside?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-slate-800">{title}</h2>
        {aside}
      </header>
      {children}
    </section>
  )
}
