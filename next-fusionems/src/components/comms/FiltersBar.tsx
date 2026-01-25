import { CommsSearchFilters } from '../../lib/comms/types'

type FiltersBarProps = {
  filters: CommsSearchFilters
  onChange: (filters: CommsSearchFilters) => void
}

export default function FiltersBar({ filters, onChange }: FiltersBarProps) {
  return (
    <div className="filters-bar">
      <select
        value={filters.channel || 'all'}
        onChange={(event) => onChange({ ...filters, channel: event.target.value as CommsSearchFilters['channel'] })}
      >
        <option value="all">All Channels</option>
        <option value="email">Email</option>
        <option value="sms">SMS</option>
        <option value="mms">MMS</option>
        <option value="voice">Voice</option>
        <option value="fax">Fax</option>
        <option value="secure">Secure</option>
      </select>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={Boolean(filters.unreadOnly)}
          onChange={(event) => onChange({ ...filters, unreadOnly: event.target.checked })}
        />
        Unread only
      </label>
    </div>
  )
}
