#!/bin/bash

lpdir="/sys/kernel/livepatch"

load_modules()
{
	dir=$1
	kver=`uname -r`
	echo "loading modules for $dir"
	for mod in `ls $dir`;
	do
		if [ -d "$dir/$mod" -a "$mod" != "vmlinux" ];
		then
			# replace '-' and '_' by '*'
			module_name=`echo $mod | sed 's/\-/\*/g;s/_/\*/g'`
			exists=`find /lib/modules/$kver/ -iname $module_name.ko`
			if [ -n "$exists" ];
			then
				# get the module *real* name now
				module_name=`echo $exists |rev | cut -d/ -f1 | rev`
				echo "modprobe $module_name [$mod]"
				sudo modprobe $mod
			else
				echo "Can't find module $mod.ko"
			fi
		fi
	done
}

if [ ! -d "$lpdir" ];
then
	echo "livepatch directory does not exist"
	exit 1
fi

for dir in `ls $lpdir`;
do
	load_modules "$lpdir/$dir"
done

