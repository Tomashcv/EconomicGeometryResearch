# E4C3D R0 — source-manifest TSV serialization repair

E4C3D Attempt 1 successfully:

- froze the scientific estimator before source acquisition;
- downloaded the exact official ACS 2022 national housing ZIP;
- recorded SHA-256 `1f4da07a86d149bc85f786346e86730e0c7b73512ce7e1299d77ec15befd12a7`;
- inspected only the ZIP central directory;
- selected `psam_husa.csv` and `psam_husb.csv`;
- opened zero CSV member bytes and zero ACS economic values.

The run stopped before the source-freeze commit because the archive row in the generated TSV ended in empty tab-separated fields. `git diff --cached --check` correctly rejected the trailing whitespace.

R0 is a serialization repair only. It does not modify the frozen E4C3D estimator or scientific parser.

The failed manifest and source-freeze bytes are preserved exactly. The repaired manifest represents non-applicable archive/member fields explicitly using `NA`/`__ARCHIVE__` and ends every TSV row with a substantive final field.

After the repaired source manifest is committed, the unchanged E4C3D parser may open the first ACS row values.
