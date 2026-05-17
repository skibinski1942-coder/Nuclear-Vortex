# Privacy Policy — Achilles AI Assistant

**Effective Date:** May 17, 2026  
**Last Updated:** May 17, 2026  
**Publisher:** Nuclear-Vortex / Skibinski Holdings and Trust

---

## 1. Overview

This Privacy Policy explains how **Achilles AI** ("the App", "we", "us") collects, uses, and protects information when you use the Achilles AI Assistant mobile application. We are committed to protecting your privacy and being fully transparent about our data practices.

---

## 2. Information We Collect

### 2.1 Information You Provide
- **Chat messages** — text you send to the Achilles assistant during a conversation session.
- **Server URL** — the address of your Achilles backend server, entered in Settings.

### 2.2 Information Collected Automatically
- **Session identifiers** — randomly generated UUIDs created locally on your device to maintain conversation context within a session. These are not linked to your identity.
- **App crash data** — if you have enabled crash reporting on your device (via Android system settings), your device manufacturer or Google may collect crash diagnostics. We do not independently collect crash data.

### 2.3 Information We Do NOT Collect
- We do **not** collect your name, email address, phone number, or any other personally identifiable information.
- We do **not** access your device's microphone, camera, contacts, location, or storage unless you explicitly grant such permission for a future feature.
- We do **not** use advertising trackers or analytics SDKs.
- We do **not** sell your data to third parties — ever.

---

## 3. How We Use Your Information

| Data | Purpose |
|------|---------|
| Chat messages | Sent to your configured Achilles backend server to generate responses. Messages are processed in real time and not stored by the App beyond the active session. |
| Server URL | Used solely to direct API requests. Stored locally on-device in Android SharedPreferences. |
| Session ID | Used to maintain conversation context during a single session. Discarded when the session ends or the App is closed. |

---

## 4. Data Storage and Retention

All data processed by the App is either:
- **Transient** — held only in memory during an active session and discarded when you close the App, or
- **Stored locally on your device** — e.g., your preferred server URL in SharedPreferences, which you can clear at any time via Android Settings → Apps → Achilles AI → Clear Data.

**We do not operate our own cloud servers.** The App communicates exclusively with the Achilles backend server you configure. The privacy practices of that server are determined by wherever and by whomever you deploy it.

---

## 5. Third-Party Services

The App uses the following open-source libraries, which operate entirely on-device and do not independently transmit data:

| Library | Purpose | Privacy Policy |
|---------|---------|----------------|
| OkHttp (Square) | HTTP networking | [square.github.io/okhttp](https://square.github.io/okhttp/) |
| Retrofit (Square) | REST API client | [square.github.io/retrofit](https://square.github.io/retrofit/) |
| Gson (Google) | JSON parsing | Apache 2.0, no data collection |

The App does **not** include Google Analytics, Firebase, Facebook SDK, Crashlytics, or any other analytics or advertising framework.

---

## 6. Children's Privacy

Achilles AI is not directed at children under the age of 13. We do not knowingly collect personal information from children. If you believe a child has provided personal information through the App, please contact us at the address below and we will take prompt action to delete it.

---

## 7. Security

We implement reasonable technical safeguards:
- All network communication uses HTTPS (TLS 1.2+) for production deployments.
- Cleartext (HTTP) traffic is only permitted to `localhost` and `10.0.2.2` (Android emulator) during development.
- No credentials or sensitive tokens are stored in the App.

Despite these measures, no system is 100% secure. You are responsible for securing your own Achilles backend server.

---

## 8. Your Rights

Depending on your jurisdiction, you may have the right to:
- **Access** personal data we hold about you.
- **Delete** personal data we hold about you.
- **Correct** inaccurate personal data.

Because the App stores no personal data on our servers, these rights are primarily exercised by clearing App data on your device (Settings → Apps → Achilles AI → Clear Data).

For questions or requests, contact us at: **privacy@nuclear-vortex.dev**

---

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of material changes by updating the "Last Updated" date above. Your continued use of the App after any change constitutes acceptance of the updated policy.

---

## 10. Contact Us

**Nuclear-Vortex / Skibinski Holdings and Trust**  
Email: privacy@nuclear-vortex.dev  
GitHub: https://github.com/skibinski1942-coder/Nuclear-Vortex

---

*This Privacy Policy was created for the Achilles AI Android application published on the Google Play Store.*
