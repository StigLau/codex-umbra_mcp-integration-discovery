import { render, screen } from '@testing-library/react'
import { MessageList } from './MessageList'
import { IMessage } from '../../types'
import { describe, it, expect } from 'vitest'

describe('MessageList', () => {
  it('shows empty state when no messages', () => {
    render(<MessageList messages={[]} />)
    expect(screen.getByText(/Codex Umbra/)).toBeInTheDocument()
    expect(screen.getByText(/The Sentinel awaits your command/)).toBeInTheDocument()
  })

  it('renders messages correctly', () => {
    const messages: IMessage[] = [
      {
        id: '1',
        text: 'Hello',
        type: 'user',
        timestamp: '2024-01-01T12:00:00Z'
      },
      {
        id: '2',
        text: 'Hi there',
        type: 'system',
        timestamp: '2024-01-01T12:01:00Z'
      }
    ]

    render(<MessageList messages={messages} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there')).toBeInTheDocument()
  })
})
