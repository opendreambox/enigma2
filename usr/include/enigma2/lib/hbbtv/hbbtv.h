#ifndef __lib_hbbtv_hbbtv_h_
#define __lib_hbbtv_hbbtv_h_

#include "oipfapplication.h"

#include <lib/base/esignal.h>
#include <lib/service/iservice.h>
#include <lib/service/event.h>

#if QT_VERSION >= 0x050000
#define HBBTV_USER_AGENT "Mozilla/5.0 (Linux mips; U;HbbTV/1.1.1 (+RTSP;Dream Property GmbH;Dreambox;1.1;1.0;) CE-HTML/1.0; en) AppleWebKit/538.1 no/Volksbox QtWebkit OIPF/1.1";
#else
#define HBBTV_USER_AGENT "Mozilla/5.0 (Linux mips; U;HbbTV/1.1.1 (+RTSP;Dream Property GmbH;Dreambox;0.1a;1.0;) CE-HTML/1.0; en) AppleWebKit/535.19 no/Volksbox QtWebkit/2.2";
#endif


class eDVBServiceAITHandler;

class eHbbtv : public sigc::trackable
{
	static eHbbtv *instance;
	bool m_aitSignalsEnabled;
	int m_streamState;
	ePtr<eConnection> m_serviceEventConnection;
	std::list<eServiceReference> m_serviceList;
	eServiceReference m_currentBouquet;
	eServiceReference m_currentService;
	ePtr<iPlayableService> m_playableService;
	ePtr<eConnection> m_serviceEventConn;
	eDVBServiceAITHandler *m_aitHandler;
	std::map< std::string, std::map<std::string, eOipfApplication> >m_applications;

	void aitChanged(int pid);
	std::vector<std::string> split(const std::string &s, char delim, int limit = 0);
	void checkApp(const eOipfApplication *app);
	bool addApplication(const eOipfApplication &app, std::map<std::string, eOipfApplication> *currentServiceApps);
	bool isStreaming();

#ifdef SWIG
	eHbbtv();
	~eHbbtv();
#endif
public:
#ifndef SWIG
	eHbbtv();
	~eHbbtv();
#endif

	static const int VERSION_MAJOR = 1;
	static const int VERSION_MINOR = 1;
	static const int VERSION_MICRO = 1;

	enum EventTypes{
		EVENT_NOW = 0,
		EVENT_NEXT = 1,
	};

	enum PlayStates {
		BROADCAST_STATE_UNREALIZED = 0,
		BROADCAST_STATE_CONNECTING,
		BROADCAST_STATE_PRESENTING,
	};

	enum ChannelErrors{
		CHANNEL_ERROR_NOT_SUPPORTED = 0,
		CHANNEL_ERROR_TUNE_FAILED,
		CHANNEL_ERROR_TUNER_FOREIGN_LOCK,
		CHANNEL_ERROR_PARENTAL_LOCK,
		CHANNEL_ERROR_CANNOT_DECRYPT,
		CHANNEL_ERROR_UNKNOWN,
		CHANNEL_ERROR_SWITCH_INTERRUPTED,
		CHANNEL_ERROR_LOCKED_BY_RECORD,
		CHANNEL_ERROR_RESOLVE_FAILED,
		CHANNEL_ERROR_BANDWITH_INSUFFICIENT,
		CHANNEL_ERROR_CANNOT_ZAP,
	};

	enum StreamPlayStates {
		STREAM_STATE_STOPPED = 0,
		STREAM_STATE_PLAYING,
		STREAM_STATE_PAUSED,
		STREAM_STATE_CONNECTING,
		STREAM_STATE_BUFFERING,
		STREAM_STATE_FINISHED,
		STREAM_STATE_ERROR,
	};

	enum StreamErrors {
		STREAM_ERROR_NONE = 0,
		STREAM_ERROR_UNSUPPORTED,
		STREAM_ERROR_CONNECTING,
		STREAM_ERROR_UNKNOWN,
	};

	//python accessible
	static eHbbtv *getInstance();
	void setAitSignalsEnabled(bool enabled){ m_aitSignalsEnabled = enabled; };
	void setServiceList(std::string sref);
	void setStreamState(int state);
	const eOipfApplication getApplication(const std::string &id);
	const std::string resolveApplicationLocator(const std::string &dvbUrl);
	std::list<std::pair<std::string, std::string> > getApplicationIdsAndName();
	void pageLoadFinished();

#ifndef SWIG
	//C++ only
	const std::string getCurrentServiceTriplet();
	const eServiceReference &getCurrentService();
	void setCurrentService(eServiceReference service, ePtr<iPlayableService> &playableService);
	void playService(const std::string &sref);
	void playStream(const std::string &uri);
	void pauseStream();
	bool seekStream(pts_t to);
	void stopStream();
	void nextService();
	void prevService();
	void onCurrentServiceStop();
	void onCurrentServiceEvent(iPlayableService *playableService, int what);
	ePtr<iPlayableService> getPlayableService();
	long getPlayTime();
	long getPlayPosition();
	void setVolume(int volume);
	const std::list<eServiceReference> getServiceList();
	ePtr<eServiceEvent> getEvent(int nownext);
	void setVideoWindow(unsigned int x, unsigned int y, unsigned int w, unsigned int h);
	void unsetVideoWindow();
	void showCurrent();
	void hideCurrent();
	void createApplication(const std::string &uri);

	Signal0<void> currentServiceChanged;
	Signal1<void, int> serviceChangeError;
	Signal1<void, int> streamPlayStateChanged;
	Signal0<void> serviceListChanged;
	Signal0<void> loadFinished;
#endif

	/* void playServiceRequest(std::string); */
	eSignal1<void, const char *> playServiceRequest;
	/* void playStreamRequest(std::string); */
	eSignal1<void, const char *> playStreamRequest;
	/* void pauseStreamRequest(); */
	eSignal0<void> pauseStreamRequest;
	/* void seekStreamRequest(pts_t); */
	eSignal1<void, pts_t> seekStreamRequest;
	/* void stopStreamRequest(); */
	eSignal0<void> stopStreamRequest;
	/* void nextServiceRequest(); */
	eSignal0<void> nextServiceRequest;
	/* void prevServiceRequest(); */
	eSignal0<void> prevServiceRequest;
	/* void setVolumeRequest(int); */
	eSignal1<void, int> setVolumeRequest;
	/* void setVideoWindowRequest(unsigned int, unsigned int, unsigned int, unsigned int); */
	eSignal4<void, unsigned int, unsigned int, unsigned int, unsigned int> setVideoWindowRequest;
	/* void unsetVideoWindowRequest(); */
	eSignal0<void> unsetVideoWindowRequest;
	/* void aitInvalidated() */
	eSignal0<void> aitInvalidated;
	/* void redButtonAppplicationReady(std::string); */
	eSignal1<void, const char*> redButtonAppplicationReady;
	/* void textApplicationReady(std::string); */
	eSignal1<void, const char*> textApplicationReady;
	/* void createApplicationRequest(std::string); */
	eSignal1<void, const char*> createApplicationRequest
	/* void show() */;
	eSignal0<void> show;
	/* void hide() */;
	eSignal0<void> hide;
};

#endif /* __lib_hbbtv_hbbtv_h_ */
