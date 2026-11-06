// An orthographic 3D view: x runs right, y runs up, z recedes up and right.
// Ghosts are SVG artwork, never draggable .marble elements or input to arithmetic.
const MultiplicationView = (() => {
  const diameter = 44;
  const marbleStep = 36;
  let nextId = 0;

  function layout(count, rows, layers) {
    // A two-pixel minimum preserves a visible rim even in the 576-layer stress case.
    const rowStep = Math.min(42, Math.max(2, 240 / Math.max(1, rows - 1)));
    const depthStep = Math.min(28, Math.max(2, 320 / Math.max(1, layers - 1)));
    // Even a single row has a visible rear edge, representing the spheres' depth.
    const depth = 24 + (layers - 1) * depthStep;
    const rise = (rows - 1) * rowStep + depth * 0.65;
    const rowWidth = diameter + (count - 1) * marbleStep;
    return { rowStep, depthStep, depth, rise, rowWidth,
      width: rowWidth + depth, height: diameter + rise };
  }

  function svgElement(name, attributes = {}) {
    const element = document.createElementNS('http://www.w3.org/2000/svg', name);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
    return element;
  }

  function render(stack, factors) {
    const balloon = Boolean(stack.closest('.denominator'));
    stack.classList.toggle('balloon-stack', balloon);
    const marbles = [...stack.querySelectorAll('.marble')];
    const rows = factors.length >= 2 ? factors[0] : 1;
    const layers = factors.length === 3 ? factors[1] : 1;
    const total = factors.reduce((product, weight) => product * weight, 1);
    const shape = layout(marbles.length, rows, layers);
    const { rowStep, depthStep, depth, rise, rowWidth, width, height } = shape;
    stack.querySelector('.stack-visual')?.remove();
    stack.querySelector('.stack-caption')?.remove();
    stack.querySelector('.force-arrow')?.remove();
    stack.style.setProperty('--row-width', `${rowWidth}px`);
    stack.style.setProperty('--rise', `${rise}px`);
    stack.style.setProperty('--depth', `${depth}px`);
    stack.dataset.rows = rows;
    stack.dataset.layers = layers;
    stack.dataset.visualTotal = total;
    stack.setAttribute('aria-label', `Term ${factors.length}: real sum ${factors.at(-1)}; ${rows} rows, ${layers} layers; visual total ${total}. Ghost marbles have no weight.`);

    const svg = svgElement('svg', {
      class: 'stack-visual', width, height, viewBox: `0 0 ${width} ${height}`,
      'aria-hidden': 'true', focusable: 'false',
    });
    // A light floor and side outline make the depth direction visible at every size.
    svg.append(svgElement('path', {
      d: `M 0 ${height} L ${depth} ${height - depth * 0.65} L ${width} ${height - depth * 0.65} L ${rowWidth} ${height} Z`,
      class: 'volume-floor',
    }));
    svg.append(svgElement('path', {
      d: `M ${rowWidth} ${height} L ${width} ${height - depth * 0.65} L ${width} 0 L ${rowWidth} ${depth * 0.65}`,
      class: 'volume-edge',
    }));
    const id = `ghost-row-${nextId++}`;
    const defs = svgElement('defs');
    const row = svgElement('g', { id });
    marbles.forEach((marble, index) => {
      const gradientId = `${id}-${index}`;
      const gradient = svgElement('radialGradient', { id: gradientId, cx: '32%', cy: '25%', r: '75%' });
      gradient.append(svgElement('stop', { offset: '0', 'stop-color': '#ffffff' }),
        svgElement('stop', { offset: '.35', 'stop-color': marble.style.getPropertyValue('--colour') }),
        svgElement('stop', { offset: '1', 'stop-color': '#172b3b' }));
      defs.append(gradient);
      const sphere = balloon ? svgElement('path', {
        d: 'M22 1 C-5 1 -5 30 22 41 C49 30 49 1 22 1 Z M20 41 L18 44 L26 44 L24 41 Z',
        transform: `translate(${index * marbleStep} 0)`, class: 'ghost-balloon',
      }) : svgElement('circle', { cx: diameter / 2 + index * marbleStep,
        cy: diameter / 2, r: diameter / 2 - 1 });
      sphere.setAttribute('fill', `url(#${gradientId})`);
      sphere.setAttribute('stroke', '#ffffff');
      sphere.setAttribute('stroke-width', '0.8');
      row.append(sphere);
    });
    defs.append(row);
    svg.append(defs);
    const ghosts = svgElement('g', { class: 'ghost-volume' });
    // Paint far layers first. Every copy is retained, including densely packed cases.
    for (let z = layers - 1; z >= 0; z--) {
      for (let y = rows - 1; y >= 0; y--) {
        if (y === 0 && z === 0) continue;
        ghosts.append(svgElement('use', { href: `#${id}`, class: 'ghost-row',
          'data-row': y, 'data-layer': z,
          transform: `translate(${z * depthStep} ${rise - y * rowStep - z * depthStep * 0.65})` }));
      }
    }
    svg.append(ghosts);
    stack.prepend(svg);
    const caption = document.createElement('span');
    caption.className = 'stack-caption';
    caption.textContent = factors.length === 1 ? `Sum ${total}` : `${factors.join(' × ')} = ${total}`;
    caption.title = `${rows} rows · ${layers} layers. Translucent copies show multiplication; only solid marbles have weight.`;
    stack.append(caption);
    const arrow = svgElement('svg', { class: 'force-arrow', viewBox: '0 0 24 24',
      'data-direction': balloon ? 'up' : 'down', 'aria-hidden': 'true' });
    arrow.append(svgElement('path', { d: balloon ? 'M12 22 V3 M5 10 L12 3 L19 10' :
      'M12 2 V21 M5 14 L12 21 L19 14' }));
    stack.append(arrow);
  }

  return { layout, render };
})();
