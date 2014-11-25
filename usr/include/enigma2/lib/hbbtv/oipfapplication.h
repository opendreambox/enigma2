#ifndef __lib_hbbtv_eoipfapplication_h_
#define __lib_hbbtv_eoipfapplication_h_

#include <lib/base/sigc.h>
#include <dvbsi++/application_information_section.h>

class eOipfApplication: public sigc::trackable
{
public:
	enum ControlCodes {
		CONTROL_CODE_AUTOSTART = 0x01,
		CONTROL_CODE_PRESENT = 0x02,
		CONTROL_CODE_DESTROY = 0x03,
		CONTROL_CODE_KILL = 0x04,
		CONTROL_CODE_PREFETCH = 0x05,
		CONTROL_CODE_REMOTE = 0x06,
		CONTROL_CODE_DISABLED = 0x07,
		CONTROL_CODE_PLAYBACK_AUTOSTART = 0x08,
	};

	enum UsageTypes {
		USAGE_TYPE_TEXT = 0x01,
	};

	enum Visibility {
		VISIBILITY_NOT_VISIBLE_ALL = 0x00,
		VISIBILITY_NOT_VISIBLE_USERS = 0x01,
		VISIBILITY_VISIBLE_ALL = 0x11,
	};

#ifdef SWIG
private:
#endif
	eOipfApplication();
	eOipfApplication(const ApplicationInformation *ai);
	bool checkVersion() { return m_versionCheck; };
#ifdef SWIG
public:
#endif
	~eOipfApplication();
	static eOipfApplication getById(const std::string &id);

	bool isValid(){ return m_valid; };
	uint32_t getOrganisationId() const { return m_organisationId; };
	uint16_t getApplicationId() const { return m_applicationId; };
	uint16_t getApplicationProfile() const { return m_applicationProfile; };
	uint8_t getPriority() const { return m_applicationPriority; };
	uint8_t getUsageType() const { return m_usageType; };
	uint8_t getControlCode() const { return m_applicationControlCode; };
	uint8_t getServiceBoundFlag() const { return m_serviceBoundFlag; };
	uint8_t getVisibility() const { return m_visibility; };
	const std::string &getId() const { return m_id; };
	const std::string &getName() const { return m_applicationName; };
	const std::string &getInitialPath() const { return m_initialPath; };
	const std::string &getUrlBase() const { return m_urlBase; };

private:
	bool m_valid;
	bool m_versionCheck;
	uint32_t m_organisationId;
	uint16_t m_applicationId;
	uint16_t m_applicationProfile;
	uint8_t m_applicationControlCode;
	uint8_t m_serviceBoundFlag;
	uint8_t m_visibility;
	uint8_t m_applicationPriority;
	uint8_t m_usageType;
	std::string m_id;
	std::string m_applicationName;
	std::string m_initialPath;
	std::string m_urlBase;
};

#endif
