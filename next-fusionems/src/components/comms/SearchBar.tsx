type SearchBarProps = {
  value: string
  onChange: (value: string) => void
}

export default function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <div className="search-bar">
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search conversations"
      />
    </div>
  )
}
