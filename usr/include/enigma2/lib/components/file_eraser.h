#ifndef __lib_components_file_eraser_h
#define __lib_components_file_eraser_h

#include <lib/base/thread.h>
#include <lib/base/message.h>
#include <lib/base/ebase.h>

class eBackgroundFileEraser: public eMainloop_native, private eThread, public sigc::trackable
{
	struct Message
	{
		int type;
		char *filename;
		enum
		{
			done,
			erase,
			quit
		};
		Message(int type=0, char *filename=0)
			:type(type), filename(filename)
		{}
	};
	eFixedMessagePump<Message> messages;
	eFixedMessagePump<Message> messages_thread;
	static eBackgroundFileEraser *instance;
	void gotMessage(const Message &message);
	void thread();
#ifndef SWIG
public:
#endif
	eBackgroundFileEraser();
	~eBackgroundFileEraser();
#ifdef SWIG
public:
#endif
	int erase(const char * filename);
	static eBackgroundFileEraser *getInstance() { return instance; }
	eSignal1<void, const char*> fileErased;

};

#endif
