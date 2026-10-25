# Changelog

## 0.1.0 - 2026-10-25

First public release.

- Local control of Skylight Wi-Fi aquarium lamps (SLcontrol), set up from the UI by IP
  address; the lamp is identified by its MAC address.
- Light with brightness, RGB colour and effects: the 60 colours of the SLcontrol palette
  (e.g. "B5 · Neutral white"), all four LED channels driven like in the app; a colour from the
  colour wheel is matched to the closest palette colour.
- Mode select (schedule, manual, demo, off), colour select, intensity, "Keep manual mode on"
  switch, "Resume schedule" button.
- Sensors: schedule level now (schedule points in attributes), Wi-Fi signal, lamp clock.
- Lovelace card `custom:skylight-lamp-card` like the manual page of SLcontrol, loaded
  automatically with the integration.
- The Wi-Fi password the lamp returns is never logged or stored.
- Brand images (icon, logo, dark variants); English and Polish translations.
