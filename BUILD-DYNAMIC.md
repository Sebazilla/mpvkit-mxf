# Replaceable macOS frameworks — WP-CVE3 dyn5 candidate

Only GMP changes version: 6.3.0 from the official GNU archive, SHA256 a3c2b80201b89e68616f4ad30bc66aee4927c3ce50e33929ca819d5c43538898. The coordinator independently verified the detached signature; the implementer makes no GPG-verification claim.

With the cve3 M3 gate lock held, run `/usr/bin/python3 tools/cve3/build_all.py`. It requires an absent `/Volumes/4M2/Dev/rushdeck/tmp/cve3/dyn5` root and verified offline sources under tmp/cve3/sources. Historical cve2 drivers and the dyn4 tag remain unchanged. GMP, Nettle/Hogweed, GnuTLS, FFmpeg, mpv, libplacebo and the retained-archive framework link steps run freshly. MoltenVK frameworks and static HarfBuzz 15.0.0 are explicit retained inputs bound to dyn4; unchanged original PIC archives and verified tools are retained inputs, not a claim of rebuilding every upstream library.

Both architectures keep existing versions/features/macOS deployment and patches except GMP. New root names are explicit in guards and source/header selection. No source fallback is permitted. Publication is separate: no tag/push/pin until coordinator review of G3, local verified TLS roundtrip (both dyn4/dyn5), and isolated durable-root relink with 18 binary hashes. dyn4 had a library-load/version check, not a TLS handshake proof. Runtime claims cover arm64 only; no GUI/MoltenVK render-quality or x86_64-runtime claim.

The durable root is `/Volumes/4M2/Dev/rushdeck/mpvkit-dyn5`. Relink portability is pending measured proof; no exact invocation claim is made yet. New fork objects are independent, without Git alternates. Historical dyn4/source still depends on dyn2/source objects through alternates; neither historical root is modified.

Historical dyn4 recipe and limitations: BUILD-DYNAMIC-DYN4.md.
