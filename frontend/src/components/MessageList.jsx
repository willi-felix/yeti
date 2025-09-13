import { h } from 'preact';
import MessageItem from './MessageItem.jsx';
export default function MessageList({ messages }){
  return messages.map(m=> <MessageItem key={m.id || m.created_at} message={m} />);
}
