#ifndef __lib_base_remotetssource_h
#define __lib_base_remotetssource_h

#include <string>
#include <lib/base/itssource.h>
#include <lib/base/message.h>
#include <gst/gst.h>

class eTsRemoteSource: public iTsSource, public Object
{
	DECLARE_REF(eTsRemoteSource);

	bool m_is_rtp, m_is_mcast, m_mcast_join;

	eSingleLock m_lock;

	std::string m_uri;
	int m_gst_fds[2];
	unsigned char m_alignment_buffer[188];
	ssize_t m_alignment_buffer_size;

protected:
	GstElement *m_gst_pipeline;
	virtual void play();
public:
	eTsRemoteSource(bool rtp, bool mcast, bool mcast_join);
	virtual ~eTsRemoteSource();

	int open(const char *uri);
	int close();

	// iTsSource
	off_t lseek(off_t offset, int whence);
	ssize_t read(off_t offset, void *buf, size_t count);
	off_t length();
	int valid();
private:
	static void gstPadAdded(GstElement *element, GstPad *pad, gpointer user_data);
	static void gstNotifySource(GObject *o, GParamSpec* p, gpointer d);
};

class eTsRemoteFileSource: public eTsRemoteSource
{
	struct Message
	{
		Message()
			:type(-1)
			{}
		Message(int type)
			:type(type)
		{}
		Message(int type, GstPad *pad)
			:type(type)
		{
			d.pad=pad;
		}
		int type;
		union {
			GstPad *pad; // for msg type 3
		} d;
	};
	eFixedMessagePump<Message> m_pump;

	struct bufferInfo
	{
		int bufferPercent;
		int avgInRate;
		int avgOutRate;
		int64_t bufferingLeft;
		bufferInfo()
			:bufferPercent(0), avgInRate(0), avgOutRate(0), bufferingLeft(-1)
		{
		}
	};

	int m_buffer_size;
	bufferInfo m_bufferInfo;

	static GstBusSyncReply gstBusSyncHandler(GstBus *bus, GstMessage *message, gpointer user_data);
	void gstBusCall(GstBus *bus, GstMessage *msg);
	void gstPoll(const Message&);

	virtual void play();
public:
	eTsRemoteFileSource();
	PyObject *getBufferCharge();
	int setBufferSize(int size);
};


#endif
