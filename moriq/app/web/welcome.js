// Welcome page carousel. Project facts come from public listings; photos are local-only and may be missing.
const PROJECTS = [
  {name: 'Courtyard Villa', place: 'Hyderabad, India', year: '2017', image: '/assets/courtyard-villa.jpg', id: 'courtyard-image', credit: 'Photo courtesy of MORIQ', url: 'https://www.archdaily.com/913785/courtyard-villa-moriq', alt: 'A planted courtyard framed by concrete living spaces, timber decking and patterned paving.'},
  {name: 'Villa 430', place: 'Hyderabad, India', year: '2017', image: '/projects/villa-430.jpg', credit: 'Photo courtesy of MORIQ, as published by HomeAdore', url: 'https://www.archdaily.com/896185/villa-430-moriq', alt: 'Villa 430, a home of two built forms across a central lawn and water body.'},
  {name: 'Amwaj Villa', place: 'Amwaj, Bahrain', year: '2015', image: '/projects/amwaj-villa.jpg', credit: 'Photo courtesy of MORIQ, as published by HomeAdore', url: 'https://www.archdaily.com/954404/amwaj-villa-moriq', alt: 'Amwaj Villa, a contemporary family home in Bahrain.'},
  {name: 'AAK Villa', place: 'Amwaj, Bahrain', year: '2016', image: '/projects/aak-villa.jpg', credit: 'Photo by Riyaz Quraishi, as published by HomeAdore', url: 'https://www.archdaily.com/801530/aak-villa-moriq', alt: 'AAK Villa, an ocean-facing home in Bahrain.'},
  {name: 'Villa in Meenakshi Bamboos', place: 'Hyderabad, India', year: '2012', image: '/projects/meenakshi-bamboos.jpg', credit: 'Photo courtesy of MORIQ, as published by HomeAdore', url: 'https://homeadore.com/?p=88951', alt: 'Villa in Meenakshi Bamboos, a family home planned around a water body under a skylight.'},
  {name: 'Apartment @ 11', place: 'Hyderabad, India', year: '2016', image: '/projects/apartment-11.jpg', credit: 'Photo courtesy of MORIQ, as published by HomeAdore', url: 'https://homeadore.com/?p=147582', alt: 'Apartment @ 11, an interior mixing modern lines with traditional elements.'},
];
const EXTRA_ROWS = [
  {name: 'Sky-high duplex apartment', place: 'Kukatpally, Hyderabad', year: '2015', url: 'https://www.houzz.in/magazine/houzz-tour-contemporary-meets-classical-in-this-hyderabad-home-stsetivw-vs~75412970'},
  {name: 'Studio apartment', place: 'Hyderabad, India', year: '2016', url: 'https://thearchitectsdiary.com/studio-apartment-in-hyderabad-by-moriq'},
];
const SECONDS = 6;
const $ = selector => document.querySelector(selector);
const slides = $('#slides');
let index = 0, timer = null, stopped = matchMedia('(prefers-reduced-motion: reduce)').matches, held = false;

function buildSlide(project, position) {
  const figure = document.createElement('figure');
  figure.className = 'slide' + (position === 0 ? ' current' : '');
  figure.setAttribute('aria-hidden', position === 0 ? 'false' : 'true');
  const fallback = document.createElement('span');
  fallback.className = 'slide-fallback';
  fallback.textContent = project.name;
  fallback.hidden = true;
  const image = new Image();
  if (project.id) image.id = project.id;
  image.alt = project.alt;
  image.loading = position === 0 ? 'eager' : 'lazy';
  image.decoding = 'async';
  image.addEventListener('error', () => { image.hidden = true; fallback.hidden = false; figure.dataset.missing = 'true'; if (position === index) caption(); });
  image.src = project.image;
  figure.append(image, fallback);
  return figure;
}
function caption() {
  const project = PROJECTS[index];
  $('#slide-name').textContent = project.name;
  $('#slide-place').textContent = `${project.place}, ${project.year}`;
  $('#slide-count').textContent = `${index + 1} / ${PROJECTS.length}`;
  const missing = slides.children[index].dataset.missing === 'true';
  $('#slide-credit').textContent = missing ? 'Photo not included in this copy' : project.credit;
}
function show(next) {
  const items = slides.children;
  items[index].classList.remove('current');
  items[index].setAttribute('aria-hidden', 'true');
  index = (next + items.length) % items.length;
  items[index].classList.add('current');
  items[index].setAttribute('aria-hidden', 'false');
  const image = items[index].querySelector('img');
  if (image) image.loading = 'eager';
  caption();
}
function schedule() {
  clearTimeout(timer);
  timer = null;
  const visible = !$('#arrival').hidden && !document.hidden;
  if (!stopped && !held && visible) timer = setTimeout(() => { show(index + 1); schedule(); }, SECONDS * 1000);
}
function pauseLabel() {
  const button = $('#slide-pause');
  button.textContent = stopped ? '▶' : '❚❚';
  button.setAttribute('aria-label', stopped ? 'Play project slideshow' : 'Pause project slideshow');
  $('#slides-status').setAttribute('aria-live', stopped ? 'polite' : 'off');
}
function row(project) {
  const item = document.createElement('li');
  const link = document.createElement('a');
  link.href = project.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
  for (const text of [project.name, project.place, project.year]) { const span = document.createElement('span'); span.textContent = text; link.append(span); }
  item.append(link);
  return item;
}
PROJECTS.forEach((project, position) => slides.append(buildSlide(project, position)));
$('#project-list').append(...[...PROJECTS, ...EXTRA_ROWS].sort((a, b) => b.year - a.year).map(row));
caption();
pauseLabel();
schedule();
$('#slide-prev').addEventListener('click', () => { show(index - 1); schedule(); });
$('#slide-next').addEventListener('click', () => { show(index + 1); schedule(); });
$('#slide-pause').addEventListener('click', () => { stopped = !stopped; pauseLabel(); schedule(); });
$('#about-link').addEventListener('click', () => $('#about-moriq').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}));
const hero = $('.hero');
for (const [name, value] of [['mouseenter', true], ['mouseleave', false], ['focusin', true], ['focusout', false]]) {
  hero.querySelector('.project-caption').addEventListener(name, () => { held = value; schedule(); });
}
hero.addEventListener('keydown', event => {
  if (event.target.closest('a, input, textarea')) return;
  if (event.key === 'ArrowLeft') { show(index - 1); schedule(); }
  if (event.key === 'ArrowRight') { show(index + 1); schedule(); }
});
document.addEventListener('visibilitychange', schedule);
addEventListener('hashchange', schedule);
