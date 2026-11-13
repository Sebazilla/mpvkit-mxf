# MPVKit dyn6 dynamic macOS frameworks

Versions and source hashes are unchanged from dyn5. Fourteen frameworks are compiled from release sources; FriBidi, uchardet and libbluray are freshly linked from pinned PIC archives. MoltenVK, HarfBuzz 15 and the permissive archives remain individually hashed retained inputs. Their complete source-to-object correspondence has not been newly established. Historical provenance is retained in [BUILD-DYNAMIC-HISTORY.md](BUILD-DYNAMIC-HISTORY.md), [BUILD-DYNAMIC-DYN4.md](BUILD-DYNAMIC-DYN4.md), and [BUILD-DYNAMIC-HISTORICAL-ADDENDUM.md](BUILD-DYNAMIC-HISTORICAL-ADDENDUM.md); it is not asserted as current validation. The original static FFmpeg input enabled nonfree and reported a nonfree licence string, as described in HISTORY. The current shared build retains `--disable-nonfree`, `--disable-gpl`, and `--enable-version3`. Historical instructions require the corresponding historical tag; the current root guards reject their old roots.

## Source build and exact recipe

The round-2 source build root is `/Volumes/4M2/Dev/rushdeck/tmp/fork6/round2-build`; its independent durable derivation is `/Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2`. These recipes deliberately reject dyn2–dyn5 roots. Their original tags remain authoritative for historical builds and relinks. `tools/fork6/prepare.py` only describes copying an existing verified fork6 cache; it was not executed to prepare the measured round-2 build. Preparation was performed outside the fork, including the cross-file additions described below. Root-relative tool manifests must match the actual prepared tools. No prior TLS, FFmpeg, placebo or mpv build output was copied as a source-build input.

The cache contains the SHA256-verified release archives and their extracted sources. Its source preparation follows the historical method recorded in `tools/cve3/prepare.py`: extract the archives under their recorded targets, apply the two patches in `Sources/BuildScripts/patch/libmpv` to mpv 0.42.0, and replace exactly `kCVPixelBufferOpenGLESCompatibilityKey` and `kCVPixelBufferIOSurfaceOpenGLTextureCompatibilityKey` with `kCVPixelBufferMetalCompatibilityKey` in FFmpeg's `libavcodec/videotoolbox.c`. Recursive libplacebo sources use the pinned archive members. `tools/cve2-sources.json` binds the archive hashes, extraction targets and exact patched/added member hashes; `verify_cve3.verify_sources` checks those members during the build. Original ZIP/member checks and the TLS release-tarball checks are separate. The historical preparation script is a description of cache origin, not a supported dyn6 entry point.

Run `/usr/bin/nice -n 10 /usr/bin/python3 -B source/tools/fork6/build_all.py all` with `FORK6_BUILD_ROOT` set to the source-build root. All phases and architectures run serially, make/Meson use `-j2`. This single pass produces `framework-stage/{arm64,x86_64,universal}` and `candidate-Dynamic`. FFmpeg uses `ffmpeg-build`, mpv `mpv-build` and `mpv-prefix`; there are no v3/v4 path substitutions after building. The recipe was committed before the measured pass; artifact commit `457044307367d509b079c38e980d5206743012a4` has the identical recipe blobs and a single parent, dyn5 c920cef. Later documentation-only commits do not change those recipe or artifact blobs. The pre-build recipe snapshot is retained locally for provenance.

GnuTLS has an empty system-priority-file configure argument (`DISABLE_SYSTEM_CONFIG=1`); its sysconfdir/localedir and mpv's actual MPV_CONFDIR lie under `/System/Library/RushDeck-Disabled`. No such directories are created. Upstream `GNUTLS_SYSTEM_PRIORITY_FILE` environment handling is unchanged. On ordinary customer systems the previous build-root config path did not exist. Synthetic decode/headless comparisons test that case, not manually configured developer machines.

All fresh source compilations receive prefix maps. GMP receives its file-prefix map through CPPFLAGS, so generated `__GMP_CFLAGS` does not embed the root. The committed TLS recipe (`tools/gnutls/build_tls.py`) and FFmpeg recipe (`tools/build_ffmpeg.py`) explicitly pass `-Wl,-oso_prefix,<build-root>/`. In the measured build, libplacebo and libmpv also received that option through the prepared `harfbuzz-<arch>.ini` cross files, inherited by their own cross files. Those flags were added by preparation outside the fork, not by `tools/fork6/prepare.py`; the latter is therefore not a complete recipe for reproducing the measured prepared cache. Libudfread was linked without the option.

Measured TLS N_OSO entries are relative and their counts are unchanged (Nettle 240, Hogweed 146 per slice), so the debug maps are preserved. The review measured no debug entries in Libplacebo/Libudfread and only one N_AST reference in Libmpv. From that absence of relevant entries, no binary effect from the cross-file option difference is inferred for those libraries; a second build via `tools/fork6/prepare.py` was not run to prove that inference. Libplacebo and Libudfread were measured byte-identical to dyn5. The relative N_OSO treatment does not remove Libmpv's N_AST reference. No shipped binary is subsequently stripped or edited to remove strings. Install-name rewriting and ad-hoc signing are framework assembly operations as before. The three retained-PIC framework links keep the dyn5 arguments: no absolute N_OSO root was present, and libbluray must retain its dyn5 bytes.

