import { h } from 'preact';
import { useTranslation } from 'react-i18next';
export default function Sidebar({ onSelect }){
  const { t } = useTranslation();
  const convs = [{id:'c1', name:'Alice'},{id:'c2', name:'Team'}];
  return (
    <div class="w-1/4 border-r">
      <div class="p-4 font-bold">{t('appName')}</div>
      <div>
        {convs.map(c=>(
          <div key={c.id} class="p-3 hover:bg-gray-100 cursor-pointer" onClick={()=>onSelect(c)}>{c.name}</div>
        ))}
      </div>
    </div>
  );
}
