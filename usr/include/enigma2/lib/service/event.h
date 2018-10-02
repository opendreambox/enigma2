#ifndef __lib_service_event_h
#define __lib_service_event_h

#ifndef SWIG
#include <time.h>
#include <list>
#include <set>
#include <string>
#include <tuple>
class Event;

#define MAX_LANG 40
extern const std::string ISOtbl[MAX_LANG][2];

#endif

#include <lib/base/object.h>
#include <lib/service/iservice.h>

#ifndef SWIG
struct eventData
{
	bool operator<(const eventData &e) const
	{
		return iso_639_language_code < e.iso_639_language_code;
	}
	time_t begin_time;
	uint32_t duration;
	uint16_t event_id;
	std::string iso_639_language_code;
	std::string title;
	std::string short_description;
	std::string extended_description;
};

class eventSet:public std::set<eventData>
{
public:
	std::set<eventData>::iterator find(std::string iso_639_language_code)
	{
		eventData d;
		d.iso_639_language_code = iso_639_language_code;
		return std::set<eventData>::find(d);
	}
	std::set<eventData>::const_iterator find(std::string iso_639_language_code) const
	{
		eventData d;
		d.iso_639_language_code = iso_639_language_code;
		return std::set<eventData>::find(d);
	}
};
#endif

SWIG_IGNORE(eComponentData);
struct eComponentData
{
	friend class eServiceEvent;
	uint8_t m_streamContent;
	uint8_t m_componentType;
	uint8_t m_componentTag;
	std::string m_iso639LanguageCode;
	std::string m_text;
public:
	eComponentData() { m_streamContent = m_componentType = m_componentTag = 0; }
	int getStreamContent(void) const { return m_streamContent; }
	int getComponentType(void) const { return m_componentType; }
	int getComponentTag(void) const { return m_componentTag; }
	std::string getIso639LanguageCode(void) const { return m_iso639LanguageCode; }
	std::string getText(void) const { return m_text; }
};

SWIG_ALLOW_OUTPUT_SIMPLE(eServiceReference);  // needed for SWIG_OUTPUT in eServiceEvent::getLinkageService

SWIG_IGNORE(eServiceEvent);
class eServiceEvent: public iObject
{
	DECLARE_REF(eServiceEvent);
	bool m_rtl_wa_applied;
	std::list<eComponentData> m_component_data;
	std::list<eServiceReference> m_linkage_services;
	time_t m_begin;
	int m_duration;
	int m_event_id;
	std::string m_event_name, m_short_description, m_extended_description;
	static std::string m_language;
	// .. additional info
	int applyData(const eventData &d);
	bool loadLanguage(Event *event, const std::string &lang, int tsidonid);
	int parseFromTxt(const std::string &_filename);
	std::string getFileExtension(const std::string &filename);
public:
#ifndef SWIG
	RESULT parseFrom(Event *evt, int tsidonid=0);
	RESULT parseFrom(const std::string &filename, int tsidonid=0);
	RESULT parseFrom(const eventSet &events, int tsidonid=0);
	static void setEPGLanguage( const std::string &language );
	size_t writeToEITBuffer(unsigned char *buffer);
#endif
	time_t getBeginTime() const { return m_begin; }
	int getDuration() const { return m_duration; }
	int getEventId() const { return m_event_id; }
	std::string getEventName() const { return m_event_name; }
	std::string getShortDescription() const { return m_short_description; }
	std::string getExtendedDescription(bool original=false);
	std::string getBeginTimeString() const;
	int getNumComponent() { return m_component_data.size(); }
	eComponentData *getComponentData(int tagnum) const;
	std::list<std::tuple<int, int, int, std::string, std::string> > getComponentData() const;
	int getNumOfLinkageServices() const { return m_linkage_services.size(); }
	SWIG_VOID(RESULT) getLinkageService(eServiceReference &SWIG_OUTPUT, eServiceReference &parent, int num) const;
};
SWIG_TEMPLATE_TYPEDEF(ePtr<eServiceEvent>, eServiceEvent);
SWIG_EXTEND(ePtr<eServiceEvent>,
	static void setEPGLanguage( const std::string &language )
	{
		extern void setServiceEventLanguage(const std::string &language);
		setServiceEventLanguage(language);
	}
);

#ifndef SWIG
SWIG_IGNORE(eDebugClass);
class eDebugClass: public iObject
{
	DECLARE_REF(eDebugClass);
public:
	int x;
	static void getDebug(ePtr<eDebugClass> &ptr, int x) { ptr = new eDebugClass(x); }
	eDebugClass(int i) { printf("build debug class %d\n", i); x = i; }
	~eDebugClass() { printf("remove debug class %d\n", x); }
};
SWIG_TEMPLATE_TYPEDEF(ePtr<eDebugClass>, eDebugClassPtr);
#endif

#endif
