#!/bin/bash
cat << EOF
    fix 289454ad26a2d752e04b07234a175feda9ec0f4e

    btrfs: clear bio reference after submit_one_bio()

    After submit_one_bio(), 'bio' can go away. However submit_extent_page()
    leave 'bio' referable if submit_one_bio() failed (e.g. -ENOMEM on OOM).
    It will cause invalid paging request when submit_extent_page() is called
    next time.

EOF

echo "Not exercised, need CONFIG_FAIL_PAGE_ALLOC, CONFIG_FAULT_INJECTION_DEBUG_FS"

exit 0
