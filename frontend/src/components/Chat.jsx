import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import socket from '../services/socket';
import MessageList from './MessageList.jsx';
import Composer from './Composer.jsx';
import { useTranslation } from 'react-i18next';
export default function Chat({ conversation }){
  const [messages, setMessages] = useState([]);
  const { t } = useTranslation();
  useEffect(()=>{
    if(!conversation) return;
    socket.emit('join_conversation',{conversation_id:conversation.id});
    socket.on('message_received', msg=>{
      if(msg.conversation_id===conversation.id) setMessages(prev=>[...prev,msg]);
    });
    socket.on('message_retracted', data=>{
      setMessages(prev=>prev.filter(m=>m.id!==data.message_id));
    });
    socket.on('message_blocked', data=>{
      alert(t('blocked') + ': ' + data.reason);
    });
    return ()=>{ socket.off('message_received'); socket.off('message_retracted'); socket.off('message_blocked'); }
  }, [conversation]);
  return (
    <div class="flex-1 flex flex-col">
      <div class="flex-1 overflow-y-auto p-4">
        <MessageList messages={messages} />
      </div>
      <Composer conversation={conversation} />
    </div>
  );
}
