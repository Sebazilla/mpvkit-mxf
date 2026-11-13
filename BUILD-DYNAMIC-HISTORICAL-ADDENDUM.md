# Historical Round 2: documented reproducibility limits (unchanged tag)

The published 0.41.0-mxf-dyn tag remains unchanged; this local documentation addendum does not rebuild or republish binaries. The build PATH includes /opt/homebrew/bin and may select existing host tools. Extracted release source trees are reused without rechecking their contents. The FFmpeg recipe checks HEAD but does not require a clean working tree. Byte identity is evidenced only for repeated arm64 relink/sign, not x86_64 or a full source rebuild. These are known limitations, not reproducibility guarantees.

Round 2 license clarification: uchardet is treated under the MPL-1.1 alternative matching Licenses/uchardet/COPYING; the earlier conservative LGPL label is superseded. Separate notices for libass, FreeType, HarfBuzz, libunibreak, dav1d, LuaJIT, libuavs3d, libdovi, lcms2 and shaderc_combined are not present as tracked license documents in this tag and remain a distribution review item.
