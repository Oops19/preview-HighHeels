from high_heels.modinfo import ModInfo
from sims4communitylib.events.event_handling.common_event_registry import CommonEventRegistry
from sims4communitylib.events.sim.events.sim_spawned import S4CLSimSpawnedEvent
from sims4communitylib.events.zone_spin.events.zone_early_load import S4CLZoneEarlyLoadEvent
from sims4communitylib.events.zone_spin.events.zone_late_load import S4CLZoneLateLoadEvent
from sims4communitylib.events.zone_spin.events.zone_teardown import S4CLZoneTeardownEvent
from sims4communitylib.events.zone_update.events.zone_update_event import S4CLZoneUpdateEvent

from sims4communitylib.utils.common_log_registry import CommonLog, CommonLogRegistry

log: CommonLog = CommonLogRegistry.get().register_log(ModInfo.get_identity().author, ModInfo.get_identity().name)
we_are_live = False

class ExampleEventListener:
    # In order to listen to an event, your function must match these criteria:
    # - The function is static (staticmethod).
    # - The first and only required argument has the name "event_data".
    # - The first and only required argument has the Type Hint for the event you are listening for.
    # - The argument passed to "handle_events" is the name of your Mod.
    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def handle_event(event_data: S4CLZoneTeardownEvent):
        global log, ayr
        log.debug("S4CLZoneTeardownEvent" + str(event_data.zone) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))
        ayr.stop()

    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def handle_event(event_data: S4CLZoneEarlyLoadEvent):
        global log, ayr
        log.debug("S4CLZoneEarlyLoadEvent" + str(event_data.zone) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))
        ayr.start()

    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def handle_event(event_data: S4CLZoneLateLoadEvent):
        global log, ayr
        log.debug("S4CLZoneLateLoadEvent" + str(event_data.zone) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))
        ayr.start(True)

    #@staticmethod
    #@CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    #def handle_event(event_data: S4CLZoneUpdateEvent):
    #    global log
    #    log.debug("S4CLZoneUpdateEvent type={type(event_data)}")

    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def handle_event(event_data: S4CLSimSpawnedEvent):
        global log, ayr
        log.debug("S4CLSimSpawnedEvent type={type(event_data)}")
        # log.debug("S4CLSimSpawnedEvent" + str(event_data.sim_id) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))


class AccionYReaccion:
    def __init__(self):
        global log
        log.debug("AccionYReaccion: init()")
 
    def start(self, process_all_sims=False):
        global we_are_live
        we_are_live = True
        if process_all_sims:
            pass
            # Process all Sims

    def stop(self):
        global we_are_live
        we_are_live = False
        # Do no longer process a single sim


ayr = AccionYReaccion()
