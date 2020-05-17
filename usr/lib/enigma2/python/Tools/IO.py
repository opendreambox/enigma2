from __future__ import print_function
from os import fchmod, fsync, path, rename, unlink
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
import six


def runPipe(cmd):
	p = Popen(cmd, stdout=PIPE, close_fds=True)
	output = p.stdout.read()
	p.stdout.close()
	return p.wait(), output.splitlines()

def saveFile(filename, data, mode=0o644):
	tmpFilename = None
	try:
		f = NamedTemporaryFile(prefix='.%s.' % path.basename(filename), dir=path.dirname(filename), delete=False)
		tmpFilename = f.name
		if isinstance(data, list):
			for x in data:
				f.write(six.ensure_binary(x))
		else:
			f.write(six.ensure_binary(data))
		f.flush()
		fsync(f.fileno())
		fchmod(f.fileno(), mode)
		f.close()
		rename(tmpFilename, filename)
	except Exception as e:
		print('saveFile: failed to write to %s: %s' % (filename, e))
		if tmpFilename and path.exists(tmpFilename):
			unlink(tmpFilename)
		return False

	return True
