import styles from './MessageList.module.css'
import { IMessage } from '../../types';

interface MessageListProps {
  messages: IMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className={styles['message-list']}>
      {messages.length === 0 ? (
        <div className={styles['empty-state']}>
          <h2>Codex Umbra</h2>
          <p>The Sentinel awaits your command...</p>
        </div>
      ) : (
        messages.map((message) => (
          <div key={message.id} className={`${styles.message} ${styles[message.type]}`}>
            <div className={styles['message-content']}>
              <span className={styles['message-text']}>{message.text}</span>
              <span className={styles['message-time']}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
