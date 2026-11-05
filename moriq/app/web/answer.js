// Turns an answer's plain text into safe DOM. It only ever creates elements and text nodes, so model output cannot inject markup.
const INLINE = /(\*\*[^*\n]+\*\*|\[\d{1,2}\])/g;

function inline(parent, text, options) {
  for (const part of text.split(INLINE)) {
    if (!part) continue;
    const bold = part.match(/^\*\*([^*\n]+)\*\*$/);
    const cite = part.match(/^\[(\d{1,2})\]$/);
    if (bold) {
      const strong = document.createElement('strong');
      inline(strong, bold[1], options);
      parent.append(strong);
    } else if (cite) {
      const number = Number(cite[1]);
      const known = options.sourceCount >= number && number > 0;
      const chip = document.createElement(known && options.onCite ? 'button' : 'span');
      chip.className = 'cite';
      chip.textContent = cite[1];
      if (chip.tagName === 'BUTTON') {
        chip.type = 'button';
        chip.setAttribute('aria-label', `Open source ${number}`);
        chip.addEventListener('click', () => options.onCite(number, chip));
      }
      parent.append(known || !options.final ? chip : document.createTextNode(part));
    } else {
      parent.append(document.createTextNode(part));
    }
  }
}

export function renderAnswer(container, text, options = {}) {
  const settings = {sourceCount: 0, onCite: null, final: false, ...options};
  const nodes = [];
  let list = null, paragraph = [];
  const flush = () => {
    if (paragraph.length) {
      const p = document.createElement('p');
      paragraph.forEach((line, position) => {
        if (position) p.append(document.createElement('br'));
        inline(p, line, settings);
      });
      nodes.push(p);
      paragraph = [];
    }
  };
  for (const raw of text.replace(/\r\n/g, '\n').split('\n')) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    const number = line.match(/^(\d{1,2})[.)]\s+(.*)$/);
    const heading = line.match(/^#{1,4}\s+(.*)$/);
    if (bullet || number) {
      flush();
      const tag = bullet ? 'UL' : 'OL';
      if (!list || list.tagName !== tag) { list = document.createElement(tag); nodes.push(list); }
      const item = document.createElement('li');
      inline(item, bullet ? bullet[1] : number[2], settings);
      list.append(item);
      continue;
    }
    if (!line) { flush(); list = null; continue; }
    if (heading) {
      flush(); list = null;
      const h3 = document.createElement('h3');
      inline(h3, heading[1], settings);
      nodes.push(h3);
      continue;
    }
    list = null;
    paragraph.push(line);
  }
  flush();
  container.replaceChildren(...(nodes.length ? nodes : [document.createElement('p')]));
}
