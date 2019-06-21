# !!! WARNING !!!
# The steps are double-linked which means that the GC cannot collect them without unlinking them!
# Call the cleanup method when done with this or you'll have memleak and other unwanted side-effects!
class PrioritizedStepper(object):
	def __init__(self):
		self._steps = {}
		self._sortedPrios = []
		self._currentStep = None
		self._currentPrio = -1

	def _doubleLinkSteps(self, steps):
		if not isinstance(steps, list):
			return

		lastStep = None
		for step in steps:
			if lastStep:
				lastStep.NXT = step
				step.PRV = lastStep
			lastStep = step
		if lastStep:
			lastStep.PRV = steps[-2]

	def add(self, parent, prio, steps):
		while prio in self._steps.keys():
			prio += 1

		if isinstance(steps, list) and len(steps) == 1:
			steps = self._instantiateStep(steps[0], parent)
		if isinstance(steps, list):
			instances = []
			for step in steps:
				instances.append(self._instantiateStep(step,parent))
			steps = instances
			self._doubleLinkSteps(steps)
		else:
			steps = self._instantiateStep(steps, parent)

		self._steps[prio] = steps
		self._sortedPrios = self._steps.keys()
		self._sortedPrios.sort()

	def cleanup(self):
		for prio, steps in self._steps.iteritems():
			if isinstance(steps, list):
				for step in steps:
					step.NXT = None
					step.PRV = None
			else:
				steps.NXT = None
				steps.PRV = None
		self._steps = {}

	def _instantiateStep(self, step, parent):
		if isinstance(step, dict):
			args = step.get("args", [])
			return step["class"](parent, *args)
		return step(parent)

	def next(self):
		if self._currentStep and self._currentStep.NXT:
			self._currentStep =  self._currentStep.NXT
			return self._currentStep
		return self._nextPrio()

	def _nextPrio(self):
		if self._currentPrio == -1:
			self._currentPrio = 0
		else:
			self._currentPrio += 1
		if self._currentPrio < len(self._sortedPrios):
			step = self._steps[self._sortedPrios[self._currentPrio]]
			if isinstance(step, list):
				self._currentStep = step[0]
			else:
				self._currentStep = step
			return self._currentStep
		return None

	def previous(self):
		if self._currentPrio < 0:
			return None
		if self._currentStep and self._currentStep.PRV != None:
			self._currentStep = self._currentStep.PRV
			return self._currentStep
		return self._previousPrio()
		#decrement to prev priofall

	def _previousPrio(self):
		self._currentPrio -= 1
		if self._currentPrio < 0:
			self._currentPrio = 0
			return None
		step = self._steps[self._sortedPrios[self._currentPrio]]
		if isinstance(step, list):
			self._currentStep = step[-1]
		else:
			self._currentStep = step
		return self._currentStep

	def skipForward(self):
		return self._nextPrio()

	def skipBackward(self):
		return self._previousPrio()
