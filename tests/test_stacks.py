"""Browser regression checks. See README.md for setup and execution."""
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

    def test_extreme_layouts(self):
        for width in (320, 375, 1280):
            for quadrant in ('left', 'left-bottom'):
                for combined in (True, False):
                    with self.subTest(width=width, quadrant=quadrant, combined=combined):
                        self.page.set_viewport_size({'width': width, 'height': 1000})
                        self.page.reload()
                        for index, weight in enumerate((1, 1, 2, 2, 3, 3, 4, 4)):
                            self.add(weight, quadrant, stack=combined and index > 0)
                        self.assertEqual(self.page.locator(f'#{quadrant} .marble').count(), 8)
                        self.assertEqual(self.page.locator(f'#{quadrant} .stack').count(), 1 if combined else 8)
                        value = 20 if combined else 576
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
