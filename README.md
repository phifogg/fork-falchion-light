# Falchion Light

Local Python 3 userspace lighting controller for the ASUS ROG Falchion RX
Low Profile, wired (USB 0b05:1b04, firmware reported as 04.00.04.00) or through
its ROG Omni receiver (USB 0b05:1ace).
Uses the existing Linux hidraw driver. No daemon, downloaded executable,
third-party Python dependency, or custom kernel module.

## Installed usage

Run `man falchion-light` for the full command reference and usage examples.

```sh
falchion-light info
falchion-light probe
falchion-light battery
falchion-light layout
falchion-light sleep
falchion-light sleep 5 --save
falchion-light keys --all 202020 W=ff0000 A=ff0000 S=ff0000 D=ff0000
falchion-light set static 336699 --brightness 50
falchion-light set static ff8800 --brightness 25
falchion-light set static 336699 --brightness 0
```

Hex colors may have a leading # if quoted. Brightness is 0..100.
`set` always specifies a complete effect, color and brightness; it does not
attempt to infer the previous hardware state. Default brightness is 50%.
The last example turns lighting off; repeat a nonzero command to restore it.

`battery` sends the version query and then the read-only power query `12 01`,
and prints the battery level and whether the keyboard is charging, e.g.
`Battery: 72%, charging`. It does not change lighting.

`probe` also prints the active onboard profile (1-5) and its effect, e.g.
`Active profile: 3, effect: raindrop`. Effects without a name in this tool are
shown as `unknown (NN)`. `layout` sends the read-only query `12 12` and prints
the keyboard layout ID, e.g. `Layout ID: 25 (CH, ISO)`. Neither changes lighting.

`sleep` without a value sends the read-only power query `12 01` and prints the
idle sleep timeout. With `1`, `2`, `3`, `5`, `10` or `never` it sends `51 38`,
reads the timeout back and stops with an error if it does not match. Like
lighting, the new timeout only lasts until the keyboard is switched off unless
`--save` is given.

### Per-key colors

`keys` sets individual key colors in the keyboard's direct mode.
`--all RRGGBB` colors every key first; `KEY=RRGGBB` pairs override single keys.
Key names follow key positions on a US layout, so on a QWERTZ keyboard `Y` is
the key labelled Z. `Less` (next to left Shift) and `Hash` (left of Enter)
exist on ISO keyboards, `Backslash` only on ANSI. `falchion-light keys --list`
prints all names. Keys that are not listed keep their current color; the
running effect freezes. Per-key colors are not saved: they last until another
effect is set or the keyboard is switched off. While they are shown, the
keyboard ignores profile switching with Fn shortcuts. To leave per-key mode,
run any `set` command or switch the keyboard off and on.

### Lighting effect examples

```sh
# Blue breathing
falchion-light set breathing 336699 --speed slow --brightness 50

# Rainbow color cycle
falchion-light set cycle 000000 --speed medium --brightness 50

# Rainbow wave moving across the keys
falchion-light set wave 000000 --speed slow --brightness 50

# Blue glow on keypress
falchion-light set reactive 336699 --brightness 50

# Starry night
falchion-light set starry 336699 --speed slow --brightness 50

# Raindrops
falchion-light set raindrop 336699 --speed medium --brightness 50

# Return to steady blue
falchion-light set static 336699 --brightness 50
```

`--speed` accepts `slow`, `medium`, or `fast`; the default is `medium`.
For `cycle` and `wave`, `000000` is a required placeholder color that the effect ignores.
Static lighting and rainbow wave have been visually confirmed on this unit.
The other animated modes follow community protocol evidence and remain
unverified here.

The wave command was tested with the three-packet sequence described in
G-Helper's Falchion RX implementation. All three packets returned the expected
responses; the rainbow wave was visually confirmed on the test keyboard. It runs in the keyboard hardware
without continuous software updates.

### Additional options

`--dry-run` prints the HID report without opening the device.
`--save` explicitly sends the documented apply/save command after setting
the effect. The keyboard acknowledged saving the rainbow wave at slow speed
and 50% brightness. Without this option, the tool sends no explicit save
command. Persistence across power cycles still needs confirmation.

