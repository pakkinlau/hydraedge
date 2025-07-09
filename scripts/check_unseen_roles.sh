#!/usr/bin/env bash
# scripts/check_unseen_roles.sh

# 1) After a run, in Python dump:
#      from hydraedge.extractor.wp7_rulemap import get_unseen_counts
#      print("\n".join(get_unseen_counts().keys()))
#    Redirect that to unseen.txt

# 2) diff against your roles list:
comm -23 \
  <(cut -f1 data/sample/roles.tsv | sort) \
  <(sort unseen.txt) \
| tee missing_in_roles.txt

echo
echo "👉 missing_in_roles.txt shows SRL tags seen by pipeline but not in roles.tsv"
