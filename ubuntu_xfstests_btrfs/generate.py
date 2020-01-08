#!/usr/bin/env python2

#
# Read the test definitions and output text which can be included in control.ubuntu. 
# This will define which tests are valid on different target file systems.
# This only needs to be done after updating to a new upstream xfstests tarball.
#

import subprocess

for tn in range(1,276):
    tns = '%03d' % tn
    p = subprocess.Popen(['grep', '_supported_fs', 'xfstests/'+tns ], stdout=subprocess.PIPE)
    out, err = p.communicate()
    #print ('%s: %s' % (tns, out))
    fstypes = out.split()[1:]
    if len(fstypes) == 0:
        fstypes = "['generic']"
    print "\t    '" + tns + "' : %s," % fstypes
