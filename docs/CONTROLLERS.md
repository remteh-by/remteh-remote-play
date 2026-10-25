# Controllers and keyboard/mouse — development preview 0.7.0

Deckivo supports compatible controllers instead of assuming a particular brand.
DualSense, DualShock 4 and Xbox Series use genuine model photographs. An unknown
controller shows a gallery of references until its model is identified or chosen.
Choosing a photograph never unlocks USB capabilities. Hardware names in earlier
test records describe those exact tests, not a requirement to buy that controller.

Open **Controller lab → Full USB / Bluetooth diagnostics** on desktop, or
**Controller → Full controller diagnostics** on Android. Desktop uses an isolated
Chrome/Chromium app window and a loopback-only local server. The fixed local port
41179 retains the same origin for model choices and calibration restore points.
Android serves bundled assets at its private appassets origin and adapts native
controller events and explicitly authorized Sony USB interfaces. No root is used.

The original RemTeh tester is included: buttons, triggers and travel, stick center,
noise and circle coverage, traces, before/after, JSON exports; Sony USB touchpad,
motion, lights, motors, adaptive triggers, supported audio tests, version reads and
verified calibration. Actual availability depends on model, transport and OS.
Xbox devices are not given Sony calibration commands. A completed vibration command
is separate from a person's physical confirmation. Microphone access is requested
only by the audio test. Recordings and controller reports stay local unless you
choose to export them. Device reports can include the controller's hardware data;
PS5 registration/account keys are never supplied to the lab.

USB calibration is an optional, deliberate user operation. The inherited engine
keeps authenticity, firmware, battery, same-connection before/after, parameter
readback and permanent-write confirmation gates. No hardware calibration, firmware
flash or permission grant is part of the automatic update/test sequence. A firmware
catalog/archive request uses only RemTeh's fixed public endpoint. Installing official
firmware is done with PS5 or PlayStation Accessories, not by the version checker.

Original photo bytes and origin hashes are in
`desktop/linux/assets/controller-lab/provenance.json`. Equal-height framing and the
DS4 body contour clip remove empty margins and the cast shadow without changing the
source photograph. The artificial SVG floor shadow is removed. The local wrapper,
translations and cleanup adaptations are explicitly recorded. Protocol MIT notices
are retained; product photography is not relabelled as AGPL/unrestricted material.

## Keyboard and mouse emulate a controller

Desktop: enable **Keyboard + mouse → gamepad** in Preferences, save, then start a
stream. Capture is active only in the focused stream: the owned engine window on Mac, and the Deckivo input surface on Linux. Esc releases
it. Focus loss releases all buttons and axes without taking focus back from your
other application. Use the dashboard's capture button to recapture. The receiver
also neutralizes input after 250 ms without packets.

Android: open the stream panel and choose **Keyboard + mouse**, or press F8.
Esc releases capture. Hold that panel button for sensitivity and Y-axis inversion.
Android 8/API26 or newer supplies relative pointer capture. Changing focus, ending
capture or leaving the activity resets emulated input. This is gamepad emulation;
a game's own aiming acceleration/deadzone still applies.

| Input | PS5 controller action |
|---|---|
| WASD | Left stick |
| Mouse movement | Right stick |
| Left/right mouse button | R2 / L2 |
| Space / C / R / F | Cross / Circle / Square / Triangle |
| Q / E | L1 / R1 |
| Ctrl / Alt / middle mouse | L3 / R3 / R3 |
| Enter / 1 | Options / Share |
| Tab / F2 | Touchpad click / PS |
| Arrow keys | D-pad |
| Esc | Release capture and every held emulated control |

Mac F8 toggles capture after the feature is enabled in Preferences. A visible badge identifies capture, and Escape releases it. Mac handles its own window events with a local AppKit monitor; it does not observe other apps. Linux uses the focused Qt surface.

Desktop input is a virtual SDL controller inside the owned streaming process, not
an OS-wide virtual HID driver or global keyboard hook. macOS prepares a private copy
of the installed official chiaki-ng engine and signs that copy locally; the original
installation and system security settings stay unchanged. The adapter is not
inherited by Qt helper subprocesses. Linux composes the input adapter with its
existing per-process Tegra decoder adapter. Tested software ABI: SDL2 >=2.24.

## Stream quality

The current engine exposes 360p/540p/720p/1080p and 30/60 FPS presets. The dashboard
adds 1080p choices; advanced Android settings retain the individual profile options.
4K is not a supported/verified stream mode in this engine. Rendering a 1080p stream
on a 4K monitor does not make the received stream 4K. These are requested profiles,
not a claim of sustained FPS. Start at 720p on Switch if bandwidth or decoding is
unstable. Existing Mac quality preferences migrate once to the matching profile.

## Verification boundary

37 Android unit tests, 46 desktop tests and the native SDL harness passed; Lint has
zero new findings, 96 unchanged upstream baseline warnings. Browser checks cover
English/Russian at 390–3840 px and synthetic model/capability gates. The native SDL
harness observed pressed buttons/axes/triggers and timeout neutralization.

These software checks do not certify physical DualSense/DS4/Xbox USB calibration,
all motors/sensors/audio routes, mouse aiming in a live game, sustained 1080p play,
older macOS versions, Windows, or this update on Ubuntu hardware. They need the
corresponding real device and deliberate owner acceptance. The Switch currently
runs Android, so a Linux source package is prepared for its next Ubuntu session.
