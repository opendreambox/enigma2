#ifndef __lib_base_core_h__
#define __lib_base_core_h__

#include <lib/base/econfig.h>

class Enigma
{
	static eConfig g_settings;

public:
	static const eConfig &settings() __attribute__((const));

	static void setCmdlineOption(const std::string &key, bool value);
	static void setCmdlineOption(const std::string &key, const std::string &value);
};

#endif /* __lib_base_core_h__ */
