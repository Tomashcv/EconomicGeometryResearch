# E4D1D2A2 R2 — official CPS 2019 static layout authority acquisition

R1 correctly remained unresolved because its frozen candidate surface did not contain the official 2019 replicate-weight SAS input file. It also selected the same metadata registry artifact for both person and household layout roles; those selections are preserved as R1 evidence but are not valid layout-file targets.

R2 repairs only the authority-discovery surface. Before downloading any new bytes, it freezes the exact Census 2019 March directory and the exact three filenames required by the frozen CPS executor:

- CPS_ASEC_ASCII_REPWGT_2019.SAS
- persfmt.txt
- hhldfmt.txt

R2 may download and hash those three static text authorities only. It may not parse CPS microdata, mutate any parent adapter, change any scientific definition, or compute any 2019 coordinate.

On success, R2 authorizes a later R3 phase to patch the already-frozen CPS adapter's three static paths and linked hashes. R2 itself does not perform that patch.
