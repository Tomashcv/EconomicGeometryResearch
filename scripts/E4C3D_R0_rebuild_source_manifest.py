#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,re,sys,zipfile

RAW=Path(sys.argv[1])
MAN=Path(sys.argv[2])
FREEZE=Path(sys.argv[3])
URL=sys.argv[4]

EXPECTED_SHA="1f4da07a86d149bc85f786346e86730e0c7b73512ce7e1299d77ec15befd12a7"
EXPECTED_BYTES=248018621

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

if sha(RAW)!=EXPECTED_SHA or RAW.stat().st_size!=EXPECTED_BYTES:
    raise SystemExit("FAIL: raw ACS ZIP drift before R0 manifest rebuild")

rx=re.compile(r"^psam_hus[a-z]*\.csv$",re.I)
with zipfile.ZipFile(RAW,"r") as z:
    infos=z.infolist()

selected=[]
rows=[]
for i in infos:
    base=Path(i.filename).name
    sel=int((not i.is_dir()) and bool(rx.fullmatch(base)))
    if base.lower()=="psam_huspr.csv" and sel:
        raise SystemExit("FAIL: Puerto Rico member unexpectedly selected")
    if re.fullmatch(r"psam_pus[a-z]*\.csv",base,re.I):
        raise SystemExit("FAIL: person member found in housing archive")
    if sel:
        selected.append(i.filename)
    rows.append([
        "MEMBER","NA","NA",i.filename,
        str(i.file_size),str(i.compress_size),f"{i.CRC:08x}",str(sel)
    ])

if selected!=["psam_husa.csv","psam_husb.csv"]:
    raise SystemExit(f"FAIL: unexpected selected members: {selected}")

MAN.parent.mkdir(parents=True,exist_ok=True)
with MAN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "row_type","source_url","sha256","member_name",
        "uncompressed_bytes","compressed_bytes","crc32","selected"
    ])
    w.writerow([
        "ARCHIVE",URL,EXPECTED_SHA,"__ARCHIVE__",
        str(EXPECTED_BYTES),"NA","NA","0"
    ])
    w.writerows(rows)

manifest_sha=sha(MAN)
FREEZE.write_text(
    "\n".join([
        f"RAW_ZIP_SHA256={EXPECTED_SHA}",
        f"RAW_ZIP_BYTES={EXPECTED_BYTES}",
        f"SOURCE_MANIFEST_SHA256={manifest_sha}",
        "ZIP_CENTRAL_DIRECTORY_OPENED=1",
        "CSV_MEMBER_BYTES_OPENED=0",
        "CSV_HEADERS_OPENED=0",
        "ACS_MICRODATA_VALUES_OPENED=0",
        "SOURCE_MANIFEST_FROZEN_BEFORE_ROW_PARSE=1",
        "E4C3D_R0_TSV_SERIALIZATION_REPAIR=1",
        "E4C3D_SOURCE_FREEZE=PASS",
    ])+"\n",
    encoding="utf-8",
)

print(f"ZIP_MEMBER_COUNT={len(infos)}")
print(f"SELECTED_HOUSING_MEMBER_COUNT={len(selected)}")
for x in selected:
    print(f"SELECTED_MEMBER={x}")
print("CSV_MEMBER_BYTES_OPENED=0")
print("ACS_MICRODATA_VALUES_OPENED=0")
print(f"REPAIRED_MANIFEST_SHA256={manifest_sha}")
