from Components.Task import Task, Job, JobManager
from Tools.Downloader import downloadWithProgress
from Tools import Notifications

Notifications.notificationQueue.registerDomain("DownloadManager", _("Download Manager"), Notifications.ICON_DEFAULT)


class DownloadJob(Job):
	def __init__(self, url, file, title):
		Job.__init__(self, title)
		DownloadTask(self, url, file)

class DownloadTask(Task):
	def __init__(self, job, url, fileName):
		print "[DownloadTask] url='%s', fileName='%s'" %(url, fileName)
		Task.__init__(self, job, ("download task"))
		self.end = 100
		self.url = url
		self.local = fileName

	def prepare(self):
		self.error = None

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url,self.local)
		self.download.addProgress(self.http_progress)
		self.download.start().addCallback(self.http_finished).addErrback(self.http_failed)

	def http_progress(self, recvbytes, totalbytes):
		self.progress = int(self.end*recvbytes/float(totalbytes))

	def http_finished(self, string=""):
		print "[DownloadTask].http_finished " + str(string)
		Task.processFinished(self, 0)

	def http_failed(self, failure_instance=None, error_message=""):
		print "[DownloadTask].http_failed"
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			print "[DownloadTask].http_failed " + error_message
			Task.processFinished(self, 1)

downloadManager = JobManager(domain="DownloadManager")
downloadManager.in_background = True
