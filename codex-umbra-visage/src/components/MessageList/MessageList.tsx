import './MessageList.module.css'

interface Message {
  id: string
  text: string
  type: 'user' | 'system'
  timestamp: string
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="message-list">
      {messages.length === 0 ? (
        <div className="empty-state">
          <h2>Codex Umbra</h2>
          <p>The Sentinel awaits your command...</p>
        </div>
      ) : (
        messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              <span className="message-text">{message.text}</span>
              <span className="message-time">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))
      )}
    </div>
  )
}