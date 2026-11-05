"""Built-in starter guide plus documents the owner drops into MORIQ_HOME/documents.

Neither is registry-approved. Each answer is labelled with what it actually used:
the starter guide is AI-written, and owner-loaded documents have no independent review.
"""

import re
from dataclasses import dataclass
from pathlib import Path

_TOKEN = re.compile(r'[a-z0-9]+')
_STOP = frozenset(
    'a an and are as at be but by can do does for from how i if in into is it its me my of on or our please should '
    'that the their them there these this to us was we what when where which who why will with would you your about '
    'explain describe tell give help need want use using work works make good best'.split()
)
MAX_DOCUMENTS = 200
MAX_DOCUMENT_BYTES = 1_000_000
MAX_PASSAGE = 1000


@dataclass(frozen=True)
class Passage:
    kind: str  # starter_guide or owner_document
    title: str
    source: str
    text: str
    terms: frozenset
    title_terms: frozenset


def _terms(text):
    words = set()
    for word in _TOKEN.findall(text.casefold()):
        if word in _STOP:
            continue
        words.add(word[:-1] if len(word) > 3 and word.endswith('s') and not word.endswith('ss') else word)
    return frozenset(words)


def _passage(kind, title, source, text):
    return Passage(kind, title, source, text, _terms(text), _terms(title))


def _guide_passages(path):
    sections = re.split(r'(?m)^## +', path.read_text(encoding='utf-8'))[1:]
    for section in sections:
        title, _, body = section.partition('\n')
        if body.strip():
            yield _passage('starter_guide', title.strip(), path.stem, body.strip())


def _document_passages(path):
    try:
        if path.stat().st_size > MAX_DOCUMENT_BYTES:
            return
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return
    current, title = '', path.stem
    for block in re.split(r'\n\s*\n', text):
        block = block.strip()
        if not block:
            continue
        heading = re.match(r'#+\s+(.+)', block)
        if heading:
            title = heading[1].strip()[:80]
        if current and len(current) + len(block) > MAX_PASSAGE:
            yield _passage('owner_document', title, path.name, current)
            current = ''
        current = f'{current}\n\n{block}'.strip()[:MAX_PASSAGE * 2]
    if current:
        yield _passage('owner_document', title, path.name, current)


class Knowledge:
    def __init__(self, documents=None):
        guide = Path(__file__).resolve().parent / 'guide'
        self.passages = [p for path in sorted(guide.glob('*.md')) for p in _guide_passages(path)]
        if documents and Path(documents).is_dir():
            files = sorted(p for p in Path(documents).iterdir() if p.suffix.lower() in {'.md', '.txt'})
            self.passages += [p for path in files[:MAX_DOCUMENTS] for p in _document_passages(path)]

    @property
    def has_documents(self):
        return any(p.kind == 'owner_document' for p in self.passages)

    def search(self, question, *, kinds=('owner_document', 'starter_guide'), limit=2):
        query = _terms(question)
        if not query:
            return ()
        needed = 1 if len(query) == 1 else 2
        scored = []
        for passage in self.passages:
            if passage.kind not in kinds:
                continue
            matched = query & (passage.terms | passage.title_terms)
            if len(matched) < needed:
                continue
            score = len(matched) + len(query & passage.title_terms) + (1 if passage.kind == 'owner_document' else 0)
            scored.append((-score, passage.title, passage))
        scored.sort(key=lambda row: row[:2])
        return tuple(row[2] for row in scored[:limit])
