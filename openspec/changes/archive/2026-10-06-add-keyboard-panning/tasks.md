# Tasks

## 1. Key handling

- [x] 1.1 Add `frontend/js/keys.js` with a pure function that turns a set of held key codes, a Shift flag, and elapsed seconds into a pan offset in screen pixels: `KeyW`/`ArrowUp`, `KeyA`/`ArrowLeft`, `KeyS`/`ArrowDown`, `KeyD`/`ArrowRight` (physical `event.code` values), 700 pixels per second, 2.5 times faster with Shift, diagonals normalized, opposite keys cancelling; verify with a Node one-liner that W, W+D, A+D, and Shift+W give the expected offsets and that W+D has the same length as W
- [x] 1.2 In the same module, track held keys from `keydown` and `keyup` on the window: ignore events whose target is an `input`, `select`, or `textarea`, and events with Ctrl, Alt, or Meta held; call `preventDefault` for handled pan keys so arrows do not scroll the page; clear all held keys on window `blur` and when the document becomes hidden; verify in the browser console that the held set is empty after alt-tabbing away with W down

## 2. Panning the view

- [x] 2.1 Give `Board.start` a per-frame callback that receives the elapsed seconds, and use it in `main.js` to apply the pan offset through the existing `Board.panBy`; verify in the browser that holding each of W, A, S, D and each arrow key moves the view in the specified direction and that it stops on release
- [x] 2.2 Remember the last pointer position over the canvas and refresh the hover highlight after each keyboard pan step, clearing it when the pointer has left the canvas; verify that the highlight changes hex while panning with a still mouse and that a click then acts on the highlighted hex
- [x] 2.3 Verify the non-interference cases in the browser: typing `was` in the speed field enters text without panning, arrow keys in the iteration field, slider, and species picker act on the control, Ctrl+D does not pan, and pan keys work right after clicking Pause or a tool button
- [x] 2.4 Verify speed in the browser: holding D for about one second moves the view roughly 700 pixels at hex size 10 and at hex size 60, and Shift+D moves it visibly further
- [x] 2.5 Add WASD, arrow keys, and Shift to the controls list in `README.md`; verify the description matches the behavior

## 3. Integration check

- [x] 3.1 Run the backend test suite to confirm nothing else changed, and confirm in the browser that drag panning, wheel zoom, planting, and cutting still work alongside keyboard panning, including dragging while a pan key is held
