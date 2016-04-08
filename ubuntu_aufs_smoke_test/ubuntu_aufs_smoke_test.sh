#!/bin/sh

#
# Copyright (C) 2015 Canonical
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
#  Trival "smoke test" AUFS tests just to see
#  if basic functionality works
#
FS=aufs

TMP=/tmp/$FS
DIR1=$TMP/dir1
DIR2=$TMP/dir2
DIR3=$TMP/dir3
ROOT=$TMP/$FS-root

#
# remove any left over files
#
cleandirs()
{
	rm -f $DIR1/* $DIR2/* $DIR3/* $ROOT/*
	rm -rf $DIR1/.wh* $DIR2/.wh* $DIR3/.wh*
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
# test mounting
#
test_mount()
{
	echo -n "$FS: mount: "
	mount -t $FS -o br=$DIR1:$DIR2:$DIR3 none $ROOT
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
	umount $ROOT
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

	rm $DIR1/file1 $DIR2/file2 $DIR3/file3
}

#
# test removal of files
#
test_files_rm()
{
	local fail=0
	echo -n "$FS: delete: "

	for i in $(seq 100)
	do
		mkfile $DIR1/dir1-$i 1 > /dev/null
		mkfile $DIR2/dir2-$i 2 > /dev/null
		mkfile $DIR3/dir3-$i 3 > /dev/null
	done

	for i in $(seq 100)
	do
		rm $DIR1/dir1-$i
		rm $DIR2/dir2-$i
		rm $DIR3/dir3-$i
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
		truncate -s $sz $DIR1/truncate1
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
	local fail=0
	echo -n "$FS: stacked: "

	echo test3 > $DIR3/test
	echo test2 > $DIR2/test
	echo test1 > $DIR1/test

	if [ $(cat $ROOT/test) != "test1" ]; then
		fail=1
	fi

	rm $DIR1/test
	if [ $(cat $ROOT/test) != "test2" ]; then
		fail=1
	fi

	rm $DIR2/test
	if [ $(cat $ROOT/test) != "test3" ]; then
		fail=1
	fi

	rm $DIR3/test
	if [ -e $ROOT/test ]; then
		fail=1
	fi

	if [ $fail -eq 0 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi
}

#
# check file modification
#
test_files_modify()
{
	local fail=0
	echo -n "$FS: modify: "

	local csum1=$(mkfile $DIR1/file1 32)
	local csumroot1=$(checksum $ROOT/file1)
	if [ $csum1 != $csumroot1 ]; then
		fail=1
	fi
	if [ $(filesize $ROOT/file1) -ne 32768 ]; then
		fail=1
	fi

	local csum2=$(mkfile $DIR1/file1 64)
	local csumroot2=$(checksum $ROOT/file1)
	if [ $csum2 != $csumroot2 ]; then
		fail=1
	fi
	if [ $(filesize $ROOT/file1) -ne 65536 ]; then
		fail=1
	fi

	local csum3=$(mkfile $DIR1/file1 1)
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

	rm $DIR1/file1

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
	local csum1=$(mkfile $DIR1/file1 1)
	local csum2=$(mkfile $DIR2/file2 2)
	local csum3=$(mkfile $DIR3/file3 4)
	mkdir $DIR1/subdir

	#
	# Simple rename in same dir
	#
	echo -n "$FS: rename file: "
	mv $DIR1/file1 $DIR1/rename1
	if [ -e $ROOT/rename1 -a \
             $(checksum $ROOT/rename1) = $csum1 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	#
	# Simple move to other dir
	#
	echo -n "$FS: move file to subdirectory: "
	mv $DIR1/rename1 $DIR1/subdir/rename1
	if [ -e $ROOT/subdir/rename1 -a \
	     $(checksum $ROOT/subdir/rename1) = $csum1 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	#
	# Move file2 down to $DIR1
	#
	echo -n "$FS: rename file2 to dir1: "
	mv $DIR2/file2 $DIR1/rename2
	if [ -e $ROOT/rename2 -a \
	     $(checksum $ROOT/rename2) = $csum2 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	#
	# Move file3 to $ROOT and move to $DIR1
	#
	echo -n "$FS: move file3 to root and then to dir1: "
	mv $DIR3/file3 $ROOT/rename3
	mv $ROOT/rename3 $DIR1/rename3again

	if [ -e $ROOT/rename3again -a \
	     $(checksum $ROOT/rename3again) = $csum3 ]; then
		echo "PASSED"
	else
		echo "FAILED"
		rc=1
	fi

	rm -rf $DIR1/rename3again $DIR1/rename2 $DIR1/subdir
}

#
# simple hardlinking checks
#
test_files_hardlink()
{
	mkfile $DIR1/file1 1 > /dev/null
	ln $DIR1/file1 $DIR2/file2
	ln $DIR1/file1 $DIR3/file3
	echo -n "$FS: check hardlink count in root: "
	if [ $(hardlinks $ROOT/file1) -ne 3 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	rm $DIR3/file3
	echo -n "$FS: check hardlink count in root after 1 link removed: "
	if [ $(hardlinks $ROOT/file1) -ne 2 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	rm $DIR2/file2
	echo -n "$FS: check hardlink count in root after 1 more link removed: "
	if [ $(hardlinks $ROOT/file1) -ne 1 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	# try to make cross link (should fail)
	echo -n "$FS: attempt to create invalid cross link on root: "
	ln $ROOT/file1 $DIR1/root-file1 > /dev/null 2>&1
	if [ $? -eq 0 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi

	# remove root view of file1 (should whiteout original)
	echo -n "$FS: remove root view of original file: "
	rm $ROOT/file1
	if [ -e $ROOT/file1 ]; then
		echo "FAILED"
		rc=1
	else
		echo "PASSED"
	fi
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
	mkfile $DIR1/file1 1 > /dev/null

	echo -n "$FS: simple stat check: "
	test_files_stat_compare

	echo -n "$FS: simple stat check (touch file): "
	sleep 0.1
	touch $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod u-x): "
	chmod u-x $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod u+x): "
	chmod u-x $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod g-w): "
	chmod g-w $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod g+w): "
	chmod g-w $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod o-r): "
	chmod o-r $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod o+r): "
	chmod o-r $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (chmod 0777): "
	chmod 0777 $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (access time): "
	cat $DIR1/file1 > /dev/null
	test_files_stat_compare

	echo -n "$FS: simple stat check (modify time): "
	echo "append" >> $DIR1/file1
	test_files_stat_compare

	echo -n "$FS: simple stat check (change size): "
	truncate -s 8192 $DIR1/file1
	test_files_stat_compare
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
		mount -t $FS -o br=$DIR1:$DIR2:$DIR3 none $ROOT
		if [ $? -ne 0 ]; then
			fail=1
			break
		else
			umount $ROOT
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

rm -rf $TMP
mkdir $TMP $DIR1 $DIR2 $DIR3 $ROOT
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

rm -rf $TMP
exit $rc
