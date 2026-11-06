const beam = document.querySelector('.beam');
const left = document.querySelector('#left');
const right = document.querySelector('#right');
const leftBottom = document.querySelector('#left-bottom');
const rightBottom = document.querySelector('#right-bottom');
const tray = document.querySelector('#tray');
const result = document.querySelector('#result');
const moveMessage = document.querySelector('#move-message');
const maxTerms = 3;
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

function stackWeight(stack) {
  return Array.from(stack.querySelectorAll('.marble'))
    .reduce((sum, marble) => sum + Number(marble.dataset.weight), 0);
}

function quadrantWeight(plate) {
  const stacks = Array.from(plate.querySelectorAll('.stack'));
  // Preserve the empty numerator (0) and empty denominator (1) conventions.
  if (!stacks.length) return plate.classList.contains('denominator') ? 1 : 0;
  return stacks.reduce((product, stack) => product * stackWeight(stack), 1);
}

function formatWeight(top, bottom) {
  return bottom === 1 ? String(top) : `${top}/${bottom}`;
}

function updateScale() {
  for (const marble of document.querySelectorAll('.plate .marble, #tray .marble')) {
    const balloon = Boolean(marble.closest('.denominator'));
    marble.classList.toggle('balloon', balloon);
    marble.title = marble.title.replace(/\b(marble|balloon)\b/, balloon ? 'balloon' : 'marble');
  }
  for (const plate of [left, right, leftBottom, rightBottom]) {
    const factors = [];
    for (const stack of plate.querySelectorAll('.stack')) {
      factors.push(stackWeight(stack));
      MultiplicationView.render(stack, factors);
    }
  }
  const leftTop = quadrantWeight(left);
  const rightTop = quadrantWeight(right);
  const leftDenominator = quadrantWeight(leftBottom);
  const rightDenominator = quadrantWeight(rightBottom);

  // Cross-multiply to compare fractions exactly, then scale the tilt by their difference.
  const numerator = rightTop * leftDenominator - leftTop * rightDenominator;
  const difference = numerator / (leftDenominator * rightDenominator);
  const comparison = numerator === 0 ? '=' : numerator > 0 ? '<' : '>';
  // Tall stacks need a smaller angle on narrow screens to stay in view.
  const clearance = Math.max(0, (document.documentElement.clientWidth - beam.offsetWidth) / 2 - 2);
  const verticalClearance = parseFloat(getComputedStyle(beam.parentElement).paddingTop) - 2;
  const verticalLimit = Math.asin(Math.min(1, 2 * verticalClearance / beam.offsetWidth)) * 180 / Math.PI;
  const maxTilt = Math.min(8, verticalLimit, Math.asin(Math.min(1, 2 * clearance / beam.offsetHeight)) * 180 / Math.PI);
  const tilt = Math.max(-maxTilt, Math.min(maxTilt, difference * 2));
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
  const marble = event.target.closest('.marble, .stack');
  if (!marble || drag || event.button !== 0) return;

  moveMessage.textContent = '';
  marble.setPointerCapture(event.pointerId);
  const preview = marble.cloneNode(true);
  preview.classList.add('preview');
  preview.setAttribute('aria-hidden', 'true');
  preview.style.width = `${marble.offsetWidth}px`;
  preview.style.height = `${marble.offsetHeight}px`;
  document.body.append(preview);
  marble.classList.add('dragging');
  drag = { marble, preview, pointerId: event.pointerId };
  movePreview(event);
});

document.addEventListener('pointermove', (event) => {
  if (drag?.pointerId === event.pointerId) {
    movePreview(event);
    showDropMarker(event);
  }
});

function canCreateTerm(plate) {
  if (plate.querySelectorAll('.stack').length < maxTerms) return true;
  moveMessage.textContent = 'Each quadrant can hold up to 3 terms. Combine marbles into existing terms or move a term out first.';
  return false;
}

// Compare positions in the beam's unrotated coordinate system, including wrapped rows.
function beamPoint(x, y) {
  const bounds = beam.getBoundingClientRect();
  const angle = -parseFloat(getComputedStyle(beam).rotate || '0') * Math.PI / 180;
  const dx = x - (bounds.left + bounds.width / 2);
  const dy = y - (bounds.top + bounds.height / 2);
  return { x: dx * Math.cos(angle) - dy * Math.sin(angle),
    y: dx * Math.sin(angle) + dy * Math.cos(angle) };
}

