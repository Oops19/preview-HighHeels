#
# LICENSE https://creativecommons.org/licenses/by/4.0/ https://creativecommons.org/licenses/by/4.0/legalcode
# © 2021 https://github.com/Oops19
#

import ast
import os
import time
from typing import Union

import services
import sims4
import sims4.commands
from high_heels.enums.constants import Oops19Constants
from high_heels.enums.hh_constants import HighHeelsConstants

from high_heels.modinfo import ModInfo
from high_heels.utilities.helper_standalone import O19Helper, O19Sim
from high_heels.utilities.manage_sim_object import Object4Sim, ManageSimObject
from high_heels.slider_store import SliderStore
from high_heels.utilities.walkstyle import Oops19Walkstyle
from libraries.o19_ts4_folders_s4cl import TS4_Folders_S4CL
from objects import ALL_HIDDEN_REASONS
from protocolbuffers import PersistenceBlobs_pb2
from protocolbuffers.PersistenceBlobs_pb2 import BlobSimFacialCustomizationData
from routing.walkstyle.walkstyle_behavior import WalksStyleBehavior
from sims.outfits.outfit_enums import OutfitCategory
from sims.sim import Sim
from sims.sim_info import SimInfo
from sims.sim_info_base_wrapper import SimInfoBaseWrapper
from sims4communitylib.events.event_handling.common_event_registry import CommonEventRegistry
from sims4communitylib.events.zone_spin.events.zone_late_load import S4CLZoneLateLoadEvent
from sims4communitylib.events.zone_spin.events.zone_teardown import S4CLZoneTeardownEvent
from sims4communitylib.exceptions.common_exceptions_handler import CommonExceptionHandler
from sims4communitylib.utils.common_injection_utils import CommonInjectionUtils
from sims4communitylib.utils.common_log_registry import CommonLog, CommonLogRegistry
from sims4communitylib.utils.resources.common_interaction_utils import CommonInteractionUtils
from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils

game_loaded = False


oh = None

log: CommonLog = CommonLogRegistry.get().register_log(ModInfo.get_identity().author, ModInfo.get_identity().name)
log.enable()

# global variables - some are used, some are only set but never read.
preset_configuration = {}  # The parsed configuration of all "presets.*.ini" files

preset_configuration_ids = set()  # int - all configuration preset IDs
preset_configuration_slider_cas_ids = set()  # int - all cas IDs with slider settings (heels, ...)
preset_configuration_blacklist_interaction_ids = set()  # int - use default settings if interaction is running
preset_configuration_blacklist_sim_ids = set()  # int - skip all sims in this set

preset_configuration_body_types = set()  # int - all used body type, for shoes only: {8}
preset_configuration_modifier_ids = set()  # int - all used modifier IDs, likely {2} or {1, 2}
preset_configuration_face_sliders_ids = set()  # int - all used face sliders IDs
preset_configuration_body_sliders_ids = set()  # int - all used body sliders IDs

preset_body_type_2_face_sliders = dict()  # int - face sliders used for a specific body part {8: (11, 22, 33), 10: (33, 55, 66)}
preset_body_type_2_body_sliders = dict()  # int - body sliders used for a specific body part {8: (1, 2, 3), 10: (3,5,6)}

preset_cas_ids_2_id = dict()  # int - configuration ids used for a cas item
preset_id_2_cas_ids = dict()
preset_id_2_face_sliders = dict()  # int/(int/float) - face sliders used for a configuration id {10: {1: 1.0, 2: 0.2, 3: 0.3}, 20: [1: 0.1, 3: 0.3}}
preset_id_2_body_sliders = dict()  # int/(int/float) - body sliders used for a configuration id {10: {11: 1.0, 22: 0.2, 33: 0.3}, 20: [11: 0.1, 33: 0.3}}
preset_id_2_walkstyles = dict()  # int/(int/int) - walk style  for a configuration id {10: {123: 33}, 20: {444: 44}}
preset_object_instances = set()  # int - all configured objects / their cas IDs (12, 34, 56, ...)
preset_id_2_objects = dict()  # int/obj - object for a configuration id {10: obj, 20: obj, ...}


sim_ids_with_object = dict()  # {sim_id: [bone_name, bone_name_2, ...], sim_id_2: [..., ], }
sim_ids_with_walkstyles = dict()  # {sim_id: Walkstyle, sim_id_2: Walkstyle, ...}

# On_load: Update all sim_default_values if a new ID was added
# If shoe is detected get the SIM_ID and store all relevant slider values if not yet in 'sim_default_values'
# If shoe is not detected and SIM_ID in 'sim_default_values' apply these slider values
# If shoe is not detected and SIM_ID is not in 'sim_default_values' nothing happens



class HighHeelsGameLoadedEventListener:
    # In order to listen to an event, your function must match theResettingse criteria:
    # - The function is static (staticmethod).
    # - The first and only required argument has the name "event_data".
    # - The first and only required argument has the Type Hint for the event you are listening for.
    # - The argument passed to "handle_events" is the name of your Mod.
    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def handle_event(event_data: S4CLZoneTeardownEvent):
        global log, game_loaded
        if game_loaded:
            log.debug("S4CLZoneTeardownEvent" + str(event_data.zone) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))
            game_loaded = False

