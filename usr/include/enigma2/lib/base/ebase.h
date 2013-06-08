#ifndef __ebase_h
#define __ebase_h

#ifndef SWIG
#include <vector>
#include <map>
#include <sys/poll.h>
#include <sys/time.h>
#include <asm/types.h>
#include <time.h>

#include <lib/base/eptrlist.h>
#include <lib/base/sigc.h>
#endif

#include <lib/python/connections.h>

#define E_UNUSED(x)	(void)x;

class eMainloop;

extern eMainloop* eApp;

#define DUMP_DESCRIPTOR(class, it) \
	do { \
		eDebug(class"::%s line %d descriptor with tag %04x", __FUNCTION__, __LINE__, (*it)->getTag()); \
	} while (0);

#ifndef SWIG
	/* TODO: remove these inlines. */
static inline bool operator<( const timespec &t1, const timespec &t2 )
{
	return t1.tv_sec < t2.tv_sec || (t1.tv_sec == t2.tv_sec && t1.tv_nsec < t2.tv_nsec);
}

static inline bool operator<=( const timespec &t1, const timespec &t2 )
{
	return t1.tv_sec < t2.tv_sec || (t1.tv_sec == t2.tv_sec && t1.tv_nsec <= t2.tv_nsec);
}

static inline timespec &operator+=( timespec &t1, const timespec &t2 )
{
	t1.tv_sec += t2.tv_sec;
	if ( (t1.tv_nsec += t2.tv_nsec) >= 1000000000 )
	{
		t1.tv_sec++;
		t1.tv_nsec -= 1000000000;
	}
	return t1;
}

static inline timespec operator+( const timespec &t1, const timespec &t2 )
{
	timespec tmp;
	tmp.tv_sec = t1.tv_sec + t2.tv_sec;
	if ( (tmp.tv_nsec = t1.tv_nsec + t2.tv_nsec) >= 1000000000 )
	{
		tmp.tv_sec++;
		tmp.tv_nsec -= 1000000000;
	}
	return tmp;
}

static inline timespec operator-( const timespec &t1, const timespec &t2 )
{
	timespec tmp;
	tmp.tv_sec = t1.tv_sec - t2.tv_sec;
	if ( (tmp.tv_nsec = t1.tv_nsec - t2.tv_nsec) < 0 )
	{
		tmp.tv_sec--;
		tmp.tv_nsec += 1000000000;
	}
	return tmp;
}

static inline timespec operator-=( timespec &t1, const timespec &t2 )
{
	t1.tv_sec -= t2.tv_sec;
	if ( (t1.tv_nsec -= t2.tv_nsec) < 0 )
	{
		t1.tv_sec--;
		t1.tv_nsec += 1000000000;
	}
	return t1;
}

static inline timespec &operator+=( timespec &t1, const long msek )
{
	t1.tv_sec += msek / 1000;
	if ( (t1.tv_nsec += (msek % 1000) * 1000000) >= 1000000000 )
	{
		t1.tv_sec++;
		t1.tv_nsec -= 1000000000;
	}
	return t1;
}

static inline timespec operator+( const timespec &t1, const long msek )
{
	timespec tmp;
	tmp.tv_sec = t1.tv_sec + msek / 1000;
	if ( (tmp.tv_nsec = t1.tv_nsec + (msek % 1000) * 1000000) >= 1000000000 )
	{
		tmp.tv_sec++;
		tmp.tv_nsec -= 1000000;
	}
	return tmp;
}

static inline timespec operator-( const timespec &t1, const long msek )
{
	timespec tmp;
	tmp.tv_sec = t1.tv_sec - msek / 1000;
	if ( (tmp.tv_nsec = t1.tv_nsec - (msek % 1000)*1000000) < 0 )
	{
		tmp.tv_sec--;
		tmp.tv_nsec += 1000000000;
	}
	return tmp;
}

static inline timespec operator-=( timespec &t1, const long msek )
{
	t1.tv_sec -= msek / 1000;
	if ( (t1.tv_nsec -= (msek % 1000) * 1000000) < 0 )
	{
		t1.tv_sec--;
		t1.tv_nsec += 1000000000;
	}
	return t1;
}

static inline int64_t timeout_msec ( const timespec & orig )
{
	timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);
	return (int64_t)((orig-now).tv_sec)*1000 + (orig-now).tv_nsec/1000000;
}

static inline int64_t timeout_msec ( const timespec & orig, const timespec &now )
{
	return (int64_t)((orig-now).tv_sec)*1000 + (orig-now).tv_nsec/1000000;
}

#endif

class eSocketNotifier;
class eTimer;
class PSignal;

class eMainloop
{
	friend class eTimer;
	friend class eSocketNotifier;
	friend class ePythonConfigQuery;

	virtual eSocketNotifier *createSocketNotifier(int fd, int req, bool startnow) = 0;
	virtual eTimer *createTimer() = 0;
	virtual void addSocketNotifier(eSocketNotifier *sn) = 0;
	virtual void removeSocketNotifier(eSocketNotifier *sn) = 0;
	virtual void addTimer(eTimer* e) = 0;
	virtual void removeTimer(eTimer* e) = 0;

protected:
	int m_is_idle;
	int m_idle_count;

	virtual void enterIdle() { m_is_idle=1; ++m_idle_count; }
	virtual void leaveIdle() { m_is_idle=0; }

	virtual ~eMainloop();
public:
	eMainloop();
#ifndef SWIG
	virtual void quit(int ret=0) = 0; // leave all pending loops (recursive leave())
#endif
		/* run will iterate endlessly until the app is quit, and return
		   the exit code */
	virtual int runLoop() = 0;

		/* m_is_idle needs to be atomic, but it doesn't really matter much, as it's read-only from outside */
	int isIdle() { return m_is_idle; }
	int idleCount() { return m_idle_count; }
};

#ifndef SWIG
			// die beiden signalquellen: SocketNotifier...
/**
 * \brief Gives a callback when data on a file descriptor is ready.
 *
 * This class emits the signal \c eSocketNotifier::activate whenever the
 * event specified by \c req is available.
 */
class eSocketNotifier: public iObject
{
	friend class eMainloop_native;
	DECLARE_REF(eSocketNotifier);
public:
	enum { Read=POLLIN, Write=POLLOUT, Priority=POLLPRI, Error=POLLERR, Hungup=POLLHUP };
protected:
	eMainloop *context;
	eSocketNotifier(eMainloop *context, int fd, int req, bool startnow);
private:
	int fd;
	int state;
	int requested;		// requested events (POLLIN, ...)
public:
	/**
	 * \brief Constructs a eSocketNotifier.
	 * \param context The thread where to bind the socketnotifier to. The signal is emitted from that thread.
	 * \param fd The filedescriptor to monitor. Can be a device or a socket.
	 * \param req The events to watch to, normally either \c Read or \c Write. You can specify any events that \c poll supports.
	 * \param startnow Specifies if the socketnotifier should start immediately.
	 */
	static eSocketNotifier* create(eMainloop *context, int fd, int req, bool startnow=true) { return context->createSocketNotifier(fd, req, startnow); }
	virtual ~eSocketNotifier();

	PSignal1<void, int> activated;

	void start();
	void stop();
	bool isRunning() { return state; }

	int getFD() { return fd; }
	int getRequested() { return requested; }
	virtual void setRequested(int req) { requested = req; }
	int getState() { return state; }
	void activate(int what);

	eSmartPtrList<iObject> m_clients;
};

				// ... und Timer
/**
 * \brief Gives a callback after a specified timeout.
 *
 * This class emits the signal \c eTimer::timeout after the specified timeout.
 */
class eTimer: public iObject
{
	friend class eMainloop_native;
	DECLARE_REF(eTimer);
	timespec nextActivation;
	int interval;
	bool bSingleShot;
	bool bActive;
protected:
	eMainloop *context;
	eTimer(eMainloop *context);
public:
	/**
	 * \brief Constructs a timer.
	 *
	 * The timer is not yet active, it has to be started with \c start.
	 * \param context The thread from which the signal should be emitted.
	 */
	static eTimer *create(eMainloop *context=eApp) { return context->createTimer(); }
	virtual ~eTimer();

	PSignal0<void> timeout;

	bool isActive() { return bActive; }

	timespec &getNextActivation() { return nextActivation; }
	int getInterval() const { return interval; }

	void activate();
	void start(int msec, bool b=false);
	void stop();
	void changeInterval(int msek);
	void startLongTimer(int seconds);
	bool operator<(const eTimer& t) const { return nextActivation < t.nextActivation; }
	eSmartPtrList<iObject> m_clients;
};

			// werden in einer mainloop verarbeitet
class eMainloop_native: public eMainloop
{
	bool m_timer_sn_thread_checks;
protected:
	std::multimap<int, eSocketNotifier*> m_notifiers;
	std::multimap<int, eSocketNotifier*> m_notifiers_new;

	ePtrList<eTimer> m_timers;
	ePtrList<eTimer> m_timers_new;

	pid_t m_tid;
	volatile bool m_abort_loop;
	int m_loop_count;
	bool m_app_quit_now;
	int m_retval;

	void processOneEvent(int do_wait=1);

	eSocketNotifier *createSocketNotifier(int fd, int req, bool startnow) { return new eSocketNotifier(this, fd, req, startnow); }
	eTimer *createTimer() { return new eTimer(this); }

	void addSocketNotifier(eSocketNotifier *sn);
	void removeSocketNotifier(eSocketNotifier *sn);
	void addTimer(eTimer* e);
	void removeTimer(eTimer* e);
public:
	eMainloop_native();
	~eMainloop_native();

	void quit(int ret=0); // leave all pending loops (recursive leave())
		/* run will iterate endlessly until the app is quit, and return
		   the exit code */
	int runLoop();

	void reset() { m_app_quit_now = false; }
};
#endif  // SWIG

#endif
