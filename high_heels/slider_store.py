
import ast
import os
from os import path

from high_heels.enums.constants import Oops19Constants
from high_heels.enums.hh_constants import HighHeelsConstants

from high_heels.modinfo import ModInfo
from high_heels.utilities.helper_standalone import O19Helper, O19Sim
from protocolbuffers import PersistenceBlobs_pb2
from sims4communitylib.utils.common_log_registry import CommonLog, CommonLogRegistry

log: CommonLog = CommonLogRegistry.get().register_log(ModInfo.get_identity().author, ModInfo.get_identity().name)


class SliderStore:
    def __init__(self, oh: O19Helper, preset_configuration_face_sliders_ids: set, preset_configuration_body_sliders_ids: set):
        self.oh = oh
        self.preset_configuration_face_sliders_ids = preset_configuration_face_sliders_ids
        self.preset_configuration_body_sliders_ids = preset_configuration_body_sliders_ids

        self.body_sliders: dict = {}  # {sim_id: {k: v, ...}, sim_id_2: {k: v, ... }, ...
        self.face_sliders: dict = {}
        self.slider_sims: set = set()  # Sims with a slider definition (all sims in config-file)
        self.updated_sims: set = set()  # Sims with an updated slider definition (0 after loading)

    # store all sim sliders as 'default' values
    def store_sim_sliders(self, sim_id: int, force_refresh: bool = False, auto_save: bool = True) -> bool:
        self.slider_sims.add(sim_id)
        self.updated_sims.add(sim_id)


        log.debug(f"store_sim_sliders({sim_id}, force_refresh={force_refresh}, auto_save={auto_save})")
        try:
            if (force_refresh is False) and (sim_id in self.updated_sims):
                return True

            o19sim: O19Sim = self.oh.get_sim_all(sim_id)
            if not o19sim.sim_info:
                log.error(f"Can not access the sim ({sim_id}) right now, try it again later.", throw=False)
                return False
            appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
            appearance_attributes.MergeFromString(o19sim.sim_info.facial_attributes)

            active_body_sliders = {}
            active_face_sliders = {}
            # Initialize 'active_body_sliders / active_face_sliders' with 0 in case the sliders are not found
            for slider_id in self.preset_configuration_body_sliders_ids:
                active_body_sliders.update({slider_id: 0})
            for slider_id in self.preset_configuration_face_sliders_ids:
                active_face_sliders.update({slider_id: 0})

            # Store the actual slider values in 'new_body_sliders / new_face_sliders'
            for modifier in appearance_attributes.body_modifiers:
                if modifier.key in self.preset_configuration_body_sliders_ids:
                    active_body_sliders.update({modifier.key: modifier.amount})
            for modifier in appearance_attributes.face_modifiers:
                if modifier.key in self.preset_configuration_face_sliders_ids:
                    active_face_sliders.update({modifier.key: modifier.amount})

            # {sim_id: __{k5: v5, k6: v6, },__ sim_id_2: {k7: v7, k8, v8, },
            default_body_sliders = self.body_sliders.get(sim_id)

            # {sim_id: __{k1: v1, k2: v2, },__ sim_id: {k3: v3, k4: v4, },
            default_face_sliders = self.face_sliders.get(sim_id)

            # Join the sliders
            # Join the body_sliders
            if force_refresh or default_body_sliders is None:
                # 1st call OR new: add the sim with current values
                self.body_sliders.update({sim_id: active_body_sliders})
                log.debug(f'store_sim_sliders() Setting new defaults {self.body_sliders}')
            else:
                # Merge sliders, add only new slider values to the existing ones. Existing values will not be replaced.
                merged_body_slider = {**active_body_sliders, **default_body_sliders}
                self.body_sliders.update({sim_id: merged_body_slider})

            # Join the face_sliders
            if force_refresh or default_face_sliders is None:
                # 1st call OR new: add the sim with current values
                self.face_sliders.update({sim_id: active_face_sliders})
                log.debug(f'store_sim_sliders() Setting new defaults {self.face_sliders}')
            else:
                # Merge sliders, add only new slider values to the existing ones. Existing values will not be replaced.
                merged_face_slider = {**active_face_sliders, **default_face_sliders}
                self.face_sliders.update({sim_id: merged_face_slider})
            self.updated_sims.add(sim_id)

            if auto_save:
                self.save_config_file({HighHeelsConstants.BLOB_SIM_BODY_MODIFIER: self.body_sliders, HighHeelsConstants.BLOB_SIM_FACE_MODIFIER: self.face_sliders})
            self.slider_sims.add(sim_id)
            self.updated_sims.add(sim_id)
            return True
        except Exception as ex:
            log.error("store_sim_sliders() Error occurred.", exception=ex)
        return False

    def save_config_file(self, sim_default_values):
        return

        # No save files for now
        log.info(f"save_config_file()")
        try:
            current_directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
            config_directory = os.path.join(current_directory, Oops19Constants.DIRECTORY_CONFIGURATION)
            file_name = os.path.join(config_directory, HighHeelsConstants.FILE_CONFIGURATION_CACHE)
            try:
                with open(file_name, 'wt') as fp:
                    self.oh.print_pretty(fp, str(sim_default_values))
                    fp.close()
            except:
                with open(file_name, 'wt') as fp:
                    fp.write(f"{sim_default_values}")
                log.error(f"save_config_file() - print_pretty failed.", throw=False)
        except Exception as ex:
            log.error("save_config_file() Error occurred.", exception=ex)

    def read_config_file(self) -> dict:
        '''
        Returns all sims with stored default values. These sims were modified in the past.
        :return:
        '''
        return {HighHeelsConstants.BLOB_SIM_BODY_MODIFIER: {}, HighHeelsConstants.BLOB_SIM_FACE_MODIFIER: {}, }

        # No save files for now
        log.info(f"read_config_file()")
        # start with an empty configuration as a fallback
        sim_default_values = {HighHeelsConstants.BLOB_SIM_BODY_MODIFIER: {}, HighHeelsConstants.BLOB_SIM_FACE_MODIFIER: {}, }
        try:
            current_directory = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
            config_directory = os.path.join(current_directory, Oops19Constants.DIRECTORY_CONFIGURATION)
            file_name = os.path.join(config_directory, HighHeelsConstants.FILE_CONFIGURATION_CACHE)
            if path.exists(file_name):
                log.debug(f"Reading '{file_name}'")
                with open(os.path.join(config_directory, file_name), 'rt') as fp:
                    configuration_text = ""
                    for line in fp:
                        configuration_text = configuration_text + line
                    fp.close()
                try:
                    sim_default_values = ast.literal_eval(configuration_text)
                except Exception as ex:
                    log.error("read_config_file() - Could not parse file '{file_name}'", exception=ex, throw=False)

                self.body_sliders: dict = sim_default_values.get(HighHeelsConstants.BLOB_SIM_BODY_MODIFIER)
                self.face_sliders: dict = sim_default_values.get(HighHeelsConstants.BLOB_SIM_FACE_MODIFIER)
                for slider_cat, sim_cfg in sim_default_values:
                    for sim_id, _ in sim_cfg:
                        self.slider_sims.add(sim_id)
            else:
                log.debug("Starting with empty file '{file_name}'.")
        except Exception as e:
            log.error("read_config_file() - Could not read '{file_name}'", exception=e, throw=False)
        return sim_default_values


    @property
    def sims_with_sliders(self) -> set:
        return self.slider_sims

    @property
    def sims_with_updated_sliders(self) -> set:
        return self.updated_sims


#hhd = HighHeelsDefaults()