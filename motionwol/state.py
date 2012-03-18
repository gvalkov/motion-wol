# encoding: utf-8

# addr : mac
arp = {}

# host : last time host was woken up (a time.time())
wakelog = {}

# host : last successful ping time (a time.time())
pinglog = {}

# time of last and second to last motion events
last_motion = [None]
prev_motion = [0]

# list of dsl.Rule objects
config = []
