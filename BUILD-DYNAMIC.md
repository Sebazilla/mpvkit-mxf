# Replaceable macOS LGPL frameworks

The dynamic variant retains the source versions and codec configuration of
`0.41.0-mxf` (commit `f053e670846e80d451024f499ab557ec37f7a326`).
Its selected product is `MPVKit`, never `MPVKit-GPL`. This build targets macOS
11+ and retains both arm64 and x86_64 slices; RushDeck packages its host slice.
The legacy iOS/GPL build recipes are historical inputs, not the dynamic build entry.

## Build inputs and method

`tools/original-assets.json` records original GitHub asset URLs and ZIP SHA256s.
`tools/dynamic-inputs.json` records the hashes of their original universal archives.
`tools/fetch_inputs.py --destination <input-directory>` downloads those assets,
checks hashes before extraction and restricts redirects to GitHub's asset hosts.
Alternatively, the exact original, SwiftPM-verified artifact cache can be supplied
to `build_frameworks.py`; every input archive is checked against its recorded hash.
No GPL archive or OpenSSL archive is a relinker input.

GMP 6.2.1, Nettle 3.10 (including Hogweed), and GnuTLS 3.8.11 are rebuilt from
official release tarballs by `tools/gnutls/build_tls.py`. URLs and SHA256s are
constants in that script. It verifies SHA256 before using/extracting each archive.
Signature files are downloaded but NOT verified: GPG was unavailable; no keyserver
is used. These hashes were calculated from the canonical downloads, not obtained
through an independently authenticated channel.

The original GnuTLS recipe is mpvkit/gnutls-build 3.8.11 at
`e766d4e9a38b8360fc8bb61a523e7ab71b1c2303`. Its component versions are
GMP v6.2.1, Nettle nettle_3.10_release_20240616, GnuTLS 3.8.11. Release
tarballs replace Git bootstrap, retaining their generated configure, tables and
Makefile.in files. No autoreconf, gtkdocize, asn1Parser or package-manager install
is performed. Doxygen/gtk-doc/documentation, tests and CLI tools are disabled as
applicable. The library configuration retains the original included minitasn1
and Unicode/gnulib helper implementation, compression/IDN/p11-kit exclusions and
hardware-acceleration option. The old generated-Makefile assembler workaround is
not needed for the successful release-tarball build. Shared replaces static;
PIC and macOS 11 deployment are retained. Architecture/compiler flags follow
the original recipe without adding an optimization setting; only the SDK path
follows the installed Xcode. The original GMP header records Xcode 16.4/SDK 15.5;
the actual build toolchain is recorded with the validation evidence. GnuTLS C++ wrapper/tools are not shipped.

FFmpeg is rebuilt as shared from n8.1: the original static archives contain
private ff_* symbols that cannot resolve across separate dylibs. The original
configuration for each architecture is extracted from its own avutil archive
and recorded in tools/ffmpeg-configs.json. build_ffmpeg.py changes only output
linkage/install paths and supplies local dependency metadata; it retains codec,
MXF, licensing and per-architecture options, plus the original two VideoToolbox
macro substitutions. MoltenVK's original 1.4.1 header SDK is SHA256-pinned in
the script. The generated configuration-delta.json records old/new arguments.

The libbluray archive also contains libudfread 1.2.0. Its four embedded objects
(default_blockinput.c.o, ecma167.c.o, udfread.c.o, udfread-version.c.o) are removed
from libbluray. Their original embed-mode visibility is private, so libudfread
is rebuilt separately from the exact bundled source in the SHA256-pinned official
libbluray 1.4.0 tarball, with embed_udfread=false/default_library=shared. Public
API export visibility is the required change; source version/code are unchanged.
Meson uses an explicit cross file, a local prefix, no examples, no downloads and
no executable wrapper (including for x86_64, avoiding any Rosetta prompt).

Other LGPL libraries (mpv, libbluray, FriBidi, uchardet, libplacebo) are dynamically
relinked from the exact PIC object archives of 0.41.0-mxf, rather than reconfiguring
their sources. Thus the MXF flags, mpv
`-Dgpl=false`, patches and enabled decoders are preserved. Every library gets its
own Mach-O dylib/framework; dependencies on other LGPL libraries bind to their
dynamic frameworks. Permissive dependency archives resolve only needed symbols.
The relinker does not use undefined-dynamic-lookup or an umbrella dylib containing
all LGPL components. Install names are `@rpath/Name.framework/Name`. Framework
layout is normalized to Versions/A, with minimum-system metadata corrected from
the static wrapper's placeholder to 11.0. Libraries are individually ad-hoc signed.

The original FFmpeg configuration contains `--enable-nonfree` and a generated
`FFMPEG_LICENSE` string of `nonfree and unredistributable`. This is pre-existing
and deliberately not silently changed by an object-code relink. No `--enable-gpl`
is added and no GPL target is linked. This document describes technical provenance;
it makes no legal/distribution-clearance claim. Corresponding source is FFmpeg
n8.1 at `9047fa1b084f76b1b4d065af2d743df1b40dfb56`; the original MXF configuration
is in Sources/BuildScripts/XCFrameworkBuild/main.swift. mpv v0.41.0 is
`41f6a645068483470267271e1d09966ca3b9f413`, with the two patches under
Sources/BuildScripts/patch/libmpv retained verbatim.