#    @staticmethod
#    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
#    def handle_event(event_data: S4CLZoneEarlyLoadEvent):
#        global log, game_loaded
#        if not game_loaded:
#            log.debug("S4CLZoneEarlyLoadEvent" + str(event_data.zone) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))
#            game_loaded = True

    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def handle_event(event_data: S4CLZoneLateLoadEvent):
        global log, game_loaded
        log.debug("S4CLZoneLateLoadEvent" + str(event_data.zone) + "/" + str(event_data.game_loading) + "/" + str(event_data.game_loaded))
        game_loaded = True


@CommonInjectionUtils.inject_safely_into(ModInfo.get_identity(), SimInfoBaseWrapper, SimInfoBaseWrapper._set_current_outfit_without_distribution.__name__, handle_exceptions=False)
def hh_set_current_outfit_without_distribution(original, self, *args, **kwargs):
    if game_loaded:
        try:
            change_clothes(self, *args, **kwargs)
        except Exception as ex:
            CommonExceptionHandler.log_exception(ModInfo.get_identity(), 'Error occurred changing outfit.', exception=ex)
    return original(self, *args, **kwargs)

def change_clothes(_self, *args, **kwargs):
    log.enable()
    main = HighHeels()
    main.change_clothes_v2(_self, *args, **kwargs)

@CommonInjectionUtils.inject_safely_into(ModInfo.get_identity(), WalksStyleBehavior, WalksStyleBehavior._get_property_override.__name__, handle_exceptions=False)
def hh__get_property_override(original, self, *args, **kwargs):
    try:
        rv = get_property_override(self, *args, **kwargs)
        if rv:
            return rv
    except Exception as ex:
        CommonExceptionHandler.log_exception(ModInfo.get_identity(), 'Error occurred changing walkstyle.', exception=ex)
    return original(self, *args, **kwargs)


def get_property_override(_self, actor, property_name):
    global sim_ids_with_object, sim_ids_with_walkstyles
    if isinstance(actor, Sim) and (actor.id in sim_ids_with_object) and (actor.id in sim_ids_with_walkstyles):
        #walkstyle = Walkstyle('StreamingDrone_Default', 3508326505)
        #log.debug(f" --------------- Drone ------")
        return sim_ids_with_walkstyles.get(actor.id)
    return None


# Walk_Wade (0x30126688): <class 'routing.walkstyle.walkstyle_tuning.Walkstyle'>
#    def _get_property_override(self, actor, property_name):
#        overrides = tuple(buff.walkstyle_behavior_override for buff in actor.get_active_buff_types() if buff.walkstyle_behavior_override is not None)
#        override = sims4.math.safe_max((override for override in overrides if getattr(override, property_name) is not None), key=operator.attrgetter('walkstyle_behavior_priority'), default=self)
#        property_value = getattr(override, property_name)
#        return property_value

previous_change_time = 0
previous_sim_id = -1
log_trace = False
oh: Union[O19Helper, None] = None
ss: Union[SliderStore, None] = None
o19ws = None
sim_info_mgr = None
sim_default_values: Union[dict, None] = None
modified_sims = set()  # A list with all sims in sim_default_values
sims_with_default_sliders = set()  # A list with all sims with default sliders applied



