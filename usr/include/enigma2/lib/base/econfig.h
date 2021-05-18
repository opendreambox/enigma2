#ifndef __lib_base_econfig_h__
#define __lib_base_econfig_h__

#include <map>
#include <string>

class eConfig : std::map<std::string, std::string>
{
	friend class Enigma;

	std::string m_filename;

	bool load();
	//bool save() const;

	void insert(const std::string &kvpair);
	void insert(const std::string &key, const std::string &value);

public:
	eConfig(const std::string &filename);

	std::string value(const std::string &key, const std::string &defaultValue = std::string(), bool foreignThread=false) const;
	bool boolean(const std::string &key, bool defaultValue = false) const;
};

#endif /* __lib_base_econfig_h__ */
