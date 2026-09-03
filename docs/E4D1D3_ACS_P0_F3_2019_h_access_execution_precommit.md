# E4D1D3 ACS P0 F3 — corrected first 2019 empirical execution precommit

Two pre-value validator assumptions were caught before any empirical execution.

1. The initial P0 assumed the general E4D1B manifest also carried the later-acquired ACS person archive. The canonical person authority is instead the dedicated E4D1BR2B person-data manifest.
2. F1 used the wrong E4D1BR2B registry key `member_name`. F2 proved the exact key is `member`, and the exact header fields are `SERIALNO_present`, `RELSHIPP_present`, and `AGEP_present`.

The frozen method processes two housing CSVs (`psam_husa.csv`, `psam_husb.csv`) and all person CSVs; the canonical person set is exactly (`psam_pusa.csv`, `psam_pusb.csv`). No unique-person-member assumption is allowed.

F3 hashes both canonical raw archives and reads only their ZIP central directories. It opens no CSV member content, survey row, coordinate value, or adapter execution.

A successful F3 precommit freezes the structural acceptance criteria and authorizes only the subsequent ACS H 2019 empirical execution.
