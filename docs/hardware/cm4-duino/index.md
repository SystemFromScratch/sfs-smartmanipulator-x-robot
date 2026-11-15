# CM4-Duino Robot PC board

The Robot PC of SmartManipulator-X runs on a Waveshare **CM4-Duino** carrier
board with a Raspberry Pi **Compute Module 4** (variant with Wi-Fi). The board
has the size and header layout of an Arduino Uno R3 and exposes the CM4 GPIO,
an 8-channel ADC, HDMI, one USB 2.0 port, a camera connector and an M.2 slot.

> **Why this page is so detailed:** the CM4-Duino is no longer sold through
> the official Waveshare channels and its wiki page may disappear. This page
> keeps everything the project needs from the
> [Waveshare wiki](https://www.waveshare.com/wiki/CM4-Duino), retrieved on
> 2026-11-15; the links below point to the
> [vendor files](#vendor-files) on the Waveshare servers. If this page and
> the [schematic](https://files.waveshare.com/upload/a/a1/CM4-Duino-sch.pdf)
> disagree, the schematic is authoritative; update this page.
>
> **Status (2026-11-15):** board selected, not yet brought up in this
> project. Nothing below is verified on our hardware unless marked so.

Waveshare drawings: [pinout](https://www.waveshare.com/wiki/File:CM4-Duino4.png) (Arduino-style headers with
the CM4 GPIO numbers and functions) and
[onboard components](https://www.waveshare.com/wiki/File:CM4-Duino-details-intro.jpg).

## Specifications

| Item | Value |
| --- | --- |
| Compute module | Socket for every Compute Module 4 variant (with or without eMMC, with or without wireless) |
| Power input | 5 V through the USB Type-C connector; use **5 V / 3 A** (Waveshare states 5 V / 2 A as the minimum; the extra current is headroom for the M.2 slot, the USB port and the bus interface), otherwise the CM4 throttles or switches off |
| Type-C as data port | With the BOOT switch ON the CM4 boots from Type-C as a USB device (eMMC flashing with `rpiboot`) |
| USB | 1 × USB 2.0 Type-A host port, **disabled by default** (see [USB 2.0 port](#usb-20-port)) |
| Video | 1 × HDMI (HDMI0), up to 4K at 30 fps; **no DSI** connector |
| Camera | 1 × MIPI CSI-2, 15-pin 1.0 mm FPC; a single camera works only as CAM0 |
| M.2 | M-key slot on the CM4 PCIe lane (one lane), for an NVMe SSD (**2242**) or another PCIe module |
| Storage | microSD socket, used only with CM4 Lite (without eMMC) |
| ADC | TI **ADS7830**, 8 channels, 8 bit, I²C, up to 70 kSPS, default address **0x48** |
| User I/O | LED on **GPIO6**; button USER1 on **GPIO4**; button USER2 on **GPIO5** (or CM4 reset, selectable) |
| Headers | Arduino Uno R3 layout; the CM4 GPIO run at the **IO-VREF** level (3.3 V by default), with no level shifters |
| Ethernet | **No RJ45 connector and no magnetics** on the board. The CM4 Ethernet is not usable without an adapter; this project uses the CM4 Wi-Fi |
| Dimensions, weight | 73.58 × 53.34 mm, 25 g |
| Operating system | Raspberry Pi OS (the wiki covers Bookworm, and older Bullseye/Buster setups) |

## Onboard components

| Item | Function |
| --- | --- |
| Type-C (PWR & BOOT) | 5 V input; also the USB device port for flashing the eMMC |
| USB 2.0 Type-A | Host port, off until enabled in `config.txt` |
| HDMI0 | Display output |
| BOOT switch | **ON:** boot from the Type-C port (`rpiboot`). **OFF:** boot from eMMC or microSD |
| CM4 connector | Two 100-pin board-to-board connectors |
| CAM | MIPI CSI-2 camera (CAM0) |
| PWR / ACT LEDs | Power and CM4 activity |
| User LED | GPIO6 |
| USER1, USER2 | Push buttons, GPIO4 and GPIO5 (USER2 can be the reset button instead) |
| ADS7830 | 8-channel ADC on I²C (GPIO2/GPIO3) |
| Arduino headers | GPIO, I²C, SPI, UART, PWM, analog inputs, power |
| Function pads | Solder-jumper options, see [Function pads](#function-pads) |
| M.2 M-key | NVMe SSD 2242 or another PCIe device |
| microSD | System card for CM4 Lite |

## Header pinout

The labels `Dn` printed on the board are the **BCM GPIO numbers of the CM4**
(`D14` = GPIO14), not Arduino pin numbers. The "Uno position" column says
which Arduino Uno pin sits at the same place; it is derived from the standard
Uno layout and matters only when an Arduino shield is plugged in.

### Digital header (right side, top to bottom)

| Silkscreen | CM4 pin | Alternate function | Uno position | Use in this project |
| --- | --- | --- | --- | --- |
| SCL | GPIO3 | I²C1 SCL (shared with the ADS7830) | SCL | ADC (bus voltage monitoring, optional) |
| SDA | GPIO2 | I²C1 SDA (shared with the ADS7830) | SDA | ADC (optional) |
| AREF | – | ADC reference (`AD_REF` net) | AREF | – |
| GND | GND | – | GND | Bus interface ground |
| D11 | GPIO11 | SPI0 SCLK | D13 | free |
| D9 | GPIO9 | SPI0 MISO | D12 | free |
| D10 | GPIO10 | SPI0 MOSI | D11 | free |
| D8 | GPIO8 | SPI0 CE0 | D10 | free |
| D23 | GPIO23 | – | D9 | free |
| D22 | GPIO22 | – | D8 | free |
| D21 | GPIO21 | – | D7 | free |
| D18 | GPIO18 | PWM0 | D6 | free |
| D19 | GPIO19 | PWM1 | D5 | free |
| D20 | GPIO20 | – | D4 | free |
| D17 | GPIO17 | – | D3 | free |
| D16 | GPIO16 | – | D2 | free |
| D14 | GPIO14 | UART0 TXD | D1 / TX | **DYNAMIXEL bus TX** |
| D15 | GPIO15 | UART0 RXD | D0 / RX | **DYNAMIXEL bus RX** |

### Power and analog headers (left side, top to bottom)

| Silkscreen | Function | Uno position |
| --- | --- | --- |
| A7 | ADS7830 channel 7 | (NC on the Uno) |
| CFG | **A6** (ADS7830 channel 6) or **3.3 V**, selected by the CFG pad | IOREF |
| RST | CM4 reset (`RUN`) or global enable, selected by the RUN/GL-EN pad | RESET |
| 3V3 | 3.3 V (supplies the [bus interface](../wiring.md#robot-pc-cm4-duino-to-the-bus-interface)) | 3.3V |
| 5V | 5 V | 5V |
| GND | Ground | GND |
| GND | Ground | GND |
| VIN | Not described by Waveshare; do not use it to power the board until checked in the schematic | VIN |
| A0–A5 | ADS7830 channels 0–5 | A0–A5 |

!!! warning "3.3 V logic, no protection"
    The GPIO connect straight to the CM4 (IO-VREF, 3.3 V by default; 1.8 V
    selectable). 5 V Arduino shields and 5 V signals damage the CM4. Every
    interface built for this project (bus transceiver, sensors) must use
    3.3 V logic on the CM4 side.

## Function pads

Solder-jumper and 0 Ω options on the top side, next to the CM4 connector:

| Pad | Options | Function | Default |
| --- | --- | --- | --- |
| BT-DIS | open / closed | Disables Bluetooth (CM4 with wireless only) | open |
| WIFI-DIS | open / closed | Disables Wi-Fi (CM4 with wireless only). **Must stay open in this project** | open |
| WP-DIS | open / closed | Write-protect option of the CM4 (not described by Waveshare) | open |
| IO-VREF | 1.8 V / 3.3 V | Logic level of the GPIO bank | 3.3 V |
| RUN / GL-EN | RUN / GL-EN | Whether the RST pin and reset button reset the CM4 (`RUN`) or switch it off (`GLOBAL_EN`) | not stated by Waveshare; check on the board |
| CFG | 3V3 / A6 | Function of the IOREF position of the power header | A6 |
| USER 2 | RST / D5 | USER2 button as reset or as GPIO5 | D5 (GPIO5) |
| AD I2C ADDR | A0, A1 each to 3V3 or GND | ADS7830 address `0b10010 A1 A0`: 0x48 to 0x4B | both GND, **0x48** |

The defaults for BT-DIS, WIFI-DIS and WP-DIS are not documented by Waveshare;
"open" is what the product photos show. Bluetooth is switched off in software
for this project (`dtoverlay=disable-bt`), not with the pad.

## Software setup

The paths below are for Raspberry Pi OS Bookworm (`/boot/firmware/config.txt`;
Bullseye and older use `/boot/config.txt`).

### Flashing the eMMC

1. Set the BOOT switch to **ON** and connect the Type-C port to a PC. Connect
   nothing else, so the CM4 is powered only from the PC.
2. Run `rpiboot` on the PC (Raspberry Pi
   [usbboot](https://github.com/raspberrypi/usbboot); Waveshare ships a
   Windows installer, `Rpiboot_setup.zip`). The eMMC appears as a USB drive.
3. Write the image with Raspberry Pi Imager.
4. Set the BOOT switch to **OFF**, power the board from a 5 V / 3 A supply.

A CM4 Lite boots from the microSD card instead; prepare the card on a PC.

### USB 2.0 port

The port is off by default to save power. Enable it in `config.txt`:

```ini
dtoverlay=dwc2,dr_mode=host
```

Raspberry Pi OS images after 2021-10-30 set `otg_mode=1` in the `[cm4]`
section. The port then still works but the kernel logs
`config failed, hub doesn't have any ports! (err -19)`. Remove `otg_mode=1`
and keep the `dtoverlay` line above to get rid of it.

### ADC (ADS7830)

- I²C bus 1 (GPIO2/GPIO3), address 0x48 by default; enable I²C in
  `raspi-config` or with `dtparam=i2c_arm=on`.
- Single-ended inputs by default (differential possible), 8 bit, reference on
  `AD_REF`.
- An unconnected input reads random values.
- Waveshare's Python example is archived as
  [`CM4-duino-code.zip`](https://files.waveshare.com/upload/5/5d/CM4-duino-code.zip) (`ADS7830.py`,
  run with `sudo python3 ADS7830.py`).

### Camera

Not used by the project now; kept for completeness. Only CAM0 exists. Add the
overlay of the sensor to `config.txt`, for example `dtoverlay=imx219,cam0`
(others: `ov5647`, `ov9281`, `imx290` with `clock-frequency=37125000`,
`imx296`, `imx378`, `imx477`, `imx519`, `imx708`), reboot and test with
`libcamera-hello --list-cameras`. If the log says
`Camera frontend has timed out!`, update the firmware (`sudo rpi-update`).

### Settings used by this project

Planned, see [Robot PC on the CM4-Duino](../../robot-pc/cm4-duino.md):

```ini
# /boot/firmware/config.txt  (SmartManipulator-X, planned)
enable_uart=1
dtoverlay=disable-bt          # PL011 UART0 on GPIO14/15 for the DYNAMIXEL bus
dtoverlay=dwc2,dr_mode=host   # USB 2.0 port (only if a USB device is needed)
```

## Mechanical data

Waveshare drawings and photos:
[board outline dimensions](https://www.waveshare.com/wiki/File:CM4-Duino2.png),
[Compute Module 4 outline dimensions](https://www.waveshare.com/wiki/File:Compute_Module_4_IO_Board_5.png),
[board with the CM4 fitted](https://www.waveshare.com/wiki/File:CM4_Duino_Spec_01.jpg). The 3D model is
[`CM4-Duino_3D.zip`](https://files.waveshare.com/upload/a/a4/CM4-Duino_3D.zip).

## Precautions

- Do not plug or unplug anything except USB and HDMI while the board is powered.
- Use a 5 V / 3 A supply on Type-C; the motor supply of the arm
  stays separate (see [DYNAMIXEL bus](../../dynamixel/bus.md#power-and-ground)).
- While flashing over Type-C, connect nothing else to the board.

## Vendor files

Links checked on 2026-11-15. The files are © Waveshare. Because the board is
discontinued, the repository keeps a backup copy in
`docs/hardware/cm4-duino/vendor/`; it is not covered by the Apache License 2.0
and is not published on this website. If a link below stops working, use the
backup in the repository.

| File | Content | Waveshare original | Backup in the repository |
| --- | --- | --- | --- |
| Schematic | Circuit of the board | [`CM4-Duino-sch.pdf`](https://files.waveshare.com/upload/a/a1/CM4-Duino-sch.pdf) | `CM4-Duino-sch.pdf` |
| Pinout drawing | Headers with CM4 GPIO numbers | [`File:CM4-Duino4.png`](https://www.waveshare.com/wiki/File:CM4-Duino4.png) | `smx-cm4duino-pinout.png` |
| Onboard components | Labeled board photo | [`File:CM4-Duino-details-intro.jpg`](https://www.waveshare.com/wiki/File:CM4-Duino-details-intro.jpg) | `smx-cm4duino-onboard.jpg` |
| Board dimensions | Outline drawing | [`File:CM4-Duino2.png`](https://www.waveshare.com/wiki/File:CM4-Duino2.png) | `smx-cm4duino-dimensions.png` |
| CM4 dimensions | Outline drawing | [`File:Compute_Module_4_IO_Board_5.png`](https://www.waveshare.com/wiki/File:Compute_Module_4_IO_Board_5.png) | `smx-cm4duino-cm4-dimensions.png` |
| Board with the CM4 | Photo | [`File:CM4_Duino_Spec_01.jpg`](https://www.waveshare.com/wiki/File:CM4_Duino_Spec_01.jpg) | `smx-cm4duino-connection.jpg` |
| Example code | ADS7830 Python example | [`CM4-duino-code.zip`](https://files.waveshare.com/upload/5/5d/CM4-duino-code.zip) | `CM4-duino-code.zip` |
| 3D model | Board model | [`CM4-Duino_3D.zip`](https://files.waveshare.com/upload/a/a4/CM4-Duino_3D.zip) | `CM4-Duino_3D.zip` |

Further references, without a backup because their publishers keep them
available: [Raspberry Pi CM4 datasheet and documentation](https://www.raspberrypi.com/documentation/computers/compute-module.html),
[usbboot](https://github.com/raspberrypi/usbboot),
[ADS7830 datasheet (TI)](https://www.ti.com/product/ADS7830).
