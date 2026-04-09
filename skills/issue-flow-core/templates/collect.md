# Collect: {{case_id}}

## Issue Context

Playback does not recover after audio focus changes.

## Evidence References

- `/tmp/audio-focus-bug/player.log` — Application log from the failed repro run
- `/tmp/audio-focus-bug/screenshot.png` — UI screenshot captured during the failure
- `/Users/shenyeke01/Downloads/bug-report.zip` — Original archive; inspect or extract in place if needed

## Code References

- `biz/player/src/main/java/com/netease/music/iot/player/CarAudioFocusManager.kt` — User suspects this code path is involved

## What's Missing

- Additional device-side logs if the app log alone is insufficient

## Next

Evidence references registered. Ready for investigation.
