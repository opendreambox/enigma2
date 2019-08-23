#ifndef __lib_base_http_h__
#define __lib_base_http_h__

#include <lib/base/ebase.h>
#include <curl/curl.h>
#include <string>
#include <vector>
#include <map>
#include <stdint.h>

class eHTTPRequest
{
	DECLARE_REF(eHTTPRequest);
public:
	eHTTPRequest(const std::string &url, sigc::slot<void, ePtr<eHTTPRequest>> doneCallback, const std::vector<std::string> &headers = std::vector<std::string>());
	~eHTTPRequest();

	bool valid() const { return m_valid; }
	CURL *getCURL() { return m_curl; }

	const std::string &getURL() { return m_url; }

	static size_t chunkCallback0(void *contents, size_t size, size_t nmemb, void *userp);
	size_t chunkCallback(void *contents, size_t size, size_t nmemb);

	static size_t headerCallback0(void *contents, size_t size, size_t nmemb, void *userp);
	size_t headerCallback(void *contents, size_t size, size_t nmemb);

	bool finished() const { return m_finished; }
	const std::vector<uint8_t> &getData() { return m_data; }
	const std::map<std::string, std::string> &getResponseHeaders() { return m_responseHeaders; }
	long getResponseCode() { return m_responseCode; }

	void finalize();

private:
	bool m_valid;
	CURL *m_curl;
	std::string m_url;
	bool m_finished;
	std::vector<uint8_t> m_data;
	sigc::slot<void, ePtr<eHTTPRequest>> m_doneCallback;
	std::map<std::string, std::string> m_responseHeaders;
	long m_responseCode;
};

class eHTTP : public eMainloop_native, public sigc::trackable
{
friend class eHTTPRequest;
public:
	eHTTP();
	~eHTTP();

	bool addRequest(ePtr<eHTTPRequest> request);
private:

	static int curlMultiSocketCallback0(CURL* easy, curl_socket_t fd, int action, void* userp, void* socketp);
	int curlMultiSocketCallback(CURL* easy, curl_socket_t fd, int action, void* socketp);

	static int curlMultiTimerCallback0(CURLM* multi, long timeout_ms, void* userp);
	int curlMultiTimerCallback(CURLM* multi, long timeout_ms);

	void curlTimeout();
	void curlPollActivity(int events, const ePtr<eSocketNotifier> &sn);

	void perform(int fd);

	CURLM *m_curlMultiHandle;
	ePtr<eTimer> m_timeoutTimer;
	std::map<int, ePtr<eSocketNotifier>> m_notifiers;
	std::vector<ePtr<eHTTPRequest>> m_activeRequests;
};

#endif /* __lib_base_http_h__ */
