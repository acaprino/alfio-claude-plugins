# Client-Server Architecture

The separation-of-concerns principle applies universally: **clients handle presentation; servers enforce truth**. UI rendering, form hints, navigation, and display logic belong on the client. Pricing calculations, discount rules, eligibility checks, workflow orchestration, and all authorization decisions belong on the server.

## MUST

- **Never place authorization or business-rule enforcement solely on the client.** All client platforms are reverse-engineerable. JavaScript in SPAs/PWAs is fully readable; mobile APKs can be decompiled; Electron apps bundle readable Node.js code.

## DO

- Use a **Backend-for-Frontend (BFF) pattern** when different platforms need different data shapes, rather than duplicating business logic across clients.
- For desktop apps, treat the renderer process as untrusted and route all sensitive operations through the main/core process that communicates with the server.

## DON'T

- Duplicate business logic across SPA, mobile, and desktop clients. Consistency bugs emerge when pricing or eligibility rules diverge between platforms.
- Trust client-computed values without server re-validation.
