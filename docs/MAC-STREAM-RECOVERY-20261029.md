# macOS video surface and End stream recovery

This is a local fix on top of the unpublished audit candidate. It does not
publish a release, advance version/build, change console firmware, or replace
the separately installed official chiaki-ng bundle.

## Findings and changes

- The owner reported white video with working audio. Decode counters continued
  to advance. Reconnecting with keyboard/mouse capture disabled restored the
  picture, as confirmed by the owner. This narrows the problem to the capture /
  presentation path but does not by itself prove a unique root cause.
- The old capture hint inserted an AppKit text view into Qt's streaming
  `contentView`. The hint now uses an independent, nonactivating, mouse-transparent
  child panel that disappears after three seconds. Qt's video view and backing
  layer are left to the renderer. Keyboard bindings and sensitivity are retained.
- A stuck old engine was independently sampled during shutdown. Its main thread
  was in `StreamSession::~StreamSession` → `chiaki_thread_join` while network
  threads remained alive. SIGTERM did not end that already stuck process; the
  exact owned child had to be killed. The PS5 was not powered off.
- The supervisor now starts a fixed deadline only on an explicit stop or a
  closing notice from the owned streaming window. It first requests normal
  closure, then sends SIGTERM after three seconds, and SIGKILL after one more
  second if needed. Repeated stop requests do not extend the deadline. It keeps
  the stream lock until the exact child has been reaped.
- Closing the temporary hint panel cannot issue a stream-closing notice. Native
  window-close observation is active even when keyboard/mouse capture is off.

## Checks on 2026-10-29

- 118 desktop tests passed. Three new tests exercise real child processes and
  Unix sockets: SIGTERM-resistant child plus repeated stop, native closing notice,
  and an unknown packet that must not interrupt a healthy child.
- The actual native input core passed its ASan/UBSan harness. The final adapter
  compiled with `-Wall -Wextra -Werror`; the packaged app passed strict codesign
  verification (ad hoc, not notarized).
- Thirty deployed Python sources match the checkout. Local pairing checksum is
  unchanged. Keyboard/mouse capture is enabled again with the owner's bindings.
- On a live PS5 session with capture enabled, End stream returned the dashboard
  to idle in 0.701 seconds. Neither SIGTERM nor SIGKILL fallback was needed in
  this final live stop test. A subsequent connection again decoded 1080p video.

## Acceptance boundaries

Decoded frames are not proof of visible presentation. The initial owner-confirmed
picture was the temporary no-capture test; the final capture-enabled visual and
input acceptance must be recorded separately. Automated window capture still
fails with ScreenCaptureKit -3811, so no live screenshot acceptance is claimed.
The OpenGL shared-context warning also appeared in the successful no-capture
test and is not, by itself, evidence of the white-screen cause.

Long sessions, display sleep/wake, multiple monitors, repeated fullscreen changes,
physical controller combinations, Android/Switch, and clean-user Gatekeeper are
not covered by this focused Mac check. No public release/update channel or old
release asset was edited.

## Follow-up: restoring keyboard/mouse after minimizing

The owner confirmed visible video in the final capture-enabled connection, then
reported that keyboard/mouse stopped after minimizing and restoring the stream.
The previous focus-loss handler deliberately released capture but had no resume
transition.

Focus loss now suspends capture, releases the pointer and clears every held
key/button. Returning to the same visible, non-minimized key streaming window
automatically resumes capture, only when that engine app is active and has no
modal dialog. Duplicate app/window focus-loss notifications preserve the pending
resume. Explicit Esc/F8 release, End stream and application termination cancel
it. No global keyboard monitor or new system permission is introduced.

The production state policy is shared with the native harness. It passed 500
cycles through all 32 focus combinations, including neutral input on return,
fresh WASD input after return, duplicate loss notifications and cancellation of
pending resume. The 118 desktop tests also passed. These checks validate the
state policy and native build; the owner must still verify the real macOS
minimize/restore cycle and physical input after installing this follow-up.

## Owner rejection and instrumented lifecycle follow-up

The owner rejected that focus follow-up: input still failed, window/image size
changed and sound continued while minimized. Passing the policy harness did not
establish acceptance of the macOS lifecycle.

The next local candidate adds a per-process `metrics.json.input` diagnostic with
focus/capture state, aggregate event counts, virtual-controller attachment and
open state, and window dimensions in logical points. It contains no key values,
mouse coordinates, window titles, console names, IPs or credentials. A true stop
cancels capture; Esc/F8 frees the cursor for the current focus interval. A content
click or leave/return cycle can capture again, including Esc → minimize → restore.
The owned key window is reconciled instead of relying forever on the first native
window pointer.

Minimize/restore saves and restores the window frame in logical points, bounded
by the current screen, without changing the negotiated video resolution. Content
clicks that reclaim input are consumed instead of reaching the engine's
double-click fullscreen shortcut. Background/minimized audio submissions are
dropped through the actual SDL queue API, letting the decoder/drain continue
without building a delayed audio backlog or changing system volume.

All 120 desktop checks passed on the Mac, including two native checks: the
ASan/UBSan input/focus/Retina geometry harness and a real SDL dummy-device test
with the production adapter inserted for 500 mute/unmute cycles. This establishes
native policy and audio-queue behavior, not physical input, visible window or
audible acceptance. The instrumented owner test remains required.

The instrumented session subsequently exposed an actual 1920×1080-point window
on a 1470×956-point screen. The owned engine profile now uses `Adjust Manually`
window sizing and removes oversized/off-screen cached geometry against Qt's
available screen bounds; the video request remains 1080p. Restore preserves the
actual saved native frame, including a safe-area frame smaller than NSScreen.

The owner also showed a disabled input-editor button during a live session.
Mac input editing is now available while streaming, while connection/video and
general Save controls remain locked. A bounded, validated per-process JSON
request and private `conf` command apply mappings/speed/inversion without
restarting. Success is displayed only after the matching process/revision and
open virtual controller acknowledge the update; otherwise the UI says it was
saved for the next session. Invalid/partial runtime profiles retain the current
mapping. The setting explanation is included in all 16 desktop catalogs.

The expanded suite passed 125 tests, including the actual Mac widget guard,
local-socket request/ack, oversized geometry, and native runtime parser cases.
The final editor checks were rerun after the capture-button state adjustment.
This does not replace the owner's visible minimize/restore and in-game checks.
