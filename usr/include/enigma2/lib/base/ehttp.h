#ifndef __lib_base_http_h__
#define __lib_base_http_h__

#include <lib/base/ebase.h>
#include <lib/base/thread.h>
#include <lib/base/message.h>
#include <curl/curl.h>
#include <string>
#include <vector>
#include <map>
#include <queue>
#include <stdint.h>
#include <mutex>
#include <atomic>

class eHTTPRequest
{
	DECLARE_REF(eHTTPRequest);
public:
	enum class Status
	{
		OK,
		CANCELLED,
		TIMEOUT,
		ERROR
	};

	eHTTPRequest(const std::string &url, sigc::slot<void, ePtr<eHTTPRequest>> doneCallback, const std::vector<std::string> &headers = std::vector<std::string>());
	~eHTTPRequest();

	void setup();
	void cancel();

	bool valid() const { return m_valid; }
	CURL *getCURL() { return m_curl; }

	const std::string &getURL() { return m_url; }
	bool getEffectiveURL(std::string &effectiveURL);

	static size_t chunkCallback0(void *contents, size_t size, size_t nmemb, void *userp);
	size_t chunkCallback(void *contents, size_t size, size_t nmemb);

	static size_t headerCallback0(void *contents, size_t size, size_t nmemb, void *userp);
	size_t headerCallback(void *contents, size_t size, size_t nmemb);

	bool finished() const { return m_finished; }

	Status getStatus() const { return m_status; }
	void setStatus(Status status) { m_status = status; }

	const std::vector<uint8_t> &getData() { return m_data; }
	const std::map<std::string, std::string> &getResponseHeaders() { return m_responseHeaders; }
	long getResponseCode() { return m_responseCode; }
	double getDownloadSpeed() { return m_downloadSpeed; }

	void finalize();
	bool headersOnly() const;
	void setHeadersOnly(bool headersOnly);
	void setPostData(const std::string &postData);

	int getUserId() const;
	void setUserId(int userId);


private:
	bool m_valid;
	std::atomic<bool> m_cancelled;
	CURL *m_curl;
	std::string m_url;
	std::vector<std::string> m_headers;
	bool m_finished;
	Status m_status;
	std::vector<uint8_t> m_data;
	sigc::slot<void, ePtr<eHTTPRequest>> m_doneCallback;
	std::map<std::string, std::string> m_responseHeaders;
	long m_responseCode;
	double m_downloadSpeed;
	bool m_headersOnly;
	std::string m_postData;
	int m_userId;
};

class eHTTP : public eMainloop_native, public eThread, public sigc::trackable
{
friend class eHTTPRequest;
public:
	static eHTTP& getInstance();

	void thread();

	static std::string urlEncode(const std::string &url);
	static std::string urlDecode(const std::string &url);

	bool addRequest(ePtr<eHTTPRequest> request);
private:
	eHTTP();
	~eHTTP();

	static int curlMultiSocketCallback0(CURL* easy, curl_socket_t fd, int action, void* userp, void* socketp);
	int curlMultiSocketCallback(CURL* easy, curl_socket_t fd, int action, void* socketp);

	static int curlMultiTimerCallback0(CURLM* multi, long timeout_ms, void* userp);
	int curlMultiTimerCallback(CURLM* multi, long timeout_ms);

	void curlTimeout();
	void curlPollActivity(int events, const ePtr<eSocketNotifier> &sn);

	void perform(int fd);

	void message(int request);

	CURLM *m_curlMultiHandle;
	ePtr<eTimer> m_timeoutTimer;
	std::map<int, ePtr<eSocketNotifier>> m_notifiers;
	std::vector<ePtr<eHTTPRequest>> m_activeRequests;

	std::queue<ePtr<eHTTPRequest>> m_queuedRequests;
	std::queue<ePtr<eHTTPRequest>> m_finishedRequests;

	eFixedMessagePump<int> m_pumpToThread;
	eFixedMessagePump<int> m_pumpToMain;

	std::mutex m_mtx;
};

#endif /* __lib_base_http_h__ */
