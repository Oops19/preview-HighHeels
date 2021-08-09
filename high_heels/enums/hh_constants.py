#
# License: https://creativecommons.org/licenses/by/4.0/ https://creativecommons.org/licenses/by/4.0/legalcode
# © 2020 https://github.com/Oops19
#
#

from sims4.math import MAX_INT32


class HighHeelsConstants:

    # Read-Only files (in Oops19Constants.DIRECTORY_INI)
    FILE_INI_SLIDERS = "sliders.ini"
    FILE_INI_BODY_TYPES = "body_types.ini"

    # Mod and custom user configurations (in Oops19Constants.DIRECTORY_CONFIGURATION)
    FILE_CONFIGURATION_CACHE = "do-not-delete-this-file-2.txt"

    # Various dump or trace files (in Oops19Constants.DIRECTORY_DUMP)
    FILE_DUMP_OUTFIT = "outfit.{0}.txt"
    FILE_DUMP_SLIDER = "slider.{0}.txt"

    # BLOB_SIM_DETAILS = {0: 'Sculpts', 1: 'Face_Modifiers', 2: 'Body_Modifiers'}
    BLOB_SIM_SCULPTS = 0  # not supported
    BLOB_SIM_FACE_MODIFIER = 1
    BLOB_SIM_BODY_MODIFIER = 2
    BLOB_SIM_NAME = [None] * 3
    BLOB_SIM_NAME[BLOB_SIM_SCULPTS] = "Sculpts"
    BLOB_SIM_NAME[BLOB_SIM_FACE_MODIFIER] = "Face_Modifiers"
    BLOB_SIM_NAME[BLOB_SIM_BODY_MODIFIER] = "Body_Modifiers"

    DEFAULT_SIM_ID = 0

    OUTPUT_SIM_ID = "sim_id"
    SIM_NAME_SEP = '#'
    OUTPUT_SIM_NAME = "sim_name"
    OUTPUT_SIM_OUTFIT_CATEGORY_TEXT = "category_text"
    OUTPUT_SIM_OUTFIT_CATEGORY = "category"
    OUTPUT_SIM_OUTFIT_INDEX = "index"
    OUTPUT_OUTFIT = "outfit"
    OUTPUT_SLIDERS = "sliders"

    PRESET_CFG_CAS = "CAS_IDs"
    PRESET_CFG_FACE_MODIFIERS = "Face_Modifiers"
    PRESET_CFG_BODY_MODIFIERS = "Body_Modifiers"
    PRESET_CFG_ADD_OBJECTS = "Add_Objects"

    DEFAULT_CONFIGURATION_FILENAME = 'global.ini'

    PRESET_CFG_BL_SIM = "Blacklist_Sim_IDs"
    DEFAULT_BLACKLIST_SIM_IDS = []

    PRESET_CFG_WL_SIM = "Whitelist_Sim_IDs"
    DEFAULT_WHITELIST_SIM_IDS = None

    PRESET_CFG_BODY_TYPE = "BodyType"
    DEFAULT_BODY_TYPE = 8

    PRESET_CFG_BL_INTERACTION = "Blacklist_Interaction_IDs"
    DEFAULT_BLACKLIST_INTERACTION_IDS = (11270438951712522986, ) # ww.woohoo_interaction_id

    PRESET_CFG_BL_SIM_ANIMATION_IDS = 'Blacklist_Animation_IDs'  # not implemented
    DEFAULT_BLACKLIST_ANIMATION_IDS = {}  # not implemented

    PRESET_CFG_WALKSTYLE = "Walkstyle"
    DEFAULT_WALKSTYLE = {2293790836: MAX_INT32}

    PRESET_CFG_FAST_START = "Fast_Start"
    DEFAULT_FAST_START = True