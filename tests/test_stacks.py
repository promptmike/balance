"""Run with Playwright installed and BALANCE_URL pointing to the served docs site."""
import os
import unittest
from playwright.sync_api import sync_playwright


class StackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 1000})
        self.page.goto(os.environ.get("BALANCE_URL", "http://127.0.0.1:8765"))

    def tearDown(self):
        self.page.close()

    def move(self, source, destination):
        self.page.locator(source).first.drag_to(self.page.locator(destination).last)

    def add(self, weight, quadrant, stack=False):
        self.move(f'#tray .marble[data-weight="{weight}"]',
                  f'#{quadrant} .stack .marble' if stack else f'#{quadrant} h2')

    def result(self, expected):
        self.assertEqual(self.page.locator('#result').text_content(), expected)

    def test_sums_products_and_fractions(self):
        self.result('Left 0 = 0 Right')
        self.add(1, 'left')
        self.add(2, 'left', stack=True)
        self.result('Left 3 > 0 Right')
        self.add(3, 'left')
        self.result('Left 9 > 0 Right')
        self.add(1, 'left-bottom')
        self.add(2, 'left-bottom', stack=True)
        self.add(3, 'left-bottom')
        self.result('Left 9/9 > 0 Right')
        self.add(4, 'right')
        self.add(4, 'right-bottom')
        self.result('Left 9/9 = 4/4 Right')
        self.assertEqual(self.page.locator('.beam').evaluate(
            "el => el.style.getPropertyValue('--tilt')"), '0deg')

    def test_regroup_remove_and_transfer(self):
        self.add(2, 'left')
        self.add(3, 'left')
        self.result('Left 6 > 0 Right')
        self.move('#left .stack:first-child .marble', '#left .stack:last-child .marble')
        self.result('Left 5 > 0 Right')
        self.assertEqual(self.page.locator('#left .stack').count(), 1)
        self.move('#left .marble[data-weight="2"]', '#left h2')
        self.result('Left 6 > 0 Right')
        self.move('#left .marble[data-weight="2"]', '#right-bottom h2')
        self.result('Left 3 > 0/2 Right')
        self.move('#right-bottom .marble', '#tray h2')
        self.result('Left 3 > 0 Right')
        self.assertEqual(self.page.locator('#right-bottom .stack').count(), 0)
        self.move('#left .marble', '#tray h2')
        self.result('Left 0 = 0 Right')
        self.assertEqual(self.page.locator('.stack').count(), 0)

    def test_cancel_and_invalid_drop_preserve_stacks(self):
        self.add(2, 'left')
        self.move('#left .marble', 'h1')
        self.move('#left .marble', '#left .marble')
        marble = self.page.locator('#left .marble')
        box = marble.bounding_box()
        self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
        self.page.mouse.down()
        marble.dispatch_event('pointercancel', {'pointerId': 1})
        self.page.mouse.up()
        self.result('Left 2 > 0 Right')
        self.assertEqual(self.page.locator('.preview, .dragging').count(), 0)
        self.assertEqual(self.page.locator('#left .stack').count(), 1)

    def test_drag_whole_stack_and_keep_marble_editing(self):
        self.add(1, 'left')
        self.add(2, 'left', stack=True)
        self.add(3, 'right')
        stack = self.page.locator('#left .stack')
        stack.drag_to(self.page.locator('#right h2'),
                      source_position={'x': 40, 'y': 16})
        self.result('Left 0 < 9 Right')
        self.assertEqual(self.page.locator('#right .stack').count(), 2)
        self.assertEqual(self.page.locator('#left .stack').count(), 0)
        self.move('#right .marble[data-weight="2"]', '#left h2')
        self.result('Left 2 < 3 Right')
        self.move('#left .marble', '#right .stack:last-child .marble')
        self.result('Left 0 < 9 Right')
        self.page.locator('#right .stack').last.drag_to(
            self.page.locator('#left-bottom h2'),
            source_position={'x': 40, 'y': 16})
        self.result('Left 0/3 < 3 Right')

    def test_stack_invalid_drop_and_cancel(self):
        self.add(1, 'left')
        self.add(2, 'left', stack=True)
        stack = self.page.locator('#left .stack')
        for target in ('h1', '#left h2'):
            stack.drag_to(self.page.locator(target),
                          source_position={'x': 40, 'y': 16})
            self.result('Left 3 > 0 Right')
            self.assertEqual(stack.locator('.marble').count(), 2)
        box = stack.bounding_box()
        self.page.mouse.move(box['x'] + 40, box['y'] + 16)
        self.page.mouse.down()
        stack.dispatch_event('pointercancel', {'pointerId': 1})
        self.page.mouse.up()
        self.assertEqual(self.page.locator('.preview, .dragging').count(), 0)

    def test_horizontal_sums_and_responsive_scale(self):
        for weight in (1, 2, 3, 4):
            self.add(weight, 'left', stack=weight != 1)
        self.add(1, 'left')
        for width in (320, 375, 768, 1280, 1920):
            with self.subTest(width=width):
                self.page.set_viewport_size({'width': width, 'height': 1000})
                # Viewport resize events are delivered at the next rendering frame.
                self.page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                geometry = self.page.evaluate("""() => {
                  const beam = document.querySelector('.beam');
                  const stacks = [...document.querySelectorAll('#left .stack')];
                  const marbles = [...stacks[0].querySelectorAll('.marble')];
                  const area = document.querySelector('#left .marbles');
                  return {
                    beamWidth: beam.offsetWidth,
                    sameRow: marbles.every(m => m.offsetTop === marbles[0].offsetTop),
                    ordered: marbles.every((m, i) => !i || m.offsetLeft > marbles[i-1].offsetLeft),
                    factorsHorizontal: stacks[0].offsetTop + stacks[0].offsetHeight === stacks[1].offsetTop + stacks[1].offsetHeight,
                    scrollable: area.scrollWidth > area.clientWidth,
                    pageWidth: document.documentElement.scrollWidth,
                    tilt: Math.abs(parseFloat(beam.style.getPropertyValue('--tilt'))),
                    padding: parseFloat(getComputedStyle(beam.parentElement).paddingTop)
                  };
                }""")
                self.assertTrue(geometry['sameRow'])
                self.assertTrue(geometry['ordered'])
                self.assertGreater(geometry['beamWidth'], width - 50)
                self.assertLessEqual(geometry['pageWidth'], width)
                if width >= 1280:
                    self.assertTrue(geometry['factorsHorizontal'])
                if width == 320:
                    self.assertTrue(geometry['scrollable'])
                # Wide beams must not rotate into instructions or the result below.
                import math
                self.assertLessEqual(geometry['beamWidth'] / 2 * math.sin(
                    math.radians(geometry['tilt'])), geometry['padding'])
                self.result('Left 10 > 0 Right')

    def test_weighted_ghosts_rebuild_without_affecting_weight(self):
        self.add(2, 'left')
        self.add(1, 'left', stack=True)
        self.add(4, 'left')
        self.add(2, 'left')
        self.result('Left 24 > 0 Right')
        terms = self.page.locator('#left .stack')
        self.assertEqual(terms.nth(0).locator('.ghost-row').count(), 0)
        self.assertEqual(terms.nth(1).locator('.ghost-row').count(), 2)
        self.assertEqual(terms.nth(2).locator('.ghost-row').count(), 11)
        self.assertEqual(terms.nth(2).get_attribute('data-rows'), '3')
        self.assertEqual(terms.nth(2).get_attribute('data-layers'), '4')
        self.assertEqual(terms.nth(2).get_attribute('data-visual-total'), '24')
        self.assertEqual(self.page.locator('.marble').count(), 8)
        self.move('#left .marble[data-weight="1"]', '#tray h2')
        self.result('Left 16 > 0 Right')
        self.assertEqual(terms.nth(2).locator('.ghost-row').count(), 7)
        # Removing the whole first factor shifts both the index and the multipliers.
        self.move('#left .stack:first-child .marble', '#tray h2')
        self.result('Left 8 > 0 Right')
        self.assertEqual(terms.nth(0).locator('.ghost-row').count(), 0)
        self.assertEqual(terms.nth(1).locator('.ghost-row').count(), 3)
        self.assertEqual(terms.nth(1).get_attribute('data-layers'), '1')
        self.assertEqual(self.page.locator('.marble').count(), 8)

    def test_three_term_limit_is_atomic(self):
        for quadrant in ('left', 'right', 'left-bottom', 'right-bottom'):
            with self.subTest(quadrant=quadrant):
                self.page.reload()
                for weight in (1, 2, 3):
                    self.add(weight, quadrant)
                before = self.page.locator('#result').text_content()
                self.add(4, quadrant)
                self.assertEqual(self.page.locator('#result').text_content(), before)
                self.assertEqual(self.page.locator(f'#{quadrant} .stack').count(), 3)
                self.assertEqual(self.page.locator('#tray .marble').count(), 5)
                self.assertIn('3 terms', self.page.locator('#move-message').text_content())
                other = 'right' if quadrant != 'right' else 'left'
                self.add(4, other)
                self.page.locator(f'#{other} .stack').drag_to(
                    self.page.locator(f'#{quadrant} h2'), source_position={'x': 40, 'y': 16})
                self.assertEqual(self.page.locator(f'#{other} .stack').count(), 1)
                # Adding to an existing sum is legal at capacity.
                self.add(1, quadrant, stack=True)
                self.assertEqual(self.page.locator(f'#{quadrant} .marble').count(), 4)
                # Splitting that sum would create a fourth factor and must do nothing.
                self.move(f'#{quadrant} .stack:last-child .marble[data-weight="1"]', f'#{quadrant} h2')
                self.assertEqual(self.page.locator(f'#{quadrant} .stack').count(), 3)
                self.assertEqual(self.page.locator(f'#{quadrant} .stack:last-child .marble').count(), 2)
                # Repositioning a singleton replaces a factor instead of adding one.
                self.move(f'#{quadrant} .stack:first-child .marble', f'#{quadrant} h2')
                self.assertEqual(self.page.locator(f'#{quadrant} .stack').count(), 3)
                self.assertEqual(self.page.locator(f'#{quadrant} .marble').count(), 4)
                self.assertEqual(self.page.locator('.marble').count(), 8)

    def test_touch_drag_and_cancel(self):
        # Exercise trusted touch input and pointer capture, not synthetic DOM events.
        self.page.set_viewport_size({'width': 1280, 'height': 1400})
        session = self.page.context.new_cdp_session(self.page)
        session.send('Emulation.setTouchEmulationEnabled', {'enabled': True})

        def touch_move(source, target, cancel=False):
            start = self.page.locator(source).first.bounding_box()
            end = self.page.locator(target).bounding_box()
            x, y = start['x'] + start['width']/2, start['y'] + start['height']/2
            end_x, end_y = end['x'] + end['width']/2, end['y'] + end['height']/2
            session.send('Input.dispatchTouchEvent', {'type': 'touchStart',
                'touchPoints': [{'x': x, 'y': y}]})
            for step in range(1, 6):
                session.send('Input.dispatchTouchEvent', {'type': 'touchMove',
                    'touchPoints': [{'x': x + (end_x-x)*step/5, 'y': y + (end_y-y)*step/5}]})
            session.send('Input.dispatchTouchEvent', {
                'type': 'touchCancel' if cancel else 'touchEnd', 'touchPoints': []})

        touch_move('#tray .marble[data-weight="2"]', '#left h2')
        touch_move('#tray .marble[data-weight="3"]', '#left .marble')
        self.result('Left 5 > 0 Right')
        touch_move('#left .marble[data-weight="2"]', '#right h2', cancel=True)
        self.result('Left 5 > 0 Right')
        self.assertEqual(self.page.locator('.preview, .dragging').count(), 0)
        touch_move('#left .marble[data-weight="2"]', '#right h2')
        self.result('Left 3 > 2 Right')
        session.detach()

    def test_rendering_stress_and_adaptive_overlap(self):
        self.add(4, 'left')
        data = self.page.evaluate("""() => {
          const stack = document.querySelector('#left .stack');
          const samples = [];
          for (const factors of [[1, 1, 4], [3, 4, 4], [24, 24, 4], [1, 576, 4]]) {
            MultiplicationView.render(stack, factors);
            const rows = factors[0], layers = factors[1];
            const shape = MultiplicationView.layout(1, rows, layers);
            samples.push({ copies: stack.querySelectorAll('.ghost-row').length,
              total: Number(stack.dataset.visualTotal), rows, layers,
              rowStep: shape.rowStep, depthStep: shape.depthStep,
              width: stack.offsetWidth, height: stack.offsetHeight });
          }
          return samples;
        }""")
        for sample in data:
            self.assertEqual(sample['copies'], sample['rows'] * sample['layers'] - 1)
            self.assertEqual(sample['total'], sample['rows'] * sample['layers'] * 4)
            self.assertLess(sample['width'], 1400)
            self.assertLess(sample['height'], 1000)
            self.assertGreaterEqual(sample['rowStep'], 2)
            self.assertGreaterEqual(sample['depthStep'], 2)
        self.assertEqual(data[1]['rowStep'], 42)
        self.assertEqual(data[1]['depthStep'], 28)
        self.assertLess(data[2]['rowStep'], data[1]['rowStep'])
        self.assertLess(data[3]['depthStep'], data[1]['depthStep'])
        self.assertEqual(self.page.locator('.marble').count(), 8)
        self.result('Left 4 > 0 Right')

    def test_reorder_terms_and_disband_stack(self):
        for weight in (2, 3, 4):
            self.add(weight, 'left')
        self.page.locator('#left .stack').last.drag_to(
            self.page.locator('#left .stack').first,
            source_position={'x': 40, 'y': 16}, target_position={'x': 8, 'y': 40})
        self.assertEqual(self.page.locator('#left .marble').all_text_contents(), ['4', '2', '3'])
        self.result('Left 24 > 0 Right')
        self.assertEqual(self.page.locator('#left .stack').last.get_attribute('data-rows'), '4')
        self.assertEqual(self.page.locator('#left .stack').last.get_attribute('data-layers'), '2')
        self.page.locator('#left .stack').first.drag_to(
            self.page.locator('#tray h2'), source_position={'x': 40, 'y': 16})
        self.result('Left 6 > 0 Right')
        self.assertEqual(self.page.locator('#tray .stack').count(), 0)
        self.assertEqual(self.page.locator('#tray .marble').count(), 6)
        self.assertEqual(self.page.locator('.marble').count(), 8)
        # A singleton dragged into empty space becomes the final term, not a fourth factor.
        self.move('#left .stack:first-child .marble', '#left h2')
        self.assertEqual(self.page.locator('#left .marble').all_text_contents(), ['3', '2'])
        self.result('Left 6 > 0 Right')
        self.add(1, 'left', stack=True)
        self.page.locator('#left .stack').last.drag_to(
            self.page.locator('#tray h2'), source_position={'x': 40, 'y': 16})
        self.result('Left 3 > 0 Right')
        self.assertEqual(self.page.locator('#tray .marble').count(), 7)
        self.assertEqual(self.page.locator('#tray .stack-visual').count(), 0)

    def test_balloons_arrows_and_conversion(self):
        self.add(2, 'left-bottom')
        self.add(3, 'left-bottom')
        stacks = self.page.locator('#left-bottom .stack')
        self.assertEqual(self.page.locator('#left-bottom .balloon').count(), 2)
        self.assertEqual(stacks.last.locator('.ghost-balloon').count(), 1)
        self.assertEqual(stacks.last.locator('.ghost-row').count(), 1)
        self.assertEqual(stacks.last.locator('.force-arrow').get_attribute('data-direction'), 'up')
        self.result('Left 0/6 = 0 Right')
        self.page.locator('#left-bottom .stack').last.drag_to(
            self.page.locator('#left h2'), source_position={'x': 40, 'y': 16})
        self.assertEqual(self.page.locator('#left .balloon').count(), 0)
        self.assertEqual(self.page.locator('#left .force-arrow').get_attribute('data-direction'), 'down')
        self.result('Left 3/2 > 0 Right')
        self.page.locator('#left-bottom .stack').drag_to(
            self.page.locator('#tray h2'), source_position={'x': 40, 'y': 16})
        self.assertEqual(self.page.locator('#tray .balloon').count(), 0)
        self.assertEqual(self.page.locator('#tray .force-arrow').count(), 0)
        self.result('Left 3 > 0 Right')
        self.assertEqual(self.page.locator('.marble').count(), 8)

    def test_products_above_and_real_sums_below(self):
        for quadrant in ('left', 'left-bottom'):
            with self.subTest(quadrant=quadrant):
                self.page.reload()
                self.add(1, quadrant)
                self.add(2, quadrant, stack=True)
                self.add(3, quadrant)
                self.add(4, quadrant)
                self.assertEqual(self.page.locator(f'#{quadrant} .term-product').all_text_contents(),
                                 ['3', '3 × 3 = 9', '3 × 3 × 4 = 36'])
                self.assertEqual(self.page.locator(f'#{quadrant} .term-sum').all_text_contents(),
                                 ['1 + 2 = 3', '3', '4'])
                geometry = self.page.locator(f'#{quadrant} .stack').evaluate_all("""stacks => stacks.map(s => {
                    const product = s.querySelector('.term-product');
                    const visual = s.querySelector('.stack-visual');
                    const real = s.querySelector('.marble');
                    const brace = s.querySelector('.sum-brace');
                    const sum = s.querySelector('.term-sum');
                    const arrow = s.querySelector('.force-arrow');
                    const top = e => parseFloat(getComputedStyle(e).top);
                    return { productAbove: top(product) + product.offsetHeight < top(visual),
                      braceBelow: top(brace) > real.offsetTop + real.offsetHeight,
                      sumBelow: top(sum) >= top(brace) + 16,
                      braceWidth: Number(brace.getAttribute('width')),
                      realWidth: parseFloat(s.style.getPropertyValue('--row-width')),
                      arrowOutside: s.classList.contains('balloon-stack') ?
                        top(arrow) + 24 < top(visual) : top(arrow) > top(sum) + sum.offsetHeight };
                })""")
                for item in geometry:
                    self.assertTrue(item['productAbove'])
                    self.assertTrue(item['braceBelow'])
                    self.assertTrue(item['sumBelow'])
                    self.assertEqual(item['braceWidth'], item['realWidth'])
                    self.assertTrue(item['arrowOutside'])

    def test_extreme_layouts(self):
        for width in (320, 375, 768, 1280, 1920):
            for quadrant in ('left', 'left-bottom'):
                for combined in (True, False):
                    with self.subTest(width=width, quadrant=quadrant, combined=combined):
                        self.page.set_viewport_size({'width': width, 'height': 1000})
                        self.page.reload()
                        for index, weight in enumerate((1, 2, 4, 3, 4, 1, 2, 3)):
                            self.add(weight, quadrant, stack=index > 0 if combined else index not in (0, 3, 5))
                        self.assertEqual(self.page.locator(f'#{quadrant} .marble').count(), 8)
                        self.assertEqual(self.page.locator(f'#{quadrant} .stack').count(), 1 if combined else 3)
                        value = 20 if combined else 294
                        self.result(f'Left {value} > 0 Right' if quadrant == 'left'
                                    else f'Left 0/{value} = 0 Right')
                        errors = self.page.evaluate('''() => {
                          const errors = [];
                          if (document.documentElement.scrollWidth > innerWidth) errors.push('horizontal overflow');
                          // Inspect the layout before rotation: sums must occupy disjoint boxes.
                          const beam = document.querySelector('.beam');
                          beam.style.rotate = '0deg';
                          const stacks = [...document.querySelectorAll('.stack')].map(s => s.getBoundingClientRect());
                          stacks.forEach((a, i) => stacks.slice(i+1).forEach(b => {
                            if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top)
                              errors.push('overlapping stacks');
                          }));
                          for (const marble of document.querySelectorAll('.stack .marble')) {
                            marble.scrollIntoView({block: 'center'});
                            const r = marble.getBoundingClientRect();
                            if (document.elementFromPoint(r.x+r.width/2, r.y+r.height/2) !== marble)
                              errors.push('hidden marble label');
                          }
                          beam.style.removeProperty('rotate');
                          return errors;
                        }''')
                        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()

