import PropTypes from "prop-types"

export default function SectionHeader({ eyebrow, title, action }) {
  const titleId =
    typeof title === "string"
      ? `section-title-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`
      : undefined

  return (
    <header className="section-header">
      <div className="section-header-text">
        {eyebrow && (
          <p className="eyebrow" aria-hidden="true">
            {eyebrow}
          </p>
        )}

        <h2 id={titleId}>{title}</h2>
      </div>

      {action && (
        <div
          className="section-action"
          aria-labelledby={titleId}
        >
          {action}
        </div>
      )}
    </header>
  )
}

SectionHeader.propTypes = {
  eyebrow: PropTypes.string,
  title: PropTypes.node.isRequired,
  action: PropTypes.node,
}
