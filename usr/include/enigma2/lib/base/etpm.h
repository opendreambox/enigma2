#ifndef __lib_base_etpm_h__
#define __lib_base_etpm_h__

#include <lib/base/object.h>
#include <string>

#ifdef SWIG
#define __attribute__(...)
#endif

class eTPM
{
	E_DISABLE_COPY(eTPM)
	E_DECLARE_PRIVATE(eTPM)

public:
	enum data_type {
		DT_TPM_VERSION		= 0x02,
		DT_SERIAL		= 0x03,
		DT_LEVEL2_CERT		= 0x04,
		DT_LEVEL3_CERT		= 0x05,
		DT_FAB_CA_CERT		= 0x06,
		DT_DATABLOCK_SIGNED	= 0x07,
	};

	enum apdu_flag {
		APDU_READ	= (1 << 0),
		APDU_WRITE	= (1 << 1),
	};

	eTPM();
	~eTPM();

	enum cert_type {
		TPMD_DT_LEVEL2_CERT = DT_LEVEL2_CERT,
		TPMD_DT_LEVEL3_CERT = DT_LEVEL3_CERT,
	};
	std::string getCert(cert_type type) __attribute__ ((deprecated));
	std::string challenge(std::string rnd) __attribute__ ((deprecated));

	std::string getData(data_type type);
	std::string apdu(apdu_flag flags, unsigned char cla, unsigned char ins,
			 unsigned char p1, unsigned char p2, unsigned char len,
			 const std::string &data);
	std::string computeSignature(const std::string &data);
	std::string appCert(unsigned char n, const std::string &data);
};

#endif // __lib_base_etpm_h__
