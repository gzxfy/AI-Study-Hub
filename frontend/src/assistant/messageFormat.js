// A small display formatter, not an HTML parser. Unsupported Markdown stays text.
export function messageBlocks(content) {
  const lines = content.replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let paragraph = [];
  const flush = () => { if (paragraph.length) { blocks.push({ type: 'paragraph', text: paragraph.join('\n') }); paragraph = []; } };
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (/^\s*```/.test(line)) {
      flush();
      const language = line.trim().slice(3).trim();
      const code = [];
      while (++i < lines.length && !/^\s*```/.test(lines[i])) code.push(lines[i]);
      blocks.push({ type: 'code', text: code.join('\n'), language });
    } else if (/^#{1,6}\s+/.test(line)) {
      flush(); blocks.push({ type: 'heading', text: line.replace(/^#{1,6}\s+/, '') });
    } else if (/^\s*(?:[-*+] |\d+[.)] )/.test(line)) {
      flush();
      const ordered = /^\s*\d/.test(line);
      const previous = blocks[blocks.length - 1];
      const item = line.replace(/^\s*(?:[-*+] |\d+[.)] )/, '');
      if (previous?.type === 'list' && previous.ordered === ordered) previous.items.push(item);
      else blocks.push({ type: 'list', ordered, items: [item] });
    } else if (!line.trim()) flush();
    else paragraph.push(line);
  }
  flush();
  return blocks;
}

export function messageTime(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}