### CAS --> Object is placed in world
### Save & Load -->
class HighHeels:
    def __init__(self):
        global log, oh, o19ws, ss, sim_info_mgr
        global sim_default_values, preset_configuration_face_sliders_ids, preset_configuration_body_sliders_ids
        if o19ws is None:
            log.enable()
            log.info("Main.init()")
            sim_info_mgr = services.sim_info_manager()
            self.read_ini_files()
            log.debug("A")
            oh = O19Helper()
            log.debug("B")
            ss = SliderStore(oh, preset_configuration_face_sliders_ids, preset_configuration_body_sliders_ids)
            log.debug("C")
            sim_default_values = ss.read_config_file()
            log.debug("D")
            o19ws = Oops19Walkstyle()
            log.info("Main.init() completed")

    # TODO parameter sliders:dict() and set all sliders before applying them
    def slide_to_v3(self, sim_info: SimInfo, modifier_type: int, sliders: dict):
        log.debug(f"slide_to(SimInfo, modifier_type={modifier_type}, sliders={sliders})")
        if (modifier_type < 1) or (modifier_type > 2):
            log.error("Invalid modifier_type parameter")
            return
        try:
            slider_ids = set(sliders.keys)
            appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
            appearance_attributes.MergeFromString(sim_info.facial_attributes)
            if modifier_type == HighHeelsConstants.BLOB_SIM_BODY_MODIFIER:
                modifiers = appearance_attributes.body_modifiers
            else:
                modifiers = appearance_attributes.face_modifiers

            for modifier in modifiers:
                if modifier.key in slider_ids:
                    log.debug(f"Modifier {modifier.key} found")
                    slider_ids.remove(modifier.key)
                    modifier.amount = sliders.get(modifier.key)

            # slider_ids should be empty. If not, the modifier does not exist
            for slider_id in slider_ids:
                log.info(f"Modifier {slider_id} not found ... adding it on-the-fly")
                modifier = BlobSimFacialCustomizationData.Modifier()
                modifier.key = slider_id
                modifier.amount = sliders.get(modifier.key)
                if modifier_type == HighHeelsConstants.BLOB_SIM_BODY_MODIFIER:
                    appearance_attributes.body_modifiers.append(modifier)
                else:
                    appearance_attributes.face_modifiers.append(modifier)

            sim_info.facial_attributes = appearance_attributes.SerializeToString()
            sim_info.resend_facial_attributes()

        except:
            log.error(f"slider-error")
            pass

    # TODO parameter sliders:dict() and set all sliders before applying them
    def slide_to2(self, sim_info: SimInfo = None, modifier_type: int = -1, slider_id: int = -1, slider_value: Union[float, None] = None):
        log.debug(f"slide_to(SimInfo, {modifier_type}, {slider_id}, {slider_value})")
        if (SimInfo is None) or (modifier_type < 1) or (modifier_type > 2) or (slider_id < 0):
            log.error("Invalid parameters")
            return
        try:
            appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
            appearance_attributes.MergeFromString(sim_info.facial_attributes)
            found_modifier = False
            if modifier_type == HighHeelsConstants.BLOB_SIM_BODY_MODIFIER:
                modifiers = appearance_attributes.body_modifiers
            else:
                modifiers = appearance_attributes.face_modifiers

            for modifier in modifiers:
                if modifier.key == slider_id:
                    log.debug(f"Modifier found")
                    found_modifier = True
                    break

            if not found_modifier:
                if slider_value is None:
                    return False  # Modifier not found and no new value specified
                # Add slider (hopefully it exits in-game)
                log.info(f"Modifier not found ... adding it on-the-fly")
                modifier = BlobSimFacialCustomizationData.Modifier()
                modifier.key = slider_id  # set key & value
                modifier.amount = slider_value
                if modifier_type == HighHeelsConstants.BLOB_SIM_BODY_MODIFIER:
                    appearance_attributes.body_modifiers.append(modifier)
                else:
                    appearance_attributes.face_modifiers.append(modifier)
                sim_info.facial_attributes = appearance_attributes.SerializeToString()
                sim_info.resend_facial_attributes()
                return True  # Slider added and set

            # Modifier found
            current_value = modifier.amount
            if slider_value is not None:  # Check for None. '0' is not None.
                modifier.amount = slider_value

                sim_info.facial_attributes = appearance_attributes.SerializeToString()
                sim_info.resend_facial_attributes()
            return current_value

        except Exception as ex:
            log.error(f"slide_to() Error", exception=ex)
        return -1


    def has_slider_default(self, sim_id: int, set_to: Union[None, bool] = None) -> bool:
        global sims_with_default_sliders
        rv = sims_with_default_sliders.__contains__(sim_id)
        if set_to is True:
            sims_with_default_sliders.add(sim_id)
        elif (set_to is False) and rv:
            sims_with_default_sliders.remove(sim_id)
        return rv

    def is_in_whitelist(self, sim_id) -> bool:  # TODO
        return True

    def is_in_blacklist(self, sim_id) -> bool:  # TODO
        return False

    def is_no_slider_animation(self, sim_info: SimInfo) -> bool:
        reset_to_default = False
        no_slider_ids = HighHeelsConstants.DEFAULT_BLACKLIST_INTERACTION_IDS  # TODO f(ini-file)

        # Iterate over all interactions and if one matches the blacklist set the sliders to default
        ri = CommonSimInteractionUtils.get_running_interactions_gen(sim_info)
        for interaction in ri:
            interaction_id = CommonInteractionUtils.get_interaction_id(interaction)
            if interaction_id in no_slider_ids:
                log.debug(f"Sliders to default ({HighHeelsConstants.PRESET_CFG_BL_INTERACTION}/{interaction_id}).")
                reset_to_default = True
        return reset_to_default

    def get_outfit(self, sim_info, outfit_category_and_index):
        # Parse the parameters of the original method and fetch the current outfit (-1[0]) should also work.
        sim_id: int = sim_info.id
        try:
            outfit_category_and_index: tuple[OutfitCategory: int] = outfit_category_and_index
            outfit_category: OutfitCategory = outfit_category_and_index[0]
            outfit_index: int = outfit_category_and_index[1]
            log.debug(f"Changing clothes: (sim_id outfit[index]): {sim_id} {outfit_category}[{outfit_index}]")
            outfit = sim_info.get_outfit(outfit_category, outfit_index)
            # outfit = sim_info.get_outfit(-1 , 0)  # TODO - test this and remove everything above if oK
            return outfit
        except Exception as e:
            log.error(f"get_outfit({sim_id}) Error occurred.", exception=e)
            raise e

    def get_outfit_for_bodytype(self, outfit):
        # Iterate over all configured body_types. For shoes only this is '8, '
        # Fill 'body_type_2_outfit' with all matching {body_type: outfit_part_id} values
        global preset_configuration_body_types
        body_type_2_outfit = {}
        try:
            for body_type in preset_configuration_body_types:
                # outfit.body_types[n] contains the body_type (PRESET_CFG_BODY_TYPE) with value n. outfit.body_types[8] is likely not 8 as this would be too easy.
                # outfit.part_ids[n] contains the outfit_part_id (PRESET_CFG_CAS)
                if body_type in outfit.body_types:
                    try:
                        i = outfit.body_types.index(body_type)
                        outfit_part_id = outfit.part_ids[i]
                        body_type_2_outfit.update({body_type: outfit_part_id})
                    except:
                        # IndexError: list index out of range - this body_part has nothing attached
                        pass

                    #  Each body_type has 0-1 outfit_part_ids attached. Process the next body_type.
                    break

            log.debug(f"get_outfit_for_bodytype() Clothing items: ({body_type_2_outfit})")
        except Exception as ex:
            log.error(f"get_outfit_for_bodytype() Error occurred.", exception=ex)
        return body_type_2_outfit


    def join_sliders(self, _sliders: dict) -> dict:
        log.debug(f"join_sliders({_sliders})")
        sliders = {}
        for id, kv in _sliders.items():
            for slider_id, slider_value in kv.items():
                current_value = sliders.get(slider_id, 0)
                current_value += slider_value
                sliders.update({slider_id: current_value})

        # limit sliders from 0..1
        sliders_capped = {}
        for slider_id, slider_value in sliders.items():
            # limit max to 1, this may happen more often than min < 0
            if slider_value > 1:
                slider_value = 1
            elif slider_value < 0:
                slider_value = 0
            sliders_capped.update({slider_id: slider_value})

        log.debug(f"join_sliders({sliders_capped})")
        return sliders_capped

    def change_clothes_v2(self, sim_info: SimInfo, *args, **kwargs):
        # The 1st block makes sure that a valid sim_info is set and that we don't call it too often.
        global log, previous_change_time, previous_sim_id
        try:
            sim_id: int = sim_info.id
            sim: Sim = sim_info.get_sim_instance(allow_hidden_flags=ALL_HIDDEN_REASONS)
            if not sim:
                return
        except:
            return

        if (sim_id == previous_sim_id) and (previous_change_time >= time.time()):
            # event may be triggered often, only one change in 3s for each sim is allowed (even more if sims are switched fast enough)
            # May result in wrong slider settings during initialization
            self.trace(f"change_clothes() Skipping {sim_id} repeated changes.")
            return
        previous_sim_id = sim_id
        previous_change_time = time.time() + 3

        # Real start of change_clothes
        log.debug(f"change_clothes({sim_id})")
        global preset_configuration, preset_configuration_body_types, preset_body_type_2_face_sliders, preset_body_type_2_body_sliders
        global preset_configuration_slider_cas_ids
        global preset_cas_ids_2_id, preset_id_2_cas_ids, preset_id_2_face_sliders, preset_id_2_body_sliders
        global modified_sims, log_trace, o19ws, preset_id_2_walkstyles
        global sim_ids_with_object, preset_id_2_objects, preset_object_instances

        global ss
        preset_id = 0

        if not preset_configuration:
            log.error("Aborting as config is missing.")
            return False

        # Black- and whitelist checks
        if self.is_in_blacklist(sim_id):
            self.trace("change_clothes() - Early exit: Sim {sim_id} is blacklisted.")
            return

        if not self.is_in_whitelist(sim_id):
            self.trace("change_clothes() - Early exit: Sim {sim_id} is not whitelisted.")
            return

        # Animation check
        reset_to_default = self.is_no_slider_animation(sim_id)
        if reset_to_default:
            if self.has_slider_default(sim_id):
                self.trace("change_clothes() - Early exit: Sim {sim_id} has currently no sliders applied AND sliders should not be applied.")
                return

        # Outfit check
        outfit_category_and_index: tuple[OutfitCategory: int] = args[0]
        outfit = self.get_outfit(sim_info, outfit_category_and_index)
        body_type_2_outfit: dict = self.get_outfit_for_bodytype(outfit)
        if self.has_slider_default(sim_id) and not body_type_2_outfit:
                self.trace("change_clothes() - Early exit: Sim {sim_id} has currently no sliders applied AND all outfit parts are unknown.")

        if sim_id not in modified_sims:
            log.debug(f"change_clothes() - Sim sliders were never modified before, saving the defaults now.")

            ss.store_sim_sliders(sim_id)
            # self.store_sim_sliders(sim_id)

        body_slider_count: int = 0
        face_slider_count: int = 0
        _values_body_sliders: dict = dict()
        _values_face_sliders: dict = dict()
        attach_object: set = set()
        if not reset_to_default:
            # Iterate over body_type_2_outfit
            for body_type, outfit_part_id in body_type_2_outfit.items():
                if log_trace:
                    log.debug(f"  Processing {HighHeelsConstants.PRESET_CFG_BODY_TYPE} {body_type} with outfit_part_id {outfit_part_id} for all {preset_configuration_slider_cas_ids}")
                    log.debug(f"  sim_id in modified_sims: {sim_id} in {modified_sims} ?")
                else:
                    log.debug(f"  Processing {HighHeelsConstants.PRESET_CFG_BODY_TYPE} {body_type} with outfit_part_id {outfit_part_id} for {len(preset_configuration_slider_cas_ids)} items.")
                # Check if sim is new and/or sliders have to be adjusted
                try:
                    if outfit_part_id in preset_object_instances:
                        attach_object.add(outfit_part_id)
                    if outfit_part_id in preset_configuration_slider_cas_ids:
                        # Sliders will be adjusted
                        reset_to_default = False
                except Exception as ex:
                    log.error(f"  change_clothes(3) Error occurred.", ex)
                    return False

                log.debug(f"reset_to_default = {reset_to_default}")
                # Get the ID
                preset_id = 0
                for _id, _cas_ids in preset_id_2_cas_ids.items():
                    if outfit_part_id in _cas_ids:
                        preset_id = _id
                        break
                if not preset_id:
                    log.error(f"Strange ERROR: preset_id for outfit_part_id {outfit_part_id} not found! Resetting sliders!", throw=False)
                    reset_to_default = True
                    break

                # Get the face and body sliders for this ID
                body_sliders: dict = preset_id_2_body_sliders.get(preset_id)
                if body_sliders:
                    for slider_id, slider_value in body_sliders.items():
                        _values_body_sliders.update({body_slider_count: {slider_id: slider_value}})
                        body_slider_count += 1

                face_sliders: dict = preset_id_2_face_sliders.get(preset_id)
                if face_sliders:
                    for slider_id, slider_value in body_sliders.items():
                        _values_face_sliders.update({face_slider_count: {slider_id: slider_value}})
                        face_slider_count += 1

            # End this loop. Merge and adjust sliders. Multiple outfit_part_ids may modify the same slider in different ways.

        log.debug("AAAAAAAAAAAAAAA")
        # GET DEFAULT SLIDERS
        body_sliders = sim_default_values.get(HighHeelsConstants.BLOB_SIM_BODY_MODIFIER)
        values_body_sliders = body_sliders.get(sim_id)

        ## FAKE DEFAULT SLIDERS - FIXME
        values_body_sliders: dict = {}
        for s in preset_configuration_body_sliders_ids:
            values_body_sliders.update({s: 0})
        log.debug(f"_____ {values_body_sliders}")

        face_sliders = sim_default_values.get(HighHeelsConstants.BLOB_SIM_FACE_MODIFIER)
        values_face_sliders = face_sliders.get(sim_id)
        if not reset_to_default:
            # Append the default slider values to the retrieved slider values
            if values_body_sliders:
                for slider_id, slider_value in values_body_sliders.items():
                    _values_body_sliders.update({body_slider_count: {slider_id: slider_value}})
                    body_slider_count += 1
            # Join all sliders
            values_body_sliders = self.join_sliders(_values_body_sliders)

            if values_face_sliders:
                for slider_id, slider_value in values_face_sliders.items():
                    _values_face_sliders.update({face_slider_count: {slider_id: slider_value}})
                    face_slider_count += 1
            values_face_sliders = self.join_sliders(_values_face_sliders)

        # Apply body and face sliders, then ...
        if values_body_sliders:
            for slider_id, slider_value in values_body_sliders.items():
                log.debug(f"  Set slider: {HighHeelsConstants.BLOB_SIM_BODY_MODIFIER} {slider_id} {slider_value}")
                self.slide_to2(sim_info, HighHeelsConstants.BLOB_SIM_BODY_MODIFIER, slider_id, slider_value)

        if values_face_sliders:
            for slider_id, slider_value in values_face_sliders.items():
                log.debug(f"  Set slider: {HighHeelsConstants.BLOB_SIM_FACE_MODIFIER} {slider_id} {slider_value}")
                self.slide_to2(sim_info, HighHeelsConstants.BLOB_SIM_FACE_MODIFIER, slider_id, slider_value)

        # ..., then resend 'everything'. TS4 may process these events with some delay.
        sim_info.resend_outfits()
        sim_info.resend_physique()
        log.debug("Sliders adjusted")

        # update sim status
        self.has_slider_default(sim_id, reset_to_default)

        # Attach outfit code
        if attach_object:
            mso = ManageSimObject()
            currently_used_bones = sim_ids_with_object.get(sim_id, [])
            for outfit_part_id in attach_object:
                preset_id: int = 0
                for _id, _cas_ids in preset_id_2_cas_ids.items():
                    if outfit_part_id in _cas_ids:
                        preset_id = _id
                        break
                if not preset_id:
                    log.error(f"Strange ERROR: preset_id for outfit_part_id {outfit_part_id} not found! Skipping this item.", throw=False)
                    continue
                objects = preset_id_2_objects.get(preset_id)

                for obj in objects:
                    self.trace(f"Attaching object {obj.object_id} to {obj.parent_bone}")
                    rv = mso.obj_add(sim, obj)
                    if rv:
                        current_bones = sim_ids_with_object.get(sim_id, [])
                        current_bones.append(obj.parent_bone)
                        sim_ids_with_object.update({sim_id: current_bones})
                        if currently_used_bones.__contains__(obj.parent_bone):
                            currently_used_bones.remove(obj.parent_bone)
                    else:
                        log.error(f"Could not attach object {obj.object_id}.", throw=False)
            for bone in currently_used_bones:
                mso.remove(sim_id, bone)
        else:
            # Detach everything
            if sim_id in sim_ids_with_object:
                mso = ManageSimObject()
                current_bones = sim_ids_with_object.get(sim_id, [])
                for bone in current_bones:
                    mso.remove(sim, bone)

        # Set walk style #
        global sim_ids_with_walkstyles
        sim_ids_with_walkstyles.update({sim_id: 0})
        del sim_ids_with_walkstyles[sim_id]
        o19ws.stop(sim)
        if preset_id and not reset_to_default:
            walkstyles = preset_id_2_walkstyles.get(preset_id) #, {HighHeelsConstants.DEFAULT_WALKSTYLE: -1})
            for walkstyle, priority in walkstyles.items():
                o19ws.set(sim, walkstyle_hash=walkstyle, priority=priority)
                sim_ids_with_walkstyles.update({sim_id: o19ws.get_walkstyle(walkstyle)})
                break


    def _read_configuration(self, config_directory=None, pattern_start: str = 'random.', pattern_end: str = '.ini'):
        global log_trace
        log.info(f"_read_configuration({config_directory}, {pattern_start}, {pattern_end})")
        _configuration = {}
        if config_directory and os.path.exists(config_directory):
            file_names = sorted(os.listdir(config_directory))
            if (len(file_names)) > 1:
                _default_ini = pattern_start + 'default' + '.ini'
                file_names.remove(_default_ini)
                file_names.append(_default_ini)
            for file_name in file_names:
                # read random.default.ini 1st. Insert 'x' temporarily to keep the list a list. list.remove() may change list to NoneType
                if file_name.startswith(pattern_start) and file_name.endswith(pattern_end):
                    log.info(f"Reading {file_name}")
                else:
                    self.trace(f"Skipping {file_name}")
                    continue
                with open(os.path.join(config_directory, file_name), 'rt') as fp:
                    configuration_text = ""
                    for line in fp:
                        configuration_text = configuration_text + line
                    fp.close()
                    self.trace(f"Configuration text: {configuration_text}")
                try:
                    cfg = ast.literal_eval(configuration_text)
                    _configuration = {**cfg, **_configuration}  # Merge dicts, keep existing values as is
                except Exception as e:
                    log.error("Could not read or parse file.", exception=e)
            self.trace(f"_get_configuration(): {_configuration}")
        return _configuration

    def read_ini_files(self) -> bool:
        log.info(f"read_ini_files()")
        global preset_configuration, preset_configuration_ids, preset_configuration_slider_cas_ids
        global preset_configuration_blacklist_interaction_ids, preset_configuration_blacklist_sim_ids
        global preset_configuration_body_types, preset_configuration_modifier_ids
        global preset_configuration_face_sliders_ids, preset_configuration_body_sliders_ids
        global preset_body_type_2_face_sliders, preset_body_type_2_body_sliders

        global preset_id_2_face_sliders, preset_id_2_body_sliders
        global preset_cas_ids_2_id, preset_id_2_cas_ids, preset_id_2_walkstyles
        global preset_object_instances, preset_id_2_objects
        global log_trace

        try:
            # Read all ini files to a temp variable before assigning it globally
            _preset_configuration = {}
            ts4f = TS4_Folders_S4CL()
            config_directory = os.path.join(ts4f.base_folder, 'mod_data', 'high_heels', Oops19Constants.DIRECTORY_CONFIGURATION)

            os.makedirs(config_directory, exist_ok=True)

            _slider_configuration = self._read_configuration(config_directory, 'slider.', '.ini')
            slider_lookup = dict()
            try:
                for package_name, sliders in _slider_configuration.items():
                    slider_lookup = {**sliders, **slider_lookup}
                log.debug(f"Sliders: {slider_lookup}")
            except Exception as e:
                log.error("Could not extract slider configuration.", exception=e)

            _preset_configuration = self._read_configuration(config_directory, 'preset.', '.ini')

            if os.path.exists(config_directory):
                # Add everything to sets and dicts for faster access.
                _configuration_ids = set()
                _configuration_cas_ids = set()
                _configuration_blacklist_interaction_ids = set()
                _configuration_blacklist_sim_ids = set()
                _configuration_body_types = set()

                _configuration_modifier_ids = set()
                _configuration_face_sliders_ids = set()
                _configuration_body_sliders_ids = set()
                _body_type_face_sliders = dict()
                _body_type_body_sliders = dict()

                _cas_ids_2_id = dict()
                _id_2_cas_ids = dict()
                _id_2_face_sliders = dict()
                _id_2_body_sliders = dict()
                _preset_id_2_walkstyles = dict()

                _preset_object_instances = set()
                _preset_id_2_objects = dict()

                cas_item_lookup = {}
                for config_id, config_value in _preset_configuration.items():
                    if config_id < 0:
                        cas_item_lookup.update(config_value)
                        continue
                    _configuration_ids.add(config_id)
                    __x_cas_ids = config_value.get('CAS_IDs')
                    if not __x_cas_ids:
                        log.error(f"Field CAS_IDs missing for config_id {config_id}")
                        continue
                    for _name in __x_cas_ids:
                        __cas_ids = cas_item_lookup.get(_name)
                        if not __cas_ids:
                            log.error(f"CAS_IDs missing in config_id {config_id} for name {_name}")
                            continue
                        self.trace(f"CAS_IDs: {_name}: {__cas_ids}")

                        # NEW CODE
                        _configuration_cas_ids.update(__cas_ids)
                        tmp__cas_ids = _id_2_cas_ids.get(config_id, [])
                        tmp__cas_ids.extend(__cas_ids)
                        _id_2_cas_ids.update({config_id: tmp__cas_ids})

                    __blacklist_interaction_ids = config_value.get(HighHeelsConstants.PRESET_CFG_BL_INTERACTION)
                    if __blacklist_interaction_ids is None:
                        _configuration_blacklist_interaction_ids = HighHeelsConstants.DEFAULT_BLACKLIST_INTERACTION_IDS  # []
                    else:
                        # [] is not none and will remove the default
                        _configuration_blacklist_interaction_ids = __blacklist_interaction_ids

                    __blacklist_sim_ids = config_value.get(HighHeelsConstants.PRESET_CFG_BL_SIM)
                    if __blacklist_sim_ids is None:
                        _configuration_blacklist_sim_ids = HighHeelsConstants.DEFAULT_BLACKLIST_SIM_IDS  # []
                    else:
                        # [] is not none and will remove the default
                        _configuration_blacklist_sim_ids = __blacklist_sim_ids

                    __body_type = config_value.get(HighHeelsConstants.PRESET_CFG_BODY_TYPE, HighHeelsConstants.DEFAULT_BODY_TYPE)
                    _configuration_body_types.add(__body_type)

                    __walkstyles = config_value.get(HighHeelsConstants.PRESET_CFG_WALKSTYLE, HighHeelsConstants.DEFAULT_WALKSTYLE)
                    _preset_id_2_walkstyles.update({config_id: __walkstyles})

                    __face_sliders = config_value.get(HighHeelsConstants.PRESET_CFG_FACE_MODIFIERS)  # may be empty or None
                    if __face_sliders:
                        _configuration_modifier_ids.add(HighHeelsConstants.BLOB_SIM_FACE_MODIFIER)
                        __slider_ids = set()
                        for slider_name, slider_value in __face_sliders.items():
                            slider_id = slider_lookup.get(slider_name)
                            if not slider_id:
                                log.error(f"Error: Slider_name {slider_name} missing in config_id {config_id}")
                                continue
                            __slider_ids.add(slider_id)
                            _configuration_face_sliders_ids.add(slider_id)

                            ___current_sliders = _id_2_face_sliders.get(config_id, dict())
                            ___current_sliders.update({slider_id: slider_value})
                            _id_2_face_sliders.update({config_id: ___current_sliders})  # update the configuration

                        ___current_sliders = _body_type_face_sliders.get(__body_type, set())
                        ___current_sliders.update(__slider_ids)
                        _body_type_face_sliders.update({__body_type: ___current_sliders})  # update the configuration

                    __body_sliders = config_value.get(HighHeelsConstants.PRESET_CFG_BODY_MODIFIERS)  # may be empty or None
                    if __body_sliders:
                        _configuration_modifier_ids.add(HighHeelsConstants.BLOB_SIM_BODY_MODIFIER)
                        __slider_ids = set()
                        for slider_name, slider_value in __body_sliders.items():
                            slider_id = slider_lookup.get(slider_name)
                            if not slider_id:
                                log.error(f"Error: Slider_name {slider_name} missing in config_id {config_id}")
                                continue
                            __slider_ids.add(slider_id)
                            _configuration_body_sliders_ids.add(slider_id)

                            ___current_sliders = _id_2_body_sliders.get(config_id, dict())
                            ___current_sliders.update({slider_id: slider_value})
                            _id_2_body_sliders.update({config_id: ___current_sliders})  # update the configuration

                        ___current_sliders = _body_type_body_sliders.get(__body_type, set())
                        ___current_sliders.update(__slider_ids)
                        _body_type_body_sliders.update({__body_type: ___current_sliders})  # update the configuration

                    __outfit_objects = config_value.get(HighHeelsConstants.PRESET_CFG_ADD_OBJECTS)  # may be empty or None
                    if __outfit_objects:
                        __objects = []
                        for obj_k, obj_v in __outfit_objects.items():
                            _object_id: int = int(obj_v.get('Object_Instance', 0))
                            if not _object_id:
                                log.error(f"Error: No Object_Instance in {config_id} > {HighHeelsConstants.PRESET_CFG_ADD_OBJECTS} > {obj_k}")
                                continue
                            _parent_bone: str = obj_v.get('Parent_Bone', 'b__ROOT__')
                            _scale: float = float(obj_v.get('Scale', 1.0))

                            __position = obj_v.get('Position', '')
                            try:
                                _position = sims4.math.Vector3(float(__position.get('x')), float(__position.get('y')), float(__position.get('z')))
                            except:
                                _position = sims4.math.Vector3(0, 0, 0)

                            __rotation = obj_v.get('Rotation', '')
                            try:
                                _rotation = sims4.math.Quaternion(float(__position.get('x')), float(__position.get('y')), float(__position.get('z')), float(__position.get('w')))
                            except:
                                _rotation = sims4.math.Quaternion(0.0, 0.0, 0.0, 1.0)
                            o4s = Object4Sim(_object_id, _parent_bone, _scale, _position, _rotation)

                            _preset_object_instances.add(_object_id)
                            __objects.append(o4s)
                        _preset_id_2_objects.update({config_id: __objects})

                preset_configuration = _preset_configuration
                preset_configuration_ids = _configuration_ids
                preset_configuration_slider_cas_ids = _configuration_cas_ids
                preset_configuration_blacklist_interaction_ids = _configuration_blacklist_interaction_ids
                preset_configuration_blacklist_sim_ids = _configuration_blacklist_sim_ids
                preset_configuration_body_types = _configuration_body_types
                preset_configuration_modifier_ids = _configuration_modifier_ids
                preset_configuration_face_sliders_ids = _configuration_face_sliders_ids
                preset_configuration_body_sliders_ids = _configuration_body_sliders_ids
                preset_body_type_2_face_sliders = _body_type_face_sliders
                preset_body_type_2_body_sliders = _body_type_body_sliders
                preset_id_2_cas_ids = _id_2_cas_ids
                preset_id_2_face_sliders = _id_2_face_sliders
                preset_id_2_body_sliders = _id_2_body_sliders
                preset_id_2_walkstyles = _preset_id_2_walkstyles
                preset_object_instances = _preset_object_instances
                preset_id_2_objects = _preset_id_2_objects

                # Config file parsed properly?
                if log_trace:
                    log.debug(f"preset_configuration_ids: {preset_configuration_ids}")
                    log.debug(f"preset_configuration_slider_cas_ids: {preset_configuration_slider_cas_ids}")
                    log.debug(f"preset_configuration_blacklist_interaction_ids: {preset_configuration_blacklist_interaction_ids}")
                    log.debug(f"preset_configuration_blacklist_sim_ids: {preset_configuration_blacklist_sim_ids}")
                    log.debug(f"preset_configuration_body_types: {preset_configuration_body_types}")
                    log.debug(f"preset_configuration_modifier_ids: {preset_configuration_modifier_ids}")
                    log.debug(f"preset_configuration_face_sliders_ids: {preset_configuration_face_sliders_ids}")
                    log.debug(f"preset_configuration_body_sliders_ids: {preset_configuration_body_sliders_ids}")
                    log.debug(f"preset_body_type_2_face_sliders: {preset_body_type_2_face_sliders}")
                    log.debug(f"preset_body_type_2_body_sliders: {preset_body_type_2_body_sliders}")
                    log.debug(f"preset_id_2_cas_ids: {preset_id_2_cas_ids}")
                    log.debug(f"preset_id_2_face_sliders: {preset_id_2_face_sliders}")
                    log.debug(f"preset_id_2_body_sliders: {preset_id_2_body_sliders}")
                    log.debug(f"preset_id_2_walkstypes: {preset_id_2_walkstyles}")
                    log.debug(f"preset_object_instances: {preset_object_instances}")
                    log.debug(f"preset_id_2_objects: {preset_id_2_objects}")

            else:
                log.error("Problem with configuration directory: '" + config_directory + "'")
        except Exception as ex:
            log.error("read_ini_files() Unknown error occurred.", exception=ex)
        return False

    def trace(self, log_message: str):
        global log_trace
        if log_trace:
            log.debug(log_message)



