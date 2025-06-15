import { useState } from 'react';
import { ChatInput } from './components/ChatInput/ChatInput'; // Named import
import { MessageList } from './components/MessageList/MessageList'; // Named import
import styles from './App.module.css'; // Import CSS Module
import { IMessage } from './types'; // Import IMessage
import { postMessageToConductor } from './services/api'; // Import API service

function App() {
  const [messages, setMessages] = useState<IMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text: string) => {
    const userMessage: IMessage = {
      id: Date.now().toString(),
      text,
      type: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const apiResponse = await postMessageToConductor(text);
      
      const systemMessage: IMessage = {
        id: (Date.now() + 1).toString(), // Consider a more robust ID generation if issues arise
        text: apiResponse.response,
        type: 'system',
        timestamp: apiResponse.timestamp,
      };

      setMessages(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error("Failed to send message:", error); // Log the actual error
      const errorMessage: IMessage = {
        id: (Date.now() + 1).toString(),
        text: 'Error: Unable to connect to The Conductor. Please check console for details.',
        type: 'system',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.app}> {/* Use CSS Module class */}
      <MessageList messages={messages} />
      <ChatInput onSendMessage={sendMessage} disabled={loading} />
    </div>
  )
}

export default App