function insertionPoint(destination, target, event, excluded) {
  const stacks = [...destination.querySelectorAll('.stack')].filter(stack => stack !== excluded);
  const hovered = target.closest('.stack');
  // Dropping on the heading or outside the term area appends a new term.
  if (!target.closest('.marbles') || !stacks.length) return null;
  const point = beamPoint(event.clientX, event.clientY);
  let nearest;
  let distance = Infinity;
  for (const stack of stacks) {
    if (hovered && hovered !== excluded && stack !== hovered) continue;
    const box = stack.getBoundingClientRect();
    const center = beamPoint(box.left + box.width / 2, box.top + box.height / 2);
    for (const after of [false, true]) {
      const x = center.x + (after ? 1 : -1) * stack.offsetWidth / 2;
      const d = Math.hypot(point.x - x, point.y - center.y);
      if (d < distance) {
        distance = d;
        nearest = { stack, after };
      }
    }
  }
  return nearest;
}

function clearDropMarkers() {
  document.querySelectorAll('.drop-before, .drop-after').forEach(stack =>
    stack.classList.remove('drop-before', 'drop-after'));
}

function showDropMarker(event) {
  clearDropMarkers();
  const target = document.elementFromPoint(event.clientX, event.clientY);
  const destination = target?.closest('.plate');
  if (!destination) return;
  const wholeStack = drag.marble.classList.contains('stack');
  if (!wholeStack && target.closest('.stack')) return; // Add to this sum.
  const source = drag.marble.closest('.stack');
  const excluded = wholeStack || source?.querySelectorAll('.marble').length === 1 ? source : null;
  const insertion = insertionPoint(destination, target, event, excluded);
  insertion?.stack.classList.add(insertion.after ? 'drop-after' : 'drop-before');
}

function insertTerm(container, stack, insertion) {
  const before = insertion ? (insertion.after ? insertion.stack.nextSibling : insertion.stack) : null;
  container.insertBefore(stack, before);
}

function finishDrag(event) {
  if (drag?.pointerId !== event.pointerId) return;

  const { marble, preview } = drag;
  drag = undefined;
  clearDropMarkers();
  preview.remove();
  marble.classList.remove('dragging');

  if (event.type !== 'pointerup') return;

  const target = document.elementFromPoint(event.clientX, event.clientY);
  const destination = target?.closest('.plate, #tray');
  if (!destination) return;

  if (marble.classList.contains('stack')) {
    if (destination === tray) {
      tray.querySelector('.marbles').append(...marble.querySelectorAll('.marble'));
      marble.remove();
    } else {
      if (destination !== marble.closest('.plate') && !canCreateTerm(destination)) return;
      const insertion = insertionPoint(destination, target, event, marble);
      insertTerm(destination.querySelector('.marbles'), marble, insertion);
    }
    updateScale();
    return;
  }

  const sourceStack = marble.closest('.stack');
  if (destination === tray) {
    tray.querySelector('.marbles').append(marble);
  } else {
    let stack = target.closest('.stack');
    if (stack && stack === sourceStack) return;
    if (!stack) {
      // Moving a singleton inside its own quadrant replaces, rather than adds, a term.
      const replacesSource = sourceStack?.closest('.plate') === destination &&
        sourceStack.querySelectorAll('.marble').length === 1;
      if (!replacesSource && !canCreateTerm(destination)) return;
      stack = document.createElement('div');
      stack.className = 'stack';
      const insertion = insertionPoint(destination, target, event, replacesSource ? sourceStack : null);
      insertTerm(destination.querySelector('.marbles'), stack, insertion);
    }
    stack.append(marble);
  }
  // An empty stack must not become a zero factor in its former quadrant.
  if (sourceStack && !sourceStack.querySelector('.marble')) sourceStack.remove();
  updateScale();
}

document.addEventListener('pointerup', finishDrag);
document.addEventListener('pointercancel', finishDrag);
document.addEventListener('lostpointercapture', finishDrag);

window.addEventListener('resize', updateScale);