### Save the wave as the keyboard default

```sh
falchion-light set wave 000000 --speed slow --brightness 50 --save
```

This sends the onboard apply/save command, which the keyboard acknowledged.
Check persistence by switching the keyboard off and on, then reconnecting it.
If the wave returns without running the command, no Linux startup task is needed.

## Validation and limits

On 2026-10-15, the version query and static 336699 at 50% brightness returned
the expected responses. Steady blue lighting was visually confirmed on the test keyboard.
Wired USB and the ROG Omni receiver are supported; Bluetooth is not. When both
are connected, the wired interface is used.

On 2026-11-09, a second unit (firmware bytes 13 00 05 00, receiver firmware
bytes 02 00 07 00) was tested through the Omni receiver with the cable
unplugged: the version query, static blue and the three-packet rainbow wave
returned the expected replies and were visually confirmed. Saving through the
receiver also persisted across a power-switch off/on cycle.

Discovery requires exactly one matching USB model, interface 01, and an exact
vendor-control HID descriptor. Both identity and descriptor are rechecked
using ioctl after opening. The program locks the interface, uses nonblocking
I/O, bounded response draining and one-second poll timeouts, and checks echoed
command bytes. No automatic write retries, raw-command facility, firmware
updates, keyboard resets, or input-interface reads are implemented.

From the project directory, run hardware-free tests with:

```sh
python3 -m unittest discover -v
```

## Permissions and installation

Requires Linux, Python 3, and udev/logind for active-session device access.
Only the ASUS ROG Falchion RX Low Profile, wired (`0b05:1b04`) or through its
ROG Omni receiver (`0b05:1ace`), has been tested; other Falchion variants are
unsupported.

Clone the repository and install the executable and manual page:

```sh
git clone https://github.com/ChipGillespie/falchion-light.git
cd falchion-light
install -Dm0755 falchion-light ~/.local/bin/falchion-light
install -Dm0644 falchion-light.1 ~/.local/share/man/man1/falchion-light.1
```

Ensure `~/.local/bin` is in your `PATH`. Review the rule and helper before
installing device permissions with:

```sh
sudo bash ./install-device-access.sh
```

The helper refuses to overwrite an existing rule. Reconnect the keyboard
while logged into your local desktop session if access is not immediately
available. Run `falchion-light info` first to check discovery without sending
commands, then `falchion-light probe` to query the firmware version.

The rule grants the active local desktop user read/write access only to
the vendor interface of the wired keyboard (interface 01) and of the Omni
receiver (interface 02) through udev/logind uaccess. It does not grant access
to the keyboard's or the receiver's typing and pointer interfaces. If an older
version of the rule is already installed, remove it first so the helper can
install the version with the receiver line. Programs
running as the active user can issue vendor commands through the granted
interface, so this is still a device-access permission grant.

No system service or startup job is required. Source changes require reinstalling
the executable with `install -m 0755 falchion-light ~/.local/bin/falchion-light`.

## Removal

Remove the installed user executable and the single rule, reload udev, then
unplug/replug the keyboard to revoke the current device ACL:

```sh
rm ~/.local/bin/falchion-light
rm ~/.local/share/man/man1/falchion-light.1
sudo rm /etc/udev/rules.d/70-falchion-light.rules
sudo udevadm control --reload-rules
```

The source directory can remain for inspection. Lighting can also be adjusted
with the keyboard's Fn+arrow shortcuts.

## Protocol evidence

Community reference source reviewed at commit c8ae06a:
https://github.com/rahulrajaram/rogdriver

Vendor payloads: version query 12 00; effect 51 2c followed by mode, reserved
zero, speed, brightness, color mode, direction, per-LED flag 02, and RGB;
optional apply/save 50 55. The original source's write framing was not reused.

Kernel HID API documentation requires a zero report-number byte before an
unnumbered output report (65 bytes including 64 payload bytes):
https://docs.kernel.org/hid/hidraw.html

