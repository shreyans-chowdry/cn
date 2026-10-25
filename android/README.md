# ScamShield for Android

Reads every incoming SMS, checks it on the phone, and posts a notification when it looks like a UPI scam.
Works on English and code-mixed messages in any supported script (currently Hindi–English and Tamil–English). The language is detected automatically.

## Install (no build needed)

1. Copy `ScamShield.apk` (in the repository root, `releases/ScamShield.apk`) to the phone.
2. Open it and allow installing from this source (Android asks once).
3. Open ScamShield and tap **Turn on protection**. Allow SMS and notifications.

Minimum Android 8.0 (API 26).

## Demo without waiting for a real scam SMS

* **Check** tab → tap a sample (for example *Code-mixed scam*) → **Simulate as incoming SMS**. This runs exactly
  the same path as a real SMS: the message is classified, saved to Messages, and a notification appears.
* Send an SMS from another phone, for example
  `உங்கள் SBI account இன்று block செய்யப்படும். உடனே KYC update செய்ய link-ஐ click செய்யவும் http://sbi-kyc-update.xyz/a9`
* On an emulator: *Extended controls → Phone → SMS*.
* From any messaging app: long-press a message → **Share** → ScamShield.

## Server mode (the networking part)

1. On the laptop: `./run_demo.sh` (starts the web app and the ScamShield protocol server on TCP 9099).
2. Phone and laptop on the same Wi-Fi. In the app, open **Network**, enter the laptop's IP (it is shown on the
   web app's Network tab), port 9099, then **Save and test**. You should see the round-trip time.
3. Turn on **Use server mode**. Each SMS is now sent as an SSP frame (16-byte header, JSON, CRC-32) over TCP. The
   Network tab shows the last request frame field by field. If the server cannot be reached, the phone falls back
   to on-device checking.

## Build from source

Android Studio (Koala or newer): *Open* → this `android/` folder → Run. Or from the command line:

```bash
cd android
./gradlew assembleRelease          # app/build/outputs/apk/release/app-release.apk
./gradlew testDebugUnitTest        # parity test: Kotlin model == Python model on 300 messages
```

The model file `app/src/main/assets/model.json` and the test fixtures are written by
`python scripts/train_production.py` in the repository root.

## Why Android and not iOS

iOS does not let apps read incoming SMS. Apple only allows a Message Filter extension that sorts messages from
unknown senders into folders; it cannot show its own notification, and installing it needs a Mac with Xcode and a paid
developer account. Android lets an app receive every SMS (`RECEIVE_SMS`), and an APK can be installed directly
on any phone.

Note: Google Play restricts the SMS permission to default SMS apps, so this app is distributed as an APK
(sideloaded), which is normal for a research prototype.
