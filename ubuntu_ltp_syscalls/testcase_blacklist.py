# This database describes those test we need to skip
# It used to be a yaml file, but the python-yaml package does not exist in Groovy
# I have this converted into a dictionary for better compatibility across releases (lp:1895801)
blacklist_db = {
    'flavour': {
        'kvm': {
            'statx07 statx07': {
                'comment': 'nfs-kernel-server requires CONFIG_NFSD on KVM kernels (lp: 1821275)'}
        }
    },
    'flavour-series': {
        'aws-trusty': {
            'quotactl01 quotactl01': {
                'comment': 'no extra module for Trusty AWS (lp: 1841410)'},
            'quotactl02 quotactl02': {
                'comment': 'no extra module for Trusty AWS (lp: 1841410)'},
            'quotactl03 quotactl03': {
                'comment': 'no extra module for Trusty AWS (lp: 1841410)'},
            'quotactl06 quotactl06': {
                'comment': 'no extra module for Trusty AWS (lp: 1841410)'}
        }
    },
    'kernel': {
        '4.5.0': {
            'fanotify07 fanotify07': {
                'comment': 'fanotify07 will not get fixed < 4.5.0 (lp: 1775165)'}
            },
        '4.13.0': {
            'inotify07 inotify07': {
                'comment': 'the fix depends on ovl_inode code that was introduced in kernel v4.13 (LP: #1774387)'},
            'inotify08 inotify08': {
                'comment': 'the fix depends on ovl_inode code that was introduced in kernel v4.13 (LP: #1775784)'},
            },
        '5.2.0': {
            'copy_file_range02 copy_file_range02': {
                'comment': 'copy_file_range02 will not get fixed < 5.2.0 (https://lwn.net/Articles/774114)'}
        }
    }
}