Wave protocol evidence: G-Helper commit dd2dced63fbd6e5abb1a50d88b738f7159f5e71d,
`app/Peripherals/Keyboard/Models/Falchion.cs` and `AsusKeyboard.cs`:
https://github.com/seerge/g-helper/tree/dd2dced63fbd6e5abb1a50d88b738f7159f5e71d/app/Peripherals/Keyboard

For USB 1b04, mode 04 requires three 51 2c packets with countdown tags 02, 01,
00. Only the first carries speed, brightness, random-color flag 01, direction
00 and per-LED flag 02. This replaces the unsupported single-packet approach.

Battery protocol evidence: G-Helper commit 991145fc25c2bd0b3345f334f1fdeb8b4172322a,
`app/Peripherals/Keyboard/Models/Falchion.cs` and `AsusKeyboard.cs`. The power
query is 12 01. G-Helper indexes its buffer including the report ID, so its
offsets 11 (percentage) and 9 (charging flag) are bytes 10 and 8 of the hidraw
reply. On a wired unit with firmware bytes `13 00 05 00`, the reply
`12 01 00 00 00 48 02 01 01 14 48 …` was read as 72%, charging.
No G-Helper code was reused.

Profile and layout evidence: G-Helper commit 991145fc25c2bd0b3345f334f1fdeb8b4172322a,
`app/Peripherals/Keyboard/AsusKeyboard.cs` and `Models/Falchion.cs`. G-Helper
indexes its buffer including the report ID, so its offsets 10 (effect), 11
(profile) and 6 (layout ID) are bytes 9, 10 and 5 of the hidraw reply. Switching
through all five onboard profiles on a wired unit changed byte 10 from 1 to 5,
and byte 9 matched each profile's visible effect. A Swiss German unit reports
layout ID 25. Layout names 3 DE, 4 UK, 5 FR and 17 US and the ISO layout ID list
come from G-Helper. No G-Helper code was reused.

Omni receiver evidence: G-Helper commit 991145fc25c2bd0b3345f334f1fdeb8b4172322a,
`app/Peripherals/Keyboard/Models/Falchion.cs` (`FalchionRXLowProfileOmni`):
product 1ace, interface 2, collection 2, report ID 02, 64-byte packets. On
Linux this is one hidraw node for interface 02 with three vendor collections
(report IDs 01-03, 63 bytes each). Commands are the same as wired, sent as
report ID 02 followed by 63 payload bytes; replies start with 02 followed by
the usual echo. No G-Helper code was reused.

Sleep timeout evidence: G-Helper commit 991145fc25c2bd0b3345f334f1fdeb8b4172322a,
`app/Peripherals/Keyboard/AsusKeyboard.cs` (`SetEnergySettings`, power query
12 01) and `app/Peripherals/Mouse/AsusMouse.cs` (`PowerOffSetting`: 00 = 1, 01 = 2,
02 = 3, 03 = 5, 04 = 10 minutes, ff = never). G-Helper's reply offset 7 is byte 6
of the hidraw reply. On a second unit, `51 38 00 00 00` set byte 6 to 00 and the
lighting switched off after about one minute idle. Without 50 55 the previous
timeout returned after a power-switch off/on cycle; with 50 55 the new one stayed.
G-Helper's low-battery warning command `51 37` is rejected with `ff aa` on this
keyboard, wired and through the receiver, so it is not offered. No G-Helper code
was reused.

Per-key evidence: G-Helper commit 991145fc25c2bd0b3345f334f1fdeb8b4172322a,
`app/Peripherals/Keyboard/AsusKeyboard.cs` (`SetLedColors`): direct packets
`c0 81 count 00` followed by `led R G B` per key, 14 keys per packet. Its
Falchion RX layout table follows the rule LED id = column * 8 + row, with rows
1 to 5 on the Low Profile. The key table in this tool was written from that
rule and checked on a Swiss German (ISO) unit by coloring each row, the arrow
keys, WASD, Enter, `<` and the key left of Enter. The keyboard acknowledges
each packet with `c0 82 count 00` rather than an echo. No G-Helper code or
tables were reused.

## License

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 Chip Gillespie.
