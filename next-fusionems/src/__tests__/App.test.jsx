import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App.jsx'

const seedSession = (role = 'dispatcher') => {
  window.__AUTH_BOOTSTRAP__ = { role, org_id: 1 }
}

describe('App', () => {
  it('renders the command center title', () => {
    seedSession()
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText(/Quantum Command Center/i)).toBeInTheDocument()
  })

  it('redirects logged-out users to login', () => {
    window.__AUTH_BOOTSTRAP__ = null
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText(/Sign in to FusionEMS Quantum/i)).toBeInTheDocument()
  })

  it('renders the landing system alive panel', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText(/Unified EMS/i)).toBeInTheDocument()
    expect(screen.getByText(/System Alive/i)).toBeInTheDocument()
  })

  it('renders the HEMS mission board with action', () => {
    seedSession('hems_supervisor')
    render(
      <MemoryRouter initialEntries={['/hems/missions']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText(/Live Mission Queue/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Simulate Mission/i })).toBeInTheDocument()
  })

  it('renders the Quantum Documents workspace', () => {
    seedSession('admin')
    render(
      <MemoryRouter initialEntries={['/documents']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getAllByText(/Quantum Documents/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Drive \+ Vault/i).length).toBeGreaterThan(0)
  })
})
