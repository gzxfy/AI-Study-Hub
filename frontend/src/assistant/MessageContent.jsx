import { messageBlocks } from './messageFormat';

function Inline({ text }) {
  return text.split(/(`[^`\n]+`|\*\*[^*\n]+\*\*)/g).map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
    return part;
  });
}

export default function MessageContent({ content }) {
  return <div className="assistant-prose">{messageBlocks(content).map((block, index) => {
    if (block.type === 'code') return <div className="assistant-code" key={index}>{block.language && <span>{block.language}</span>}<pre tabIndex={0} aria-label="Code example"><code>{block.text}</code></pre></div>;
    if (block.type === 'heading') return <h4 key={index}><Inline text={block.text} /></h4>;
    if (block.type === 'list') { const List = block.ordered ? 'ol' : 'ul'; return <List key={index}>{block.items.map((item, i) => <li key={i}><Inline text={item} /></li>)}</List>; }
    return <p key={index}><Inline text={block.text} /></p>;
  })}</div>;
}
