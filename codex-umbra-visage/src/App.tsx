import { useState } from 'react'
import ChatInput from './components/ChatInput/ChatInput'
import MessageList from './components/MessageList/MessageList'
import './App.css'

interface Message {
  id: string
  text: string
  type: 'user' | 'system'
  timestamp: string
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const sendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      type: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text })
      })

      const data = await response.json()
      
      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        type: 'system',
        timestamp: data.timestamp
      }

      setMessages(prev => [...prev, systemMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Error: Unable to connect to The Conductor',
        type: 'system',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <MessageList messages={messages} />
      <ChatInput onSendMessage={sendMessage} disabled={loading} />
    </div>
  )
}

export default App
