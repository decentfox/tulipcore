import gevent
from asyncio import get_event_loop_policy

hub = gevent.get_hub()
loop_id = id(hub.loop)

# Destroy hub. Does not destroy loop if not explicitly told to.
hub.destroy()
hub = gevent.get_hub()
assert id(hub.loop) == loop_id, hub

saved_loop = hub.loop
# Destroy hub including loop.
hub.destroy(destroy_loop=True)
try:
    saved_loop.remove_reader(-1)
    assert False, saved_loop
except AttributeError:
    pass

# Create a new loop.
policy = get_event_loop_policy()
new_loop = policy.new_event_loop()
policy.set_event_loop(new_loop)

# Create new hub
hub = gevent.get_hub()
assert hub.loop is new_loop, hub
