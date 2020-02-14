#ifndef __lib_base_filepush_h
#define __lib_base_filepush_h

#include <lib/base/itssource.h>
#include <lib/base/thread.h>
#include <lib/base/ioprio.h>
#include <lib/base/sigc.h>
#include <lib/base/message.h>
#include <sys/types.h>

class iFilePushScatterGather
{
public:
	virtual void getNextSourceSpan(int64_t current_offset, size_t bytes_read, int64_t &start, size_t &size)=0;
	virtual ~iFilePushScatterGather() {}
};

class eFilePushThread: public eThread, public sigc::trackable
{
public:
	eFilePushThread(int prio_class=IOPRIO_CLASS_BE, int prio_level=5, int blocksize=188);
	virtual ~eFilePushThread();

	virtual void thread();

	void stop();

	virtual void start(int sourcefd, int destfd);
	virtual int start(const char *filename, int destfd);
	virtual void start(ePtr<iTsSource> &source, int destfd);

	void pause();
	void resume();

		/* flushes the internal readbuffer */
	void flush();
	void enablePVRCommit(int);

		/* stream mode will wait on EOF until more data is available. */
	void setStreamMode(int);

	void setScatterGather(iFilePushScatterGather *);

	enum { evtEOF, evtReadError, evtWriteError, evtUser };
	sigc::signal1<void,int> m_event;

	void installSigUSR1Handler();
	void before_set_thread_alive();

		/* you can send private events if you want */
	void sendEvent(int evt);

protected:
	int prio_class, prio;

	iFilePushScatterGather *m_sg;
	int m_stop;
	int m_buf_start, m_buf_end, m_filter_end;
	int m_fd_dest;
	int m_send_pvr_commit;
	int m_stream_mode;
	int m_blocksize;

	int64_t m_current_position;

	ePtr<iTsSource> m_source;

	eFixedMessagePump<int> m_messagepump;

	void recvEvent(const int &evt);
};

#endif