# DEBUG options
@sims4.commands.Command('o19.hh.trace', command_type=sims4.commands.CommandType.Live)
def debug_o19_hh_trace(_connection=None):
    global log_trace
    output = sims4.commands.CheatOutput(_connection)
    try:
        log_trace = not log_trace
        output(f"debug_o19_hh_trace: {log_trace}")
    except Exception as ex:
        output("Error: " + str(ex))


# DEBUG options
@sims4.commands.Command('o19.hh.readini', command_type=sims4.commands.CommandType.Live)
def debug_o19_hh_readini(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("debug_o19_hh_readini")
    try:
        main = HighHeels()
        main.read_ini_files()
        output("debug_o19_hh_readini: OK")
    except Exception as ex:
        output("Error: " + str(ex))


@sims4.commands.Command('o19.hh.config', command_type=sims4.commands.CommandType.Live)
def debug_o19_hh_config(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("debug_o19_hh_config")
    try:
        global preset_configuration, preset_id_2_cas_ids, preset_configuration_slider_cas_ids
        output("preset_configuration: " + str(preset_configuration))
        time.sleep(1.5)
        output("preset_id_2_cas_ids: " + str(preset_id_2_cas_ids))
        time.sleep(1.5)
        # output("self.sim_default_values: " + str(self.sim_default_values))
        time.sleep(1.5)
        output("preset_configuration_slider_cas_ids: " + str(preset_configuration_slider_cas_ids))
    except Exception as ex:
        output("Error: " + str(ex))


@sims4.commands.Command('o19.hh.loaded_again', command_type=sims4.commands.CommandType.Live)
def debug_o19_hh_loaded_again(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("debug_o19_hh_loaded_again")
    try:
        # WARNING - will register the interceptor again and again. You have been warned.
        HighHeels()
        # Init.game_loaded()
        output("debug_o19_hh_loaded_again: OK")
    except Exception as ex:
        output("Error: " + str(ex))