The four TLS binaries have measured zero whole-slice byte occurrences of the volume-root, user-home and Homebrew path prefixes. Inventories include both section-oriented `strings -arch` and complete byte counts, also covering `/usr/local/` and `/etc/`; section-only counts cannot establish absence of debug-map paths. FFmpeg configuration argv and mpv option strings are build provenance and intentionally retain actual build paths. FFmpeg `Headers/config.h` carries that same configuration and the header-only FFMPEG_DATADIR; generated files are not hand edited. Libmpv may retain its Swift N_AST debug-module reference, which is inventoried separately.

## Bound tools and durable derivation

The root-relative tool manifest and separate host payload manifest are verified during source building. Host binding covers the fixed Python 3.14 interpreter/framework, non-test standard-library source and native extensions, Meson source modules, tool executables and their transitive absolute Homebrew dylib dependencies. The prepared Meson wrapper requests disabled bytecode reads through a protected, absent pycache prefix and `-B`, also for its re-invocations; absence of bytecode reads was not independently traced. The host manifest binds 908 files; `.pyc`, standard-library test data, documentation and unused GUI/tooling modules are excluded. The PATH contains only the copied tools and macOS system tools. Apple SDK/compiler and system Python remain host prerequisites; this is a bound M3 toolchain, not a hermetic fresh-machine reconstruction.

`tools/fork6/derive_durable.py BUILD_ROOT NEW_DURABLE_ROOT` copies the committed source and the explicit input/output-prefix list, including the relative ffmpeg-source link. It converts links into relative internal links and rebases active `.pc`, `.la`, and cross `.ini` metadata only in the new copy. The derivation enumerates every rewritten file and link; the measured round-2 derivation rebased 110 active metadata files. Original ZIP payloads stay byte exact; compiler logs, generated config headers and binaries retain their actual build provenance. Probe files and synthetic private keys are excluded.

`tools/fork6/record_relink_inputs.py BUILD_ROOT` records the framework templates, actual shared/PIC/header inputs and libbluray source verification payload used by framework assembly. Relink verification uses that manifest, not Meson/Python 3.14/Ninja/NASM/pkgconf or the source-build host manifest. The relink uses system Python and Apple linker/SDK/signing tools.

## Independent relink: exact root, commands and sandbox

The measured durable root is `/Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2`, not its parent `mpvkit-dyn6`. Round-1 output remains beside `round2` and is not part of this root. The profile below does not deny those sibling round-1 directories. Independence from them follows from root-relative input-path validation, the 2,120-file hash manifest, and inspection of active metadata and command arguments, not from a sandbox prohibition on the siblings. The source offer and its default relink root must use the full `round2` path.

The measured child invocations, from the durable root, were the following (with the environment shown below). This is framework assembly with three PIC links, not another upstream source compilation:

```sh
/usr/bin/nice -n 10 /usr/bin/python3 -B /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/source/tools/build_frameworks.py --root /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2 --artifacts /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/verified-inputs --arch arm64
/usr/bin/nice -n 10 /usr/bin/python3 -B /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/source/tools/build_frameworks.py --root /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2 --artifacts /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/verified-inputs --arch x86_64
/usr/bin/nice -n 10 /usr/bin/python3 -B /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/source/tools/build_frameworks.py --root /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2 --artifacts /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/verified-inputs --combine
```

Required environment: `FORK6_RELINK=1`, `FORK6_STAGE=relink-stage`, `FORK6_DYNAMIC=relink-Dynamic`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, `TMPDIR=/Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/relink-temp`. The caller's PATH was `/usr/bin:/bin:/usr/sbin:/sbin`. Remove inherited DYLD, GNUTLS, PYTHONPATH and PYTHONHOME overrides. Use absent staging, output and temporary directories; preserve existing results and choose fresh output names for any later repetition. The output names above identify the measured run, not permission to overwrite it.

Use the complete Seatbelt profile below as `deny-old.sb` inside the durable root, with the entire relink process tree underneath it:

```scheme
(version 1)
(allow default)
(deny file-read* file-write* (subpath "/Volumes/4M2/Dev/rushdeck/mpvkit-dyn"))
(deny file-read* file-write* (subpath "/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2"))
(deny file-read* file-write* (subpath "/Volumes/4M2/Dev/rushdeck/mpvkit-dyn4"))
(deny file-read* file-write* (subpath "/Volumes/4M2/Dev/rushdeck/mpvkit-dyn5"))
(deny file-read* file-write* (subpath "/Volumes/4M2/Dev/rushdeck/tmp"))
```

For a repetition, the following inline launcher makes the control-and-command driver explicit. First confirm the five known control files exist and are readable outside the sandbox. Missing-file errors do not establish denial. Choose absent output names and preserve all earlier outputs; the names below identify the measured run. This inline form documents the process and was not itself the retained starter of that run.

