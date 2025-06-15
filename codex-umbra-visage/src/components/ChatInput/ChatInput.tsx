import { useState } from 'react'
import styles from './ChatInput.module.css'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className={styles['chat-input-form']}>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Enter command for The Sentinel..."
        disabled={disabled}
        className={styles['chat-input']}
      />
      <button type="submit" disabled={disabled || !message.trim()} className={styles['send-button']}>
        Send
      </button>
    </form>
  )
}
