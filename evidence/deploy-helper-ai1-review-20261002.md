# Recovery helper review — AI1, 2026-10-02

Scope: review of AI2's `2d53d67` recovery helpers, followed by local checks using
dummy credentials and mocked X input. These checks do not claim an ARM host,
real keyboard, Matrix login, or MiniMax round was executed by AI1.

Changes:

- Pass private input to `xtype --stdin`; do not put its value in process arguments
  or print its first/last characters. Reject an unmappable character before any
  key events are sent; return a failure instead of silently entering a partial value.
- Merge provider configuration while preserving existing tool policy, fallbacks,
  other environment entries, envelope metadata, and unknown fields.
- Write the exact key bytes, without an added newline, using an atomic private
  secrets file. On the pinned Linux host this is a plaintext file protected by
  permissions, not encrypted ciphertext.

Local verification:

| Check | Actual result |
| --- | --- |
| Mocked private input transport | Secret absent from argv/stdout; present only in stdin input |
| Mocked unsupported-key case | Failure returned; zero X key events; no secret text printed |
| Dummy provider merge and dry-run | Existing policy/fallbacks/other values preserved; dry-run changed no files |
| Native file contract | Exact key bytes with no extra newline; files 0600; no leftover temporary key file |
| Python helpers | All helper sources compile successfully |

Pinned source for the file contract:
[SecretsDir](https://github.com/OctoSense-org/OctoSense/blob/6c4746f0854b74446f854fdcd32eeb87b5192a81/apps/ai-providers/host-service/src/vault.rs)
reads the file verbatim and writes `secret.as_bytes()`;
[profile merge](https://github.com/OctoSense-org/OctoSense/blob/6c4746f0854b74446f854fdcd32eeb87b5192a81/apps/ai-providers/config/src/profile.rs)
preserves unrelated settings.

Still required: AI2's real X input check, private key-file equality check, and the
actual OnCue model round. A configured profile or running core is not a model result.

## Health checks follow-up

The former health script accepted any listener on the noVNC port even when its recorded websockify identity failed. It also accepted any `wm: launched` log line. The updated script requires the recorded websockify process identity, the expected loopback listener, and an HTTP 200 page. It reads the current verified host process's `--test-action` argument and requires a log line for exactly that launched app, so a shell default cannot override a prior `start --launch` choice.

AI1 ran four dummy cases with mocked process command-line input, X, listener and HTTP tools: a different launched app fails; a prefix-only app-name match fails; an unrelated listener with HTTP 200 fails identity; the expected app with valid identity/listener/HTTP 200 passes. `bash -n` and `git diff --check` pass. This sandbox cannot read the dummy subprocess's `/proc` entry; the command-line source was redirected to a temporary fixture only in the test copy. This is script logic validation, not a real ARM host restart or noVNC connection test. AI2 must run the updated script against its current runtime.
