#!/bin/sh

#
# Copyright (C) 2016 Canonical
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

#
#  Trival "smoke test" OverlayFS tests just to see
#  if basic functionality works
#
FS=overlay

TMP=/tmp/$FS
DIR1=$TMP/dir1
DIR2=$TMP/dir2
DIR3=$TMP/dir3
WORK=$TMP/work
ROOT=$TMP/$FS-root

#
# remove any left over files
#
cleandirs()
{
	rm -f $DIR1/* $DIR2/* $DIR3/* $WORK/* $ROOT/*
}

#
# checksum file in $1
#
checksum()
{
	sum=$(md5sum $1 | awk '{ print $1 }')
	echo $sum
}

#
# create a file $1, of size $2 K
#
mkfile()
{
	dd if=/dev/urandom of=$1 bs=1K count=$2 > /dev/null 2>&1
	echo $(checksum $1)
}

#
# get file size in bytes, file $1
#
filesize()
{
	stat --printf "%s" $1
}

#
# get number of hardlinks, file $1
#
hardlinks()
{
	stat --printf "%h" $1
}

#
# mount with stacked lowest to highest:
#	DIR1, DIR2, DIR3 -> ROOT
#
# "The specified lower directories will be stacked beginning from the
# rightmost one and going left."
#
do_mount()
{
	mount -t $FS -o lowerdir=$DIR2:$DIR1,upperdir=$DIR3,workdir=$WORK none $ROOT
}

do_umount()
{
	umount $ROOT
}

#
# test mounting
#
test_mount()
{
	echo -n "$FS: mount: "
	do_mount
	local ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED: ret=$ret"
		exit 1
	fi
	echo "PASSED"
}

#
# test umounting
#
test_umount()
{
	echo -n "$FS: umount: "
	do_umount
	local ret=$?
	if [ $ret -ne 0 ]; then
		echo "FAILED: ret=$ret"
		rc=1
	fi
	echo "PASSED"
}

#
# test checksum of data
#
test_files_checksum()
{
	local csum1a=$(mkfile $DIR1/file1 64)
	local csum2a=$(mkfile $DIR2/file2 64)
	local csum3a=$(mkfile $DIR3/file3 64)

	local csum1b=$(checksum $ROOT/file1)
	local csum2b=$(checksum $ROOT/file2)
	local csum3b=$(checksum $ROOT/file3)

	echo -n "$FS: checksum file1: "
	if [ ${csum1a} = ${csum1b} ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	echo -n "$FS: checksum file2: "
	if [ ${csum2a} = ${csum2b} ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	echo -n "$FS: checksum file3: "
	if [ ${csum3a} = ${csum3b} ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	rm -f $DIR1/file1 $DIR2/file2 $DIR3/file3
}

#
# test removal of files
#
test_files_rm()
{
	local fail=0
	echo -n "$FS: delete: "

	do_umount

	for i in $(seq 100)
	do
		mkfile $DIR1/dir1-$i 1 > /dev/null
		mkfile $DIR2/dir2-$i 2 > /dev/null
		mkfile $DIR3/dir3-$i 3 > /dev/null
	done

	do_mount

	for i in $(seq 100)
	do
		rm -f $ROOT/dir1-$i
		rm -f $ROOT/dir2-$i
		rm -f $ROOT/dir3-$i
	done

	#
	#  Files should not appear in root
	#
	for i in $(seq 100)
	do
		if [ -e $ROOT/dir1-$i ]; then
			fail=1
		fi
		if [ -e $ROOT/dir2-$i ]; then
			fail=1
		fi
		if [ -e $ROOT/dir3-$i ]; then
			fail=1
		fi
	done

	if [ $fail -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	do_umount
	rm -rf $DIR1/* $DIR2/* $DIR3/*
	do_mount
}

#
# test file truncation
#
test_files_truncate()
{
	local fail=0
	echo -n "$FS: truncate: "
	for i in 1 2 4 8 16 32 64 128 256 128 64 32 16 8 4 2 1
	do
		sz=$((i * 1024))
		do_umount
		truncate -s $sz $DIR1/truncate1
		do_mount
		csum1=$(checksum $DIR1/truncate1)
		csum2=$(checksum $ROOT/truncate1)
		newsz=$(filesize $ROOT/truncate1)
		if [ $sz -ne $newsz ]; then
			fail=1
		fi
		if [ $csum1 != $csum2 ]; then
			fail=1
		fi
	done
	if [ $fail -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi
	rm -f $DIR1/truncate1
}

#
# simple stacking sanity checks
#
test_files_stacked()
{
	#
	# "Changes to the underlying filesystems while part of a mounted overlay
	# filesystem are not allowed."
	#
	local fail=0
	echo -n "$FS: stacked: "

	do_umount
	echo test3 > $DIR3/test
	echo test2 > $DIR2/test
	echo test1 > $DIR1/test
	do_mount

	if [ $(cat $ROOT/test) != "test3" ]; then
		fail=1
	fi

	do_umount
	rm -f $DIR3/test
	do_mount

	if [ $(cat $ROOT/test) != "test2" ]; then
		fail=1
	fi

	do_umount
	rm -f $DIR2/test
	do_mount

	if [ $(cat $ROOT/test) != "test1" ]; then
		fail=1
	fi

	do_umount
	rm -f $DIR1/test
	do_mount

	if [ -e $ROOT/test ]; then
		fail=1
	fi

	if [ $fail -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	do_umount
	do_mount
}

#
# check file modification
#
test_files_modify()
{
	local fail=0
	echo -n "$FS: modify: "

	do_umount
	local csum1=$(mkfile $DIR1/file1 32)
	do_mount
	local csumroot1=$(checksum $ROOT/file1)
	if [ $csum1 != $csumroot1 ]; then
		fail=1
	fi
	if [ $(filesize $ROOT/file1) -ne 32768 ]; then
		fail=1
	fi

	do_umount
	local csum2=$(mkfile $DIR1/file1 64)
	do_mount
	local csumroot2=$(checksum $ROOT/file1)
	if [ $csum2 != $csumroot2 ]; then
		fail=1
	fi
	if [ $(filesize $ROOT/file1) -ne 65536 ]; then
		fail=1
	fi

	do_umount
	local csum3=$(mkfile $DIR1/file1 1)
	do_mount
	local csumroot3=$(checksum $ROOT/file1)
	if [ $csum3 != $csumroot3 ]; then
		fail=1
	fi
	if [ $(filesize $ROOT/file1) -ne 1024 ]; then
		fail=1
	fi

	# highly unlikely that M5SUMs match
	if [ $csum1 = $csum2 -o $csum1 = $csum3 ]; then
		fail=1
	fi

	do_umount
	rm -f $DIR1/file1
	do_mount

	if [ $fail -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi
}

#
# test moving and renaming files
#
test_files_mv()
{
	do_umount
	local csum1=$(mkfile $DIR1/file1 1)
	local csum2=$(mkfile $DIR2/file2 2)
	local csum3=$(mkfile $DIR3/file3 4)
	do_mount

	#
	# Rename file1
	#
	echo -n "$FS: rename file1 to file4: "
	mv $ROOT/file1 $ROOT/rename1
	mv $ROOT/rename1 $ROOT/file4

	if [ -e $ROOT/file4 -a \
	     $(checksum $ROOT/file4) = $csum1 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	#
	# Rename file2 to file1
	#
	echo -n "$FS: rename file2 to file1: "
	mv $ROOT/file2 $ROOT/file1
	if [ -e $ROOT/file1 -a \
	     $(checksum $ROOT/file1) = $csum2 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	do_umount
	rm -rf $DIR1/* $DIR2/* $DIR3/*
	do_mount
}

#
# simple hardlinking checks
#
test_files_hardlink()
{
	do_umount
	mkfile $DIR1/file1 1 > /dev/null
	ln $DIR1/file1 $DIR2/file2
	ln $DIR1/file1 $DIR3/file3
	do_mount
	echo -n "$FS: check hardlink count in root: "
	if [ $(hardlinks $ROOT/file1) -ne 3 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	do_umount
	rm -f $DIR3/file3
	do_mount
	echo -n "$FS: check hardlink count in root after 1 link removed: "
	if [ $(hardlinks $ROOT/file1) -ne 2 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	do_umount
	rm -f $DIR2/file2
	do_mount
	echo -n "$FS: check hardlink count in root after 1 more link removed: "
	if [ $(hardlinks $ROOT/file1) -ne 1 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	# try to make cross link (should fail)
	echo -n "$FS: attempt to create invalid cross link on root: "
	do_umount
	ln $ROOT/file1 $DIR1/root-file1 > /dev/null 2>&1
	ret=$?
	do_mount
	if [ $ret -eq 0 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	# remove root view of file1 (should whiteout original)
	echo -n "$FS: remove root view of original file: "
	rm -f $ROOT/file1
	if [ -e $ROOT/file1 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	do_umount
	rm -rf $DIR1/* $DIR2/* $DIR3/*
	do_mount
}

#
# compare stat output, helper for test_files_stat
#
test_files_stat_compare()
{
	stat $DIR1/file1 | grep "File:" | grep "Device:" > $DIR1/file1.stat
	stat $ROOT/file1 | grep "File:" | grep "Device:" > $ROOT/file1.stat
	diff $DIR1/file1.stat $ROOT/file1.stat > /dev/null 2>&1
	if [ $? -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi
}

#
# test stat (trivial)
#
test_files_stat()
{
	do_umount
	mkfile $DIR1/file1 1 > /dev/null
	do_mount

	echo -n "$FS: simple stat check: "
	test_files_stat_compare

	echo -n "$FS: simple stat check (touch file): "
	sleep 0.1
	do_umount
	touch $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod u-x): "
	do_umount
	chmod u-x $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod u+x): "
	do_umount
	chmod u-x $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod g-w): "
	do_umount
	chmod g-w $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod g+w): "
	do_umount
	chmod g-w $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod o-r): "
	do_umount
	chmod o-r $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod o+r): "
	do_umount
	chmod o-r $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod 0777): "
	do_umount
	chmod 0777 $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (access time): "
	do_umount
	cat $DIR1/file1 > /dev/null
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (modify time): "
	do_umount
	echo "append" >> $DIR1/file1
	do_mount
	test_files_stat_compare

	echo -n "$FS: simple stat check (change size): "
	do_umount
	truncate -s 8192 $DIR1/file1
	do_mount
	test_files_stat_compare

	do_umount
	rm -rf $DIR1/*
	do_mount
}

#
# test repeated mount/umounts
#
test_repeat_mounts()
{
	fail=0
	echo -n "$FS: mount/umount (repeated) "
	for i in $(seq 250)
	do
		do_mount
		if [ $? -ne 0 ]; then
			fail=1
			break
		else
			do_umount
			if [ $? -ne 0 ]; then
				fail=1
				break
			fi
		fi
	done

	if [ $fail -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi
}

rm -rf $TMP $DIR1 $DIR2 $DIR3 $WORK $ROOT
mkdir $TMP $DIR1 $DIR2 $DIR3 $WORK $ROOT
rc=0

test_mount
test_files_checksum
test_files_rm
test_files_mv
test_files_truncate
test_files_stacked
test_files_modify
test_files_hardlink
test_files_stat
test_umount
test_repeat_mounts

rm -rf $TMP $DIR1 $DIR2 $DIR3 $WORK $ROOT
exit $rc
