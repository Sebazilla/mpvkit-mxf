# MPVKit-MXF

A minimal fork of [mpvkit/MPVKit](https://github.com/mpvkit/MPVKit) v0.41.0 that
re-enables the FFmpeg MXF demuxer.

## Why this fork exists

Upstream MPVKit ships an LGPL libavformat with `--disable-demuxers` followed by
an explicit allowlist that **omits MXF**, to keep the binary ~150 KB smaller.
That breaks playback of every Canon Cinema EOS clip (XF-AVC inside MXF) and
Sony XDCAM/XAVC MXFs. Our consumer ([RushDeck](https://github.com/Sebazilla/tapedeck-swift),
private) is a video editor for cinema shooters where MXF is mandatory, so we
re-enable the demuxer.

The single source change vs upstream:

```diff
+ "--enable-demuxer=mxf", "--enable-demuxer=mxf_d10", "--enable-demuxer=mxf_opatom",
```

at `Sources/BuildScripts/XCFrameworkBuild/main.swift`. Everything else —
mpv version, libplacebo, hwdec, the whole xcframework topology — matches
upstream verbatim. Track upstream releases by rebasing this fork.

## License

LGPL-3.0-or-later for the MPVKit wrapper/build material, as declared upstream.
The component sources carry their own LGPL/permissive licences; full LGPL
texts/notices for the dynamic variant are under Licenses/. This is technical
provenance, not legal distribution clearance. In particular, the original
FFmpeg --enable-nonfree setting and generated licence string belong to the
historical provenance in [BUILD-DYNAMIC-HISTORY.md](BUILD-DYNAMIC-HISTORY.md).
The current dyn6 configuration disables nonfree and GPL; see
[BUILD-DYNAMIC.md](BUILD-DYNAMIC.md) for the current build and limits, and
[BUILD-DYNAMIC-DYN4.md](BUILD-DYNAMIC-DYN4.md) for the intervening source updates.

## Versioning

`0.41.0-mxf` matches upstream `0.41.0` plus the demuxer flag. When upstream
ships `0.42.0`, this repo will rebase to `0.42.0-mxf`.

## Building from source (optional)

```bash
make build platform=macos
```

Output xcframeworks land in `dist/release/`. The published GitHub Release
assets are the same zips, hashed for SwiftPM `binaryTarget(checksum:)`.

## WP-LGPL dynamic macOS variant

The original 0.41.0-mxf assets were static archives. The dynamic variant and its
pinned build inputs, source-tarball route, component licences, architecture scope
and technical limitations are documented in [BUILD-DYNAMIC.md](BUILD-DYNAMIC.md).
Use that build entry instead of the legacy make/Git-bootstrap instructions above.
No legal distribution clearance is implied.
