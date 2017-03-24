#ifndef __dvb_frontend_h
#define __dvb_frontend_h

#include <lib/base/message.h>
#include <lib/base/thread.h>
#include <lib/dvb/idvb.h>
#include <linux/dvb/frontend.h>

#ifdef SWIG
%feature("notabstract") eDVBFrontendParameters;
#endif

class eDVBFrontendParameters: public iDVBFrontendParameters
{
	DECLARE_REF(eDVBFrontendParameters);
	union
	{
		eDVBFrontendParametersSatellite sat;
		eDVBFrontendParametersCable cable;
		eDVBFrontendParametersTerrestrial terrestrial;
	};
	int m_types;
	int m_flags;
public:
	eDVBFrontendParameters();
	~eDVBFrontendParameters()
	{
	}

	SWIG_VOID(RESULT) getSystem(int &SWIG_OUTPUT) const;
	SWIG_VOID(RESULT) getDVBS(eDVBFrontendParametersSatellite &SWIG_OUTPUT) const;
	SWIG_VOID(RESULT) getDVBC(eDVBFrontendParametersCable &SWIG_OUTPUT) const;
	SWIG_VOID(RESULT) getDVBT(eDVBFrontendParametersTerrestrial &SWIG_OUTPUT) const;

	RESULT setDVBS(const eDVBFrontendParametersSatellite &p, bool no_rotor_command_on_tune=false);
	RESULT setDVBC(const eDVBFrontendParametersCable &p);
	RESULT setDVBT(const eDVBFrontendParametersTerrestrial &p);
	SWIG_VOID(RESULT) getFlags(unsigned int &SWIG_NAMED_OUTPUT(flags)) const { flags = m_flags; return 0; }
	RESULT setFlags(unsigned int flags) { m_flags = flags; return 0; }
#ifndef SWIG
	RESULT calculateDifference(const iDVBFrontendParameters *parm, int &, bool exact) const;

	RESULT getHash(unsigned long &) const;
	RESULT calcLockTimeout(unsigned int &) const;
#endif
};

#ifndef SWIG

#include <lib/dvb/sec.h>
class eSecCommandList;

class eDVBFrontend: public iDVBFrontend, public eThread, public eMainloop_native, public sigc::trackable
{
public:
	enum {
		NEW_CSW,
		NEW_UCSW,
		NEW_TONEBURST,
		CSW,                  // state of the committed switch
		UCSW,                 // state of the uncommitted switch
		TONEBURST,            // current state of toneburst switch
		NEW_ROTOR_CMD,        // prev sent rotor cmd
		NEW_ROTOR_POS,        // new rotor position (not validated)
		ROTOR_CMD,            // completed rotor cmd (finalized)
		ROTOR_POS,            // current rotor position
		ROTOR_PENDING,        // rotor cmd pending
		LINKED_PREV_PTR,      // prev double linked list (for linked FEs)
		LINKED_NEXT_PTR,      // next double linked list (for linked FEs)
		SATPOS_DEPENDS_PTR,   // pointer to FE with configured rotor (with twin/quattro lnb)
		FREQ_OFFSET,          // frequency offset for tuned transponder
		CUR_DVBS_VOLTAGE,     // current dvb-s(2) voltage
		CUR_DVBT_VOLTAGE,     // current dvb-t voltage
		CUR_TONE,             // current continuous tone
		SATCR,                // current SatCR
		NUM_DATA_ENTRIES
	};
	eSignal1<void, iDVBFrontend*> m_stateChanged;
private:
	DECLARE_REF(eDVBFrontend);
	bool m_dvbt_5V_via_proc;
	bool m_simulate;
	int m_types_enabled; // set from python
	int m_types;
	eDVBFrontend *m_simulate_fe; // only used to set frontend type in dvb.cpp
	int m_dvbid;
	int m_slotid;
	int m_fd;
	bool m_forced_timeout;
	bool m_rotor_mode;
	bool m_need_rotor_workaround;
	bool m_seen_first_event;
	bool m_dvb_t2_auto_delsys;
	char m_filename[128];
	char m_description[128];
	static int dvb_api_minor;
	dvb_frontend_parameters parm;
	typedef struct {
		eDVBFrontendParametersSatellite sat;
		eDVBFrontendParametersCable cab;
		eDVBFrontendParametersTerrestrial ter;
		int type;
	} fe_parm_t;