```sh
/usr/bin/sandbox-exec -f /Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2/deny-old.sb /usr/bin/python3 -B - <<'PYTHON'
from pathlib import Path
import errno, os, subprocess
root = Path('/Volumes/4M2/Dev/rushdeck/mpvkit-dyn6/round2')
assert (root / 'source/BUILD-DYNAMIC.md').read_bytes()
controls = [Path('/Volumes/4M2/Dev/rushdeck') / name / 'source/BUILD-DYNAMIC.md'
            for name in ['mpvkit-dyn', 'mpvkit-dyn2', 'mpvkit-dyn4', 'mpvkit-dyn5']]
controls.append(Path('/Volumes/4M2/Dev/rushdeck/tmp/fork6/round2-build/source/BUILD-DYNAMIC.md'))
for path in controls:
    try:
        path.read_bytes()
    except PermissionError as error:
        assert error.errno in (errno.EPERM, errno.EACCES)
    else:
        raise SystemExit('control was readable')
env = {key: value for key, value in os.environ.items()
       if not key.startswith(('DYLD_', 'GNUTLS_', 'PYTHONPATH', 'PYTHONHOME'))}
env.update(PATH='/usr/bin:/bin:/usr/sbin:/sbin', FORK6_RELINK='1',
           FORK6_STAGE='relink-stage', FORK6_DYNAMIC='relink-Dynamic',
           PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
           TMPDIR=str(root / 'relink-temp'))
for name in ['relink-stage', 'relink-Dynamic', 'relink-temp']:
    assert not (root / name).exists(), 'preserve existing output; choose a fresh name'
(root / 'relink-temp').mkdir()
for tail in [['--arch', 'arm64'], ['--arch', 'x86_64'], ['--combine']]:
    command = ['/usr/bin/nice', '-n', '10', '/usr/bin/python3', '-B',
               str(root / 'source/tools/build_frameworks.py'), '--root', str(root),
               '--artifacts', str(root / 'verified-inputs'), *tail]
    subprocess.run(command, cwd=root, env=env, check=True)
PYTHON
```

All five negative controls returned errno 1 in the measured run. Controls and child invocations run in the same sandboxed process tree. Do not substitute other directories or files as controls.

The measured result was 18/18 identical regular Versions/A binary Git blobs and 709/709 identical Dynamic entries (file bytes, symlink contents, Git and POSIX modes), with strict signatures verified for both architectures. A repetition must compare against the committed artifact blobs and stop on a mismatch. There is no claim of a portable source-only reconstruction.

Native C acceptance compares dyn5 with final dyn6 bytes using synthetic MP4/MXF/H.264 decode digests, headless decode choices, and a synthetic localhost TLS1.3 trust/roundtrip test. No x86_64 runtime or GUI rendering claim is made. Probe-bundle compliance runs lgpl_check --release, which directly starts that isolated bundle's ffmpeg and ffprobe helpers with -buildconf; it does not start the RushDeck main executable. No installed application or Companion is used.

## Open limits

Inherited Libplacebo Rust toolchain `.rustup` and Cargo registry `.cargo/registry` source strings are Rust diagnostic/panic source provenance, not shaderc paths. The retained LuaJIT archive embeds module search paths including the original CI home and `/usr/local/share/lua/5.1` and `/usr/local/lib/lua/5.1`; mpv enables Lua, while RushDeck disables external scripts. Libmpv's macos-bundle-path defaults include Homebrew/usr-local executables, applied for MPVBUNDLE=true. The protected compiled config path is not a general environment sandbox.

Libbluray retains the dyn5 `/usr/local/lib/` dlopen search for libaacs/libbdplus. This is a genuine runtime code-search path, reachable for Blu-ray inputs, not build provenance. Its binary is intentionally unchanged from dyn5. Whether the player should retain libbluray requires a separate coordinator/user decision. PIC source correspondence, retained-archive search paths, Homebrew host prerequisites and missing Intel runtime coverage remain limitations.

The current dyn6 scripts retain dead `if True`/`if False` branches and an unreachable `verify_cve2` import after historical roots were removed from their guards. The old drivers under `tools/cve2` and `tools/cve3` are retained historical material and are not supported entry points at this revision. `verify()` defaults to `build=False`; only the supported dyn6 source-build callers explicitly request build-host verification. During relink, `build_frameworks.py` still prepends `toolchain/bin` to PATH, but those copied tools are neither used nor hash-checked by that relink. System Python and Apple tools remain prerequisites.

The measured source-build invocation used the committed driver on the externally prepared cache. `tools/fork6/prepare.py` was not executed, and the outer starter of that build pass was not retained as a script. Attribution to the committed recipe rests on the pre-build snapshot, recorded timing and unchanged recipe blobs, not an archived launcher. Existing acceptance evidence therefore covers the measured prepared inputs and final artifact blobs, not an independently executed cache bootstrap.

GnuTLS binaries contain public cryptographic self-test vectors from upstream `lib/crypto-selftests-pk.c`, including PEM-formatted private-key test vectors. Full binary string inventories consequently contain those public test vectors too. They are distinct from the synthetic TLS probe's private key; that generated probe key is not in the fork, durable root or measurement files. No key material is reproduced here.
