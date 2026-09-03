# E4D1D3 CPSI R1 P0 — replicate ZIP case-binding repair precommit

A2 proved, without opening archive contents, that the repaired 2019 CPS I adapter
binds `CPS_REP` to a nonexistent uppercase path:

`data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.ZIP`

while the filesystem and frozen 2019 manifest bind exactly one canonical file:

`data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.zip`

The archive's frozen SHA256 remains `6281a4dee146bf72d5547a12b952ac51a07c83794c9ebe00433631030dab14de`, and the frozen container
member remains `CPS_ASEC_ASCII_REPWGT_2019.dat`.

This is a path-case/provenance binding repair only. The precommitted repair changes
exactly one path literal, on source line 86, changing three characters
(`.ZIP` -> `.zip`). It preserves the archive SHA binding, all six top-level
function source hashes, all five internal 2019 year labels, and legacy E4A2D_2022_*
output basenames.

A2's embedded self-hash is not used as authority. Its final bytes are frozen directly
here as SHA256 `df00b50b56fbe0ba4f3a31b2cd9d1d2b67f2a6a62015f841bdc0c99f4496c424` (2837 bytes).

Expected repaired adapter SHA256: `51e08a8cfdf48ad3b98feacacd4ba861eb55611d700f353e8765a72eebd85094`.

No archive content, archive member, PWWGT value, or CPS I value is opened in this
precommit.
