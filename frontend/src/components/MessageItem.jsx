import { h } from 'preact';
import twemoji from 'twemoji';
import { useTranslation } from 'react-i18next';
export default function MessageItem({ message }){
  const { t } = useTranslation();
  if(message.attachment){
    const a = message.attachment;
    return (
      <div class="mb-3 p-3 bg-gray-50 rounded">
        <div class="font-semibold">{a.name}</div>
        <div class="text-sm text-gray-600">{a.mime_type} • {(a.size/1024).toFixed(1)} KB</div>
        {a.link ? <a href={a.link} target="_blank" class="text-blue-500">{t('open_file')}</a> : null}
        {a.embed ? <div class="text-xs text-gray-500">{a.embed}</div> : null}
      </div>
    );
  }
  const content = message.message_compressed_b64 ? atob(message.message_compressed_b64) : "";
  const html = twemoji.parse(content);
  return <div class="mb-2" dangerouslySetInnerHTML={{ __html: html }} />;
}
