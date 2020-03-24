#ifndef __lib_components_file_watcher_h
#define __lib_components_file_watcher_h
#include <lib/base/thread.h>
#include <lib/base/message.h>
#include <lib/base/ebase.h>
#include <lib/base/elock.h>
#include <lib/base/esignal.h>

#include <queue>
#include <future>
#include <sys/inotify.h>

class eFileEvent {
	int m_wd;
	uint32_t m_mask;
	uint32_t m_cookie;
	std::string m_name;
	std::string m_path;
	std::string m_movedFrom;
	std::string m_movedTo;
#ifdef SWIG
	eFileEvent();
#endif
public:
	enum {
		ACCESS = IN_ACCESS,
		MODIFY = IN_MODIFY,
		ATTRIB = IN_ATTRIB,
		CLOSE_WRITE = IN_CLOSE_WRITE,
		CLOSE_NOWRITE = IN_CLOSE_NOWRITE,
		CLOSE = IN_CLOSE,
		OPEN = IN_OPEN,
		MOVED_FROM = IN_MOVED_FROM,
		MOVED_TO = IN_MOVED_TO,
		MOVE = IN_MOVE,
		CREATE = IN_CREATE,
		DELETE = IN_DELETE,
		DELETE_SELF = IN_DELETE_SELF,
		MOVE_SELF = IN_MOVE_SELF,
		ISDIR = IN_ISDIR,
	};
#ifndef SWIG
	eFileEvent(struct inotify_event *event, std::string path=std::string(""));
#endif
	int getWd() const { return m_wd; };
	uint32_t getMask() const { return m_mask; };
	uint32_t getCookie() const { return m_cookie; };
	const std::string getName() const { return m_name; };
	const std::string getPath() const { return m_path; };
	std::string getFullPath() { return std::string(std::string(m_path) + "/" + std::string(m_name)); };
	const std::string getMovedFrom() const { return m_movedFrom; };
	const std::string getMovedTo() const { return m_movedTo; };

#ifndef SWIG
	void setWd(int wd){ m_wd = wd; };
	void setMask(uint32_t mask){ m_mask = mask; };
	void setCookie(uint32_t cookie){ m_cookie = cookie; };
	void setName(const std::string &name){ m_name = name; };
	void setPath(const std::string &path){ m_path = path; };
	void setMovedFrom(const std::string &movedFrom){ m_movedFrom = movedFrom; };
	void setMovedTo(const std::string &movedTo){ m_movedTo = movedTo; };
#endif
};

/**
 * Use an eFileWatch to monitor a file or directory (recursively if required) for access/changes
 * Watches are "self-managed" and do all required interaction with the eFileMonitor instance
 * Manual interaction with eFileMonitor is not recommended!
 */
class eFileWatch : public sigc::trackable
{
	pthread_mutex_t m_startstop_mutex;
	pthread_mutex_t m_child_mutex;
	friend class eFileMonitor;

	int m_wd;
	uint32_t m_mask;
	bool m_recursive; //recursivley watch the given directory, all events of siblings will bubble to the very parent eFileWatch and be signalled from there
	bool m_destroyed;
	std::string m_directory;

	std::map<std::string, eFileWatch*> m_child_lut;
	std::vector<eFileWatch*> m_children;
	std::future<void> m_child_future;

	eFileWatch* m_parent;

	void destroy();

	/**
	 * !! Do not call createDirectChildWatches() twice, it's almost guaranteed to break things
	 */
	void createDirectChildWatches();

public:
	/**
	 * Creates a new FileWatch for a File or Directory
	 * @param directory
	 * @param mask
	 * @param recursive
	 * @param parent
	 */
	eFileWatch(std::string directory,  bool recursive=false, uint32_t mask = eFileEvent::CLOSE_WRITE | eFileEvent::MOVE | eFileEvent::CREATE | eFileEvent::DELETE | eFileEvent::DELETE_SELF | eFileEvent::MOVE_SELF, eFileWatch* parent=0);
	~eFileWatch();

	/**
	 * Start watching the directory of this eFileWatch.
	 * Calls addWatch on eFileMonitor::getInstance() and sets the watch descritpor id (m_wd)
	 * @return true if watch is now running for the eFileWatch instance an all of it's child-Watches, else false
	 */
	bool startWatching();

	/**
	 * Stop watching the directory of this eFileWatch.
	 * Class removeWatch on eFileMonitor::getInstance() and sets the watch descriptor id to 0
	 * @return
	 */
	bool stopWatching();

	bool isWatching() const;

#ifndef SWIG
	/**
	 * This should only be called for inotify events valid for this eFileWatch.
	 * If the current instance has a non-zero parent no signal will be raised but the event will bubble to the parent.
	 * Event-signals will only be raised on parentless eFileWatches!
	 * @param event
	 */
	void event(eFileEvent event, bool bubbled=false);
	void removeChild(eFileWatch* child);
#endif

	const int getWd() const { return m_wd; };
	const std::string getDirectory() const { return m_directory; };
	const uint32_t getMask() const { return m_mask; };

	void setDirectory(const std::string &dir){ m_directory = dir; };

	eSignal2<void, eFileWatch*, eFileEvent> fileChanged;
};
SWIG_EXTEND(eFileWatch,
	bool operator==(const eFileWatch &fw) const { return &fw == self; }
);

#ifndef SWIG

/**
 * Monitors the Filesystem for changes (based on inotify).
 * Do not use this class directly unless you really know why.
 * Use eFileWatch instances instead, they handle all the tricky stuff properly.
 */
class eFileMonitor: public eMainloop_native, public eThread, public sigc::trackable
{
	int m_fd;
	uint64_t m_watchcount; //watches total
	ePtr<eSocketNotifier> m_sn;
	eSingleLock m_watch_lock, m_queue_lock;
	std::queue<eFileEvent> m_eventqueue;
	//lookup-tables
	std::map<std::string, int> m_dir_wd; //key: directory, value: watch-descriptor-id
	std::map<int, std::list<eFileWatch*>> m_wd_watches; //key: watch-descriptor-id, value: related eFileWatch, required for getting all eFileWatches for an event

	struct Message
	{
		int type;
		int count;
		enum{
			process=0,
			quit,
		};
		Message(int type=0, int count=0): type(type), count(count){};
	};

	static eFileMonitor *instance;

	eFixedMessagePump<Message> messages_from_thread;
	eFixedMessagePump<Message> messages_to_thread;

	void gotMessage(const Message &msg);
	void thread();
	void readEvents(int what);
	int processInotifyEvents();
	void onWatchMoved(eFileWatch *watch, const eFileEvent &event);

public:
	eFileMonitor();
	~eFileMonitor();

	static eFileMonitor *getInstance();

	int addWatch(eFileWatch *watch);
	bool removeWatch(eFileWatch *watch);
	std::list<eFileWatch*> getWatches(int wd);

	/**
	 * processEvents(bool finished)
	 * emitted when processing of events will start (finished=false) and finish (finished=true).
	 *
	 * Can be used to encapsulate event-based actions into a single database transaction or do some other kind of batch-processing on the receiver-side
	 */
	Signal1<void, bool> processEvents;
};

#endif

#endif
