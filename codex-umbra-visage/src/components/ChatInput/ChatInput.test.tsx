import { render, screen, fireEvent } from '@testing-library/react'
import { ChatInput } from './ChatInput'
import { describe, it, expect, vi } from 'vitest'

describe('ChatInput', () => {
  it('renders input and button', () => {
    const mockOnSend = vi.fn()
    render(<ChatInput onSendMessage={mockOnSend} />)
    
    expect(screen.getByPlaceholderText(/Enter command for The Sentinel/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Send/ })).toBeInTheDocument()
  })

  it('calls onSendMessage when form is submitted', () => {
    const mockOnSend = vi.fn()
    render(<ChatInput onSendMessage={mockOnSend} />)
    
    const input = screen.getByPlaceholderText(/Enter command for The Sentinel/)
    const button = screen.getByRole('button', { name: /Send/ })
    
    fireEvent.change(input, { target: { value: 'test message' } })
    fireEvent.click(button)
    
    expect(mockOnSend).toHaveBeenCalledWith('test message')
  })
})
