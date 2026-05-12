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

LGPL-3.0-or-later, identical to upstream MPVKit. Built without `--enable-gpl`,
so consumers can dynamically link it from a closed-source app under the LGPL
re-link clause. The bundled FFmpeg / libmpv / libplacebo / libass / libbluray
pull in their respective LGPL/permissive licenses — see upstream
`LICENSE` and the copyright notices inside each xcframework.

## Versioning

`0.41.0-mxf` matches upstream `0.41.0` plus the demuxer flag. When upstream
ships `0.42.0`, this repo will rebase to `0.42.0-mxf`.

## Building from source (optional)

```bash
make build platform=macos
```

Output xcframeworks land in `dist/release/`. The published GitHub Release
assets are the same zips, hashed for SwiftPM `binaryTarget(checksum:)`.
