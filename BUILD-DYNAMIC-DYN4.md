# Replaceable macOS LGPL frameworks — WP-CVE2

Use the MPVKit product, never MPVKit-GPL. Historical dyn/dyn2/dyn3 records are retained in BUILD-DYNAMIC-HISTORY.md.


The selected MPVKit product updates mpv to v0.42.0 (b0841e8c4d156b8403dc1876c4cbd9011eb583f3), FFmpeg to 8.1.3 (1041abdc962f4cc4f394aa8de9dc5236c0c3b9e7), libplacebo to v7.387.0 (275f7dea27924cdd34ab2e6c20e448b6bc4fab65), and HarfBuzz to 15.0.0 (35f656a1a2bab548ea7f54a6dd3fba2b09680d14). tools/cve2-sources.json binds the approved official archives and all six recursive libplacebo gitlinks to SHA256, extracted paths and exact patched-member hashes. Full updated source licence/notice texts are retained under Licenses/CVE2 and current component licence directories. The coordinator independently verified the FFmpeg release signature; these build drivers make no GPG-verification claim. The legacy Swift platform recipes above describe historical inputs and are not the CVE2 entry point.

Hold the mpvlgpl M3 gate lock. The final reproduction entry is:

```
/usr/bin/python3 tools/cve2/build_all.py
```

It requires an absent /Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final root, the approved offline archives under /Volumes/4M2/Dev/rushdeck/tmp/cve2/sources, and the unchanged SHA-verified original ZIP/tool inputs in the retained cve1-dyn3 cache. It refuses an existing build root. No completed prefix, TLS/FFmpeg/mpv/libplacebo/HarfBuzz build, or dynamic framework from dyn3/dyn4 is reused. The unchanged permissive/retained-library PIC archives are explicit original inputs, not a claim to rebuild every upstream dependency from source. Existing pinned build tools/SDL, Xcode and SDK remain toolchain inputs; this is not a hermetic toolchain bootstrap.

prepare.py creates fresh source/build/staging trees, checks tar paths and hashes, applies both original mpv patches cleanly and exactly the two original FFmpeg VideoToolbox substitutions, and verifies extracted member bytes. GnuTLS/GMP/Nettle retain versions and flags. HarfBuzz is static PIC for both architectures, with wasm/glib/gobject/freetype/ICU/CoreText disabled; utilities/tests/docs/subset/raster/vector/GPU helpers are disabled. Its new universal static XCFramework and 15.0.0 headers are a local Static/Libharfbuzz target, independently of the old cached 14.2.0 template. Other text versions remain libass 0.17.5, FreeType 2.14.3, FriBidi 1.0.16 and libunibreak 6.1.

Base foundations (including MoltenVK) are freshly staged before libplacebo. libplacebo links this fresh MoltenVK and the pinned shaderc/lcms2/libdovi PIC inputs. Its generated feature variables/pkg-config metadata are preserved. System Python is explicit for its XML generation; bundled pinned jinja/markupsafe/glad supply generator modules. Vulkan/OpenGL, shaderc, LCMS and DOVI are retained; glslang, D3D11 and xxhash are disabled as before.

FFmpeg keeps original per-architecture codec/MXF configure arguments, --disable-gpl --disable-nonfree --enable-version3, shared linkage and macOS 11 deployment. mpv is compiled from source with both original fork patches, shared linkage, gpl=false, explicit original features and no curl/DVD/CDDA/subrandr or other new optional host providers. LuaJIT remains compiled; this does not claim scripting is absent. Objective-C and C/C++ cross flags explicitly bind architecture and SDK. The canonical public mpv headers remain nested under Headers/mpv and report API 2.6.

The final build produces 18 separately replaceable dynamic frameworks, both arm64 and x86_64 slices, and the new static HarfBuzz artifact. Prior local candidate artifacts are preserved under dyn4/pre-final-artifacts before final outputs replace the working tree's artifact directories. Publishing is a separate operation: only final-run artifacts may be committed/tagged after all external acceptance evidence is green. Never move an existing tag.

Acceptance evidence must include old/new synthetic decode digests, headless hwdec=auto-safe decoder choice, all architecture/header/symbol/load/signature/size/feature comparisons, native code-owner version APIs, lgpl_check --release and strict whole-probe codesign. The libplacebo public log-constructor guard follows API 387 (pl_log_create_387), with no compatibility alias for API 360. Runtime claims are native arm64 only; x86_64 is build/static/signature inspection only. vo=null is not a GUI/MoltenVK render-quality proof. No new portable byte-reproducibility claim is made. The first local candidate's results do not substitute for the required fresh final-run evidence.
