import { h } from 'preact';
import Sidebar from '../components/Sidebar.jsx';
import Chat from '../components/Chat.jsx';
import { useState } from 'preact/hooks';
export default function App(){
  const [active, setActive] = useState(null);
  return (
    <div class="flex h-screen">
      <Sidebar onSelect={setActive} />
      <Chat conversation={active} />
    </div>
  );
}
