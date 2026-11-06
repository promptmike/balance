# Balance
A simple game for learning algebra

## Stacks and multiplication

Drop a marble onto an existing stack to add it to that sum. Drop into a quadrant's
empty space (including its heading or the reserved space below the stacks) to
start a separate stack. Marbles can be regrouped within the same quadrant or
returned to the tray.

A stack adds its marble weights; a quadrant multiplies its stack weights. Each
side divides its top quadrant by its bottom quadrant. For example, stacks
`(1 + 2)` and `(3)` above the plate weigh `9`. The existing empty-top value of `0`
and empty-bottom value of `1` are retained. Empty stacks are removed immediately.

Stacks wrap into separate rows when necessary and grow vertically to fit all
eight marbles. Adjacent marbles overlap slightly, leaving their numbers visible.
This favors visibility over a fixed-height game board: large arrangements can
require vertical scrolling. Tilt is reduced for tall layouts on narrow screens
so the scale stays within the viewport.

## Browser regression tests

The website has no runtime dependencies. The optional tests use Python and
Playwright:

```sh
python3 -m venv /tmp/balance-tests
/tmp/balance-tests/bin/pip install playwright
/tmp/balance-tests/bin/playwright install chromium
python3 -m http.server 8765 --directory docs
```

With that server running, in another terminal:

```sh
/tmp/balance-tests/bin/python -m unittest discover -s tests -v
```

Set `BALANCE_URL` to test a different server. Tests cover stack sums, quadrant
products, fraction equality, same-quadrant regrouping, transfers, empty-stack
cleanup, invalid/cancelled drops, and all eight marbles either together or in
separate stacks at 320px, 375px and 1280px viewport widths. Layout checks verify
that stacks do not overlap and marble labels remain exposed.

### Issue #7 validation notes

- Initial Chromium run: arithmetic and interaction tests passed; four layout
  cases failed due to horizontal overflow at 320px and 375px with a tilted,
  loaded numerator. Viewport-aware tilt limits fix those cases.
- Final Chromium run: all four tests, including twelve extreme-layout cases,
  passed. `git diff --check` passed.
- Test setup initially failed because Node/npm were unavailable, the Node tool's
  Playwright import failed, and the sandbox prevented opening a local server.
  Validation proceeded using a temporary Python Playwright environment and an
  approved local server/browser process. Playwright used its Ubuntu fallback
  Chromium build because the host OS is not officially supported.
- Limitations: no physical touchscreen, Firefox or Safari verification. The
  existing pointer-only interaction and positive marble weights are unchanged;
  zero/negative weights and keyboard controls are outside this issue's scope.
