import sys, getopt

def is_dev() -> bool:
	"""Checks if the bot is run with the --development argument"""
	raw_arguments = sys.argv[1:]

	arguments, _ = getopt.getopt(raw_arguments, "d", ["development"])
	for arg, _ in arguments:
		if arg in ("--development", "-d"):
			return True
	return False