#ifndef __elock_h
#define __elock_h

#include <pthread.h>

class singleLock
{
	pthread_mutex_t &lock;
public:
	singleLock(pthread_mutex_t &m ) __attribute__ ((always_inline))
		:lock(m)
	{
		pthread_mutex_lock(&lock);
	}
	~singleLock() __attribute__ ((always_inline))
	{
		pthread_mutex_unlock(&lock);
	}
};

class eRdWrLock
{
	friend class eRdLocker;
	friend class eWrLocker;
	pthread_rwlock_t m_lock;
	eRdWrLock(eRdWrLock &);
public:
	eRdWrLock() __attribute__ ((always_inline))
	{
		pthread_rwlock_init(&m_lock, 0);
	}
	~eRdWrLock() __attribute__ ((always_inline))
	{
		pthread_rwlock_destroy(&m_lock);
	}
	void RdLock() __attribute__ ((always_inline))
	{
		pthread_rwlock_rdlock(&m_lock);
	}
	void WrLock() __attribute__ ((always_inline))
	{
		pthread_rwlock_wrlock(&m_lock);
	}
	void Unlock() __attribute__ ((always_inline))
	{
		pthread_rwlock_unlock(&m_lock);
	}
};

class eRdLocker
{
	eRdWrLock &m_lock;
public:
	eRdLocker(eRdWrLock &m) __attribute__ ((always_inline))
		: m_lock(m)
	{
		pthread_rwlock_rdlock(&m_lock.m_lock);
	}
	~eRdLocker() __attribute__ ((always_inline))
	{
		pthread_rwlock_unlock(&m_lock.m_lock);
	}
};

class eWrLocker
{
	eRdWrLock &m_lock;
public:
	eWrLocker(eRdWrLock &m) __attribute__ ((always_inline))
		: m_lock(m)
	{
		pthread_rwlock_wrlock(&m_lock.m_lock);
	}
	~eWrLocker() __attribute__ ((always_inline))
	{
		pthread_rwlock_unlock(&m_lock.m_lock);
	}
};

/* FIXME: rename to eMutex */
class eSingleLock
{
	pthread_mutex_t m_lock;
public:
	eSingleLock(bool recursive=false)
	{
		if (recursive)
		{
			pthread_mutexattr_t attr;
			pthread_mutexattr_init(&attr);
			pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
			pthread_mutex_init(&m_lock, &attr);
			pthread_mutexattr_destroy(&attr);
		}
		else
			pthread_mutex_init(&m_lock, 0);
	}
	~eSingleLock() __attribute__ ((always_inline))
	{
		pthread_mutex_destroy(&m_lock);
	}

	void lock() __attribute__ ((always_inline))
	{
		pthread_mutex_lock(&m_lock);
	}
	bool tryLock() __attribute__ ((always_inline))
	{
		return pthread_mutex_trylock(&m_lock) == 0;
	}
	void unlock() __attribute__ ((always_inline))
	{
		pthread_mutex_unlock(&m_lock);
	}
};

class eSingleLocker
{
	eSingleLock &m_lock;
public:
	eSingleLocker(eSingleLock &m) __attribute__ ((always_inline))
		: m_lock(m)
	{
		m_lock.lock();
	}
	~eSingleLocker() __attribute__ ((always_inline))
	{
		m_lock.unlock();
	}
};

class eLock
{
	pthread_mutex_t m_mutex;
	pthread_cond_t m_cond;

	int m_counter, m_max;
public:
	void lock(int res=100);
	void unlock(int res=100);
	int lock_count();
	int trylock(int res=100, bool force=false);
	int counter() const { return m_counter; }
	int max() const { return m_max; }

	eLock(int max=100);
	~eLock();
};

class eLocker
{
	eLock &lock;
	int res;
public:
	eLocker(eLock &lock, int res=100);
	~eLocker();
};

class eSemaphore
{
	int v;
	pthread_mutex_t mutex;
	pthread_cond_t cond;
public:
	eSemaphore();
	~eSemaphore();
	
	int down();
	int decrement();
	int up();
	int value();
};

#endif
