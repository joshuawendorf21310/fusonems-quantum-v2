import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App.jsx'

describe('App', () => {
  it('renders the command center title', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText(/Quantum Command Center/i)).toBeInTheDocument()
  })
})
