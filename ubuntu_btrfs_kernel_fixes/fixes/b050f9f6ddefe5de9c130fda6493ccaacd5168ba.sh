#!/bin/bash
cat << EOF
fix b050f9f6ddefe5de9c130fda6493ccaacd5168ba

    Btrfs: fix qgroups sanity test crash or hang

    Often when running the qgroups sanity test, a crash or a hang happened.
    This is because the extent buffer the test uses for the root node doesn't
    have an header level explicitly set, making it have a random level value.
    This is a problem when it's not zero for the btrfs_search_slot() calls
    the test ends up doing, resulting in crashes or hangs such as the following:

    [ 6454.127192] Btrfs loaded, debug=on, assert=on, integrity-checker=on
    (...)
    [ 6454.127760] BTRFS: selftest: Running qgroup tests
    [ 6454.127964] BTRFS: selftest: Running test_test_no_shared_qgroup
    [ 6454.127966] BTRFS: selftest: Qgroup basic add
    [ 6480.152005] BUG: soft lockup - CPU#0 stuck for 23s! [modprobe:5383]
    [ 6480.152005] Modules linked in: btrfs(+) xor raid6_pq binfmt_misc nfsd auth_rpcgss oid_registry nfs_acl nfs lockd fscache sunrpc i2c_piix4 i2c_core pcspkr evbug psmouse serio_raw e1000 [last unloaded: btrfs]

    Therefore initialize the extent buffer as an empty leaf (level 0).

    Issue easy to reproduce when btrfs is built as a module via:

        $ for ((i = 1; i <= 1000000; i++)); do rmmod btrfs; modprobe btrfs; done

EOF

for ((i = 1; i <= 100; i++))
do
	echo "Exercising 1000000 btrfs load/unloads: $i%"
	for ((j = 1; j <= 10000; j++))
	do
		rmmod btrfs
		modprobe btrfs
	done
done

exit 0
