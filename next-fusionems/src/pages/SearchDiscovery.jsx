import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackSearchResults, fallbackSavedSearches } from '../data/fallback.js'

const resultColumns = [
  { key: 'title', label: 'Result' },
  { key: 'module_key', label: 'Module' },
  { key: 'snippet', label: 'Snippet' },
  { key: 'classification', label: 'Class' },
]

const savedColumns = [
  { key: 'name', label: 'Saved Search' },
  { key: 'query', label: 'Query' },
]

export default function SearchDiscovery() {
  const [query, setQuery] = useState('airway')
  const [results, setResults] = useState(fallbackSearchResults)
  const [savedSearches, setSavedSearches] = useState(fallbackSavedSearches)

  const runSearch = async () => {
    try {
      const data = await apiFetch(`/api/search?query=${encodeURIComponent(query)}`)
      if (Array.isArray(data) && data.length > 0) {
        setResults(data)
      }
    } catch (error) {
      console.warn('Search unavailable', error)
    }
  }

  const loadSaved = async () => {
    try {
      const data = await apiFetch('/api/search/saved')
      if (Array.isArray(data) && data.length > 0) {
        setSavedSearches(data)
      }
    } catch (error) {
      console.warn('Saved searches unavailable', error)
    }
  }

  useEffect(() => {
    runSearch()
    loadSaved()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Discovery"
        title="Cross-Module Search"
        action={
          <button className="primary-button" type="button" onClick={runSearch}>
            Run Search
          </button>
        }
      />

      <div className="panel search-panel">
        <div className="search-input-row">
          <input
            className="text-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search incidents, missions, billing packets..."
          />
          <button className="ghost-button" type="button" onClick={runSearch}>
            Refresh
          </button>
        </div>
        <DataTable columns={resultColumns} rows={results} emptyState="No results yet." />
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Saved" title="Legal-Safe Searches" />
        <DataTable columns={savedColumns} rows={savedSearches} emptyState="No saved searches." />
      </div>
    </div>
  )
}
