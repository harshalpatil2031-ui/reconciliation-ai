# Farmer PWA scaffold

This is the isolated P2-04 waiting-time implementation. It provides a Marathi-first structured form, camera/orientation/geolocation UI, browser-side signatures, IndexedDB queue, and an installable Vite PWA shell. It does not implement the server-side photo verifier or ground API.

## Local use

Use Node.js 20 or newer.

```sh
npm install
npm run dev
```

Open the Vite URL with the case link parameters `?case=<case-id>&t=<token>`. The default API is `http://localhost:8000`; set `VITE_API_URL` to point at another local API. The current backend ground route is still a Stage 2 stub (HTTP 501), so submissions remain queued until the P2 service endpoint is implemented.

Camera and location require a secure browser context (localhost is permitted). Sensor and compass behavior still needs the device field checks listed in [`FIELD_TEST.md`](FIELD_TEST.md). The optional gallery input is only rendered with `?mode=gallery` and is marked `in_app_capture: false`.

Client signatures are deterministic upload identifiers, not authentication or device attestation. The URL token is held in memory while the app is open and is persisted with an offline queued bundle so it can retry after the device reconnects.

## Not yet complete

- Ground API, database writes, server-side idempotency, photo verification, and real case-context integration.
- Optional voice-note capture and transcription.
- Device compass field calibration and native-speaker review of Marathi strings.
- Licensed real-photo collection and demo bundle attribution; see the root [`ATTRIBUTION.md`](../ATTRIBUTION.md).
- End-to-end offline upload acceptance on a phone.
