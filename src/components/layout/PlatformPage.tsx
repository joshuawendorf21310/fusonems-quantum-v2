"use client"

type PlatformPageProps = {
  title: string
  description: string
  highlights?: string[]
}

export default function PlatformPage({ title, description, highlights = [] }: PlatformPageProps) {
  return (
    <section className="platform-page">
      <header>
        <div className="eyebrow">Mission status</div>
        <h2>{title}</h2>
        <p>{description}</p>
      </header>
      <div className="platform-card-grid">
        {highlights.map((item) => (
          <article key={item} className="platform-card">
            <p>{item}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
