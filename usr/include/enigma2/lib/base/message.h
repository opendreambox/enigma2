#ifndef __lib_base_message_h
#define __lib_base_message_h

#include <lib/base/ebase.h>
#include <lib/python/swig.h>
#include <unistd.h>
#include <lib/base/elock.h>


/**
 * \brief A generic messagepump.
 *
 * You can send and receive messages with this class. Internally a fifo is used,
 * so you can use them together with a \c eMainloop.
 */
#ifndef SWIG
class eMessagePump
{
protected:
	int fd[2];
	eLock content;
	int ismt;
public:
	eMessagePump(int mt=0);
	virtual ~eMessagePump();
	/* its NOT safe to call flush from other than 'receiver' context !!! */
	void flush();
protected:
	int send(const void *data, int len);
	int recv(void *data, int len); // blockierend
	int getInputFD() const;
	int getOutputFD() const;
};

/**
 * \brief A messagepump with fixed-length packets.
 *
 * Based on \ref eMessagePump, with this class you can send and receive fixed size messages.
 * Automatically creates a eSocketNotifier and gives you a callback.
 */
template<class T>
class eFixedMessagePump: public eMessagePump, public sigc::trackable
{
	ePtr<eSocketNotifier> sn;
	void do_recv(int)
	{
		T msg;
		const int msg_size = sizeof(T);
		if (likely(recv(&msg, msg_size) == msg_size))
			/*emit*/ recv_msg(msg);
	}
	void do_recv_mt(int)
	{
		/*
		 * before calling (blocking) recv we have to check
		 * if anything is avail to read
		 *
		 */
		int cnt=0;
		T msg;
		const int msg_size = sizeof(T);
		ePtr<eSocketNotifier> notifier = sn;
		while (++cnt < 16 && content.counter() >= msg_size)
		{
			if (likely(recv(&msg, msg_size) == msg_size))
			{
				int ref_cnt = notifier->RefCount();
				/*emit*/ recv_msg(msg);
				if (unlikely(notifier->RefCount() != ref_cnt))
					break;
			}
		}
	}
public:
	sigc::signal1<void,const T&> recv_msg;
	void send(const T &msg)
	{
		eMessagePump::send(&msg, sizeof(msg));
	}
	eFixedMessagePump(eMainloop *context, int mt)
		:eMessagePump(mt)
	{
		sn=eSocketNotifier::create(context, getOutputFD(), eSocketNotifier::Read);
		if (ismt)
			CONNECT(sn->activated, eFixedMessagePump<T>::do_recv_mt);
		else
			CONNECT(sn->activated, eFixedMessagePump<T>::do_recv);
	}
	void start() { if (sn) sn->start(); }
	void stop() { if (sn) sn->stop(); }
};
#endif

class ePythonMessagePump: public eMessagePump, public sigc::trackable
{
	ePtr<eSocketNotifier> sn;
	void do_recv(int)
	{
		int msg;
		const int msg_size = sizeof(msg);
		if (likely(recv(&msg, msg_size) == msg_size))
			/*emit*/ recv_msg(msg);
	}
public:
	PSignal1<void,int> recv_msg;
	void send(int msg)
	{
		eMessagePump::send(&msg, sizeof(msg));
	}
	ePythonMessagePump()
		:eMessagePump(1)
	{
		sn=eSocketNotifier::create(eApp, getOutputFD(), eSocketNotifier::Read);
		CONNECT(sn->activated, ePythonMessagePump::do_recv);
		sn->start();
	}
	void start() { if (sn) sn->start(); }
	void stop() { if (sn) sn->stop(); }
};

#endif
