import { h } from 'preact';
import { useState } from 'preact/hooks';
import socket from '../services/socket';
import { useTranslation } from 'react-i18next';
export default function Composer({ conversation }){
  const [text, setText] = useState('');
  const { t } = useTranslation();
  async function send(){
    if(!conversation) return;
    const encoder = new TextEncoder();
    const raw = encoder.encode(text || '');
    const b64 = btoa(String.fromCharCode(...raw));
    socket.emit('send_message',{conversation_id:conversation.id, sender_uid:'me', message_compressed_b64:b64, iv:'', message_type:'text', size_bytes: raw.length});
    setText('');
  }
  async function onFile(e){
    const f = e.target.files[0];
    if(!f) return;
    const arr = await f.arrayBuffer();
    const bytes = new Uint8Array(arr);
    const b64 = btoa(String.fromCharCode(...bytes));
    socket.emit('upload_file_to_drive',{conversation_id:conversation.id, sender_uid:'me', filename:f.name, file_b64:b64});
  }
  return (
    <div class="p-3 border-t flex items-center">
      <input class="flex-1 border rounded p-2 mr-2" value={text} onInput={e=>setText(e.target.value)} placeholder={t('placeholder_type_message')} />
      <input type="file" onChange={onFile} class="mr-2" />
      <button class="bg-blue-600 text-white px-4 py-2 rounded" onClick={send}>{t('send')}</button>
    </div>
  );
}
