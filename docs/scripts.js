const beam = document.querySelector('.beam');
const left = document.querySelector('#left');
const right = document.querySelector('#right');
const leftBottom = document.querySelector('#left-bottom');
const rightBottom = document.querySelector('#right-bottom');
const tray = document.querySelector('#tray');
const result = document.querySelector('#result');
const colours = [
  { name: 'Red', colour: '#a52339', weight: 1 },
  { name: 'Blue', colour: '#1658a1', weight: 2 },
  { name: 'Green', colour: '#217044', weight: 3 },
  { name: 'Purple', colour: '#693b91', weight: 4 },
];

for (const { name, colour, weight } of colours) {
  for (let copy = 0; copy < 2; copy++) {
    const marble = document.createElement('span');
    marble.className = 'marble';
    marble.style.setProperty('--colour', colour);
    marble.dataset.weight = weight;
    marble.title = `${name} marble, weight ${weight}`;
    marble.textContent = weight;
    tray.querySelector('.marbles').append(marble);
  }
}

function totalWeight(plate) {
  return Array.from(plate.querySelectorAll('.marble'))
    .reduce((sum, marble) => sum + Number(marble.dataset.weight), 0);
}

function formatWeight(top, bottom) {
  return bottom === 1 ? String(top) : `${top}/${bottom}`;
}

function updateScale() {
  const leftTop = totalWeight(left);
  const rightTop = totalWeight(right);
  const leftDenominator = totalWeight(leftBottom) || 1;
  const rightDenominator = totalWeight(rightBottom) || 1;

  // Cross-multiply to compare fractions exactly, then scale the tilt by their difference.
  const numerator = rightTop * leftDenominator - leftTop * rightDenominator;
  const difference = numerator / (leftDenominator * rightDenominator);
  const comparison = numerator === 0 ? '=' : numerator > 0 ? '<' : '>';
  const tilt = Math.max(-8, Math.min(8, difference * 2));
  beam.style.setProperty('--tilt', `${tilt}deg`);
  const leftWeight = formatWeight(leftTop, leftDenominator);
  const rightWeight = formatWeight(rightTop, rightDenominator);
  result.value = `Left ${leftWeight} ${comparison} ${rightWeight} Right`;
}

let drag;

function movePreview(event) {
  drag.preview.style.left = `${event.clientX}px`;
  drag.preview.style.top = `${event.clientY}px`;
}

document.addEventListener('pointerdown', (event) => {
  const marble = event.target.closest('.marble');
  if (!marble || drag || event.button !== 0) return;

  marble.setPointerCapture(event.pointerId);
  const preview = marble.cloneNode(true);
  preview.classList.add('preview');
  preview.setAttribute('aria-hidden', 'true');
  preview.style.width = `${marble.offsetWidth}px`;
  document.body.append(preview);
  marble.classList.add('dragging');
  drag = { marble, preview, pointerId: event.pointerId };
  movePreview(event);
});

document.addEventListener('pointermove', (event) => {
  if (drag?.pointerId === event.pointerId) movePreview(event);
});

function finishDrag(event) {
  if (drag?.pointerId !== event.pointerId) return;

  const { marble, preview } = drag;
  drag = undefined;
  preview.remove();
  marble.classList.remove('dragging');

  if (event.type !== 'pointerup') return;

  const target = document.elementFromPoint(event.clientX, event.clientY);
  const destination = target?.closest('.plate, #tray');
  if (destination && destination !== marble.closest('.plate, #tray')) {
    destination.querySelector('.marbles').append(marble);
    updateScale();
  }
}

document.addEventListener('pointerup', finishDrag);
document.addEventListener('pointercancel', finishDrag);
document.addEventListener('lostpointercapture', finishDrag);
