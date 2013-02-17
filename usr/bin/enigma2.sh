#!/bin/sh

prefix=/usr
exec_prefix=/usr
datarootdir=${prefix}/share

if [ -x /usr/bin/showiframe -a -f /usr/share/backdrop.mvi ]; then
	/usr/bin/showiframe /usr/share/backdrop.mvi
fi

# hook to execute scripts always before enigma2 start
for i in `ls /usr/bin/enigma2_pre_start*.sh 2> /dev/null`; do
	[ -x $i ] && $i || /bin/true
done

if [ -d /home/root ]; then
	cd /home/root
fi

LIBS="$LIBS /usr/lib/libopen.so"

#check for dreambox specific pagecache helper lib
if [ -e /usr/lib/libpagecache.so ]; then
	(sleep 40; echo "libpagecache exists... drop caches now!"; echo 3 > /proc/sys/vm/drop_caches;) &
	LIBS="$LIBS /usr/lib/libpagecache.so"
fi

#check for dreambox specific passthrough helper lib
if [ -e /usr/lib/libpassthrough.so ]; then
	LIBS="$LIBS /usr/lib/libpassthrough.so"
fi

(sleep 2; echo "enigma2 is the main pvr application... adjust oom score!"; PID=$(pidof enigma2); \
	[ -e /proc/$PID/oom_score_adj ] && echo "-999" > /proc/$PID/oom_score_adj || echo "-17" > /proc/$PID/oom_adj;) &

PAGECACHE_FLUSH_INTERVAL=$((512*1024)) LD_PRELOAD=$LIBS /usr/bin/enigma2

# enigma2 exit codes:
#
# 0 - restart enigma
# 1 - halt
# 2 - reboot
# 6 - start softwareupgrade and restart enigma2
# 7 - start softwareupgrade and reboot
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
	6)
		/usr/bin/opkgfb
		;;
	7)
		/usr/bin/opkgfb
		/sbin/reboot
		;;
	*)
		;;
esac
