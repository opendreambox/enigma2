#!/bin/sh

prefix=/usr
exec_prefix=/usr
datarootdir=${prefix}/share

if [ -x /usr/bin/showiframe -a -f /usr/share/backdrop.mvi ]; then
	/usr/bin/showiframe /usr/share/backdrop.mvi
fi

# hook to execute scripts always before enigma2 start
if [ -x /usr/bin/enigma2_pre_start.sh ]; then
	/usr/bin/enigma2_pre_start.sh
fi

if [ -d /home/root ]; then
	cd /home/root
fi

LIBS="$LIBS /usr/lib/libopen.so.0.0.0"

#check for dreambox specific passthrough helper lib
if [ -e /usr/lib/libpassthrough.so ]; then
	LIBS="$LIBS /usr/lib/libpassthrough.so"
fi

LD_PRELOAD=$LIBS /usr/bin/enigma2

# enigma2 exit codes:
#
# 0 - restart enigma
# 1 - halt
# 2 - reboot
#
# >128 signal

ret=$?
case $ret in
	1)
		/sbin/halt
		;;
	2)
		/sbin/reboot
		;;
	4)
		/sbin/rmmod lcd
		/usr/sbin/fpupgrade --upgrade 2>&1 | tee /home/root/fpupgrade.log
		sleep 1;
		/sbin/rmmod fp
		/sbin/modprobe fp
		/sbin/reboot
		;;
	*)
		;;
esac