	fe_parm_t oparm, newparm;

	int m_state;
	ePtr<iDVBSatelliteEquipmentControl> m_sec;
	ePtr<eSocketNotifier> m_sn;
	int m_tuning;
	ePtr<eTimer> m_timeout, m_tuneTimer, m_lostLockTimer;
	unsigned int m_sec_lock; // this is a bitmask (1 << m_dvbid)

	eSecCommandList m_sec_sequence;

	long m_data[NUM_DATA_ENTRIES];

	int m_idleInputpower[2];  // 13V .. 18V
	int m_runningInputpower;

	int m_timeoutCount; // needed for timeout
	int m_retryCount; // diseqc retry for rotor

	bool m_ml_running;
	eSingleLock m_sec_mutex, m_sec_lock_mutex;
	eFixedMessagePump<int> m_pump, m_thread_pump;
	void thread();
	void gotMessage(int);

	void feEvent(int);
	void timeout();
	void lostLock(); // called by m_lostLockTimer
	void tuneLoop();  // called by m_tuneTimer from tune thread
	int tuneLoopInt();
	void setFrontend(bool recvEvents=true);
	bool setSecSequencePos(int steps);
	static int PriorityOrder;
public:
	eDVBFrontend(int adap, int fe, int &ok, bool simulate=false, eDVBFrontend *simulate_fe=NULL);
	virtual ~eDVBFrontend();

	int readInputpower();
	RESULT getFrontendType(int &type);
	RESULT getTunedType(int &type);
	RESULT tune(const iDVBFrontendParameters &where);
	RESULT prepare_sat(const eDVBFrontendParametersSatellite &, unsigned int timeout);
	RESULT prepare_cable(const eDVBFrontendParametersCable &);
	RESULT prepare_terrestrial(const eDVBFrontendParametersTerrestrial &);
	RESULT connectStateChange(const sigc::slot1<void,iDVBFrontend*> &stateChange, ePtr<eConnection> &connection);
	RESULT getState(int &state);
	RESULT setTone(int tone);
	RESULT setVoltage(int voltage, iDVBFrontend *child_fe=NULL);
	RESULT sendDiseqc(const eDVBDiseqcCommand &diseqc);
	RESULT sendToneburst(int burst);
	RESULT setSEC(iDVBSatelliteEquipmentControl *sec);
	RESULT setSecSequence(eSecCommandList &list);
	RESULT getData(int num, long &data);
	RESULT setData(int num, long val);

	int readFrontendData(int type); // bitErrorRate, signalPower, signalQualitydB, signalQuality, locked, synced
	RESULT getFrontendStatus(FrontendDataMap &dest);
	RESULT getTransponderData(FrontendDataMap &dest, bool original);
	RESULT getFrontendData(FrontendDataMap &dest);
	eSignal1<void, iDVBFrontend*> &getStateChangeSignal();

	int isCompatibleWith(ePtr<iDVBFrontendParameters> &feparm);
	int getDVBID() { return m_dvbid; }
	int getSlotID() { return m_slotid; }
	bool setSlotInfo(std::tuple<int, std::string, int, int, std::string>&); // get a tuple (slotid, slotdescr, enabled, dvbid, input_name)
	static void setTypePriorityOrder(int val) { PriorityOrder = val; }
	static int getTypePriorityOrder() { return PriorityOrder; }

	void reopenFrontend();
	int openFrontend();
	int closeFrontend(bool force=false, bool no_delayed=false);
	void preClose();
	const char *getDescription() const { return m_description; }
	bool is_simulate() const { return m_simulate; }
};

#endif // SWIG
#endif