## Dedicated M3 build

Build only in `/Volumes/4M2/Dev/rushdeck/mpvkit-dyn/`, with this checkout as
`source/`. No global installation and no GUI. A fresh reproduction uses fresh
prefix, tls-build and framework-stage directories. Installed-source markers are
only local resume points; do not reuse them after changing configuration/compiler.
Keep all logs outside this repository in WP-LGPL-measurements.

Run `python3 source/tools/gnutls/wait_for_m3.py` before each build/gate/smoke.
It waits in 120-second intervals, up to 180 minutes, without signalling any other
process. A deploy/merge gate takes priority. Set RUSHDECK_CATALOG_DIR to a fresh
temporary directory for every binary invocation. Run build commands with nice 10.

For each `arm64` and `x86_64`, run from the dedicated root:

```
python3 source/tools/gnutls/build_tls.py --root /Volumes/4M2/Dev/rushdeck/mpvkit-dyn --arch <arch>
python3 source/tools/build_ffmpeg.py --root /Volumes/4M2/Dev/rushdeck/mpvkit-dyn --artifacts <input-directory> --arch <arch>
python3 source/tools/build_frameworks.py --root /Volumes/4M2/Dev/rushdeck/mpvkit-dyn --artifacts <input-directory> --arch <arch> --resume
```

The FFmpeg driver fetches/checks the pinned MoltenVK SDK and prepares the foundation frameworks before configuring FFmpeg. Then combine with the same build_frameworks invocation plus `--combine`.
It produces Dynamic/Name.xcframework, each containing one universal macOS slice.
The files are local SwiftPM binary targets pinned by the fork's immutable Git tag;
no new GitHub Release or external binary hosting is used.

## Component assignment

| Component | Handling | Reason |
|---|---|---|
| mpv 0.41.0, two original patches | Dynamic Libmpv | LGPL build, gpl=false |
| FFmpeg n8.1, original MXF config | Separate dynamic Libavcodec, Libavdevice, Libavfilter, Libavformat, Libavutil, Libswresample, Libswscale | LGPL code must not reside in the app executable |
| GnuTLS 3.8.11 | Dynamic gnutls | LGPL library, including its internal minitasn1/Unicode helper implementation |
| GMP 6.2.1 | Dynamic gmp | LGPL branch of dual licence |
| Nettle 3.10 | Separate dynamic nettle and hogweed | LGPL branch of dual licence |
| libbluray 1.4.0 | Dynamic Libbluray, without bundled UDF objects | LGPL |
| libudfread 1.2.0 | Dynamic Libudfread, built from the bundled official source | LGPL-2.1-or-later; independently replaceable |
| FriBidi 1.0.12 | Dynamic Libfribidi | LGPL; version read from original header |
| libplacebo 7.360.1 | Dynamic Libplacebo | LGPL |
| uchardet 0.0.8 | Dynamic Libuchardet | Conservatively treats LGPL branch of MPL/GPL/LGPL tri-licence dynamically |
| libass 0.17.4 | Static where referenced | ISC |
| FreeType 2.12.1 (original libass asset) | Static where referenced | FreeType licence branch of dual licence |
| HarfBuzz 8.1.1 (original libass asset) | Static where referenced | MIT |
| libunibreak (original libass asset) | Static where referenced | zlib-style permissive licence; exact binary hash pinned |
| dav1d 1.5.2 | Static where referenced | BSD |
| LuaJIT (original 2.1.0-xcode asset) | Static where referenced | MIT; exact snapshot archive hash pinned |
| libuavs3d 1.2.1-xcode | Static where referenced | BSD |
| libdovi 3.3.2 | Static where referenced | MIT, dolby_vision Cargo.toml at libdovi-3.3.2 |
| lcms2 2.17.0 | Static where referenced | MIT |
| MoltenVK 1.4.1 | Dynamic MoltenVK.framework | Apache-2.0; one Vulkan implementation shared across mpv/libplacebo/FFmpeg, avoiding duplicated loader state |
| shaderc_combined 2025.5.0 | Static where referenced | Apache-2.0/BSD dependency code |
| OpenSSL, smbclient, GPL variants | Not relinker inputs | Not linked by the selected original LGPL configuration |
| _MPVKit/_FFmpeg wrappers | Empty original SwiftPM wrapper targets | No LGPL implementation symbols |

Licence/notice texts for LGPL components are under Licenses/ and must be copied
into the app. Replacement, decode and app-signature verification are performed
by RushDeck's WP-LGPL checks, independently of creating these artifacts.

## Marked replacement build

After the unmarked arm64 build, run tools/build_marked_avutil.py with --root.
It creates independent source/build copies under replacement-build, modifies only
av_version_info() to append WP-LGPL-SWAP-20261030 and rebuilds Libavutil with the
existing shared configuration. It never installs over the baseline prefix and
asserts equality of the exported symbol set before signing the replacement.
RushDeck's tools/smoke/lgpl_swap.py uses this framework only in a fresh temporary
app copy and verifies the marker, decode and unchanged original build framework.
