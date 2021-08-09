#
# License: https://creativecommons.org/licenses/by/4.0/ https://creativecommons.org/licenses/by/4.0/legalcode
# © 2020 https://github.com/Oops19
#
#

from typing import Union

import services
from high_heels.enums.constants import Oops19Constants
from high_heels.utilities.helper_standalone import O19Helper
from sims.sim import Sim
from sims.sim_info import SimInfo
from sims4communitylib.utils.sims.common_sim_name_utils import CommonSimNameUtils
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils


class O19SimV2:
    """
    A simple class to access all Sim properties and to retrieve them.
    o19sim = O19Sim(init)
    sim: Sim = o19sim.sim  # == o19sim._get_sim()
    sim_id: SimInfo = o19sim.sim_id  # == o19sim._get_sim_id()
    sim_info: SimInfo = o19sim.sim_info  # == o19sim._get_sim_info()
    sim_name: str = o19sim.sim_name  # == o19sim._get_sim_name()
    sim_filename: str = o19sim.sim_filename  # == o19sim._get_sim_filename()
    """

    def __init__(self, sim_identifier: Union[SimInfo, Sim, int, None, str]):
        self.__init()
        self._sim = None
        self._sim_id = None
        self._sim_info = None
        self._sim_name = None
        self._sim_filename = None

        if sim_identifier is None:
            self._sim_identifier = CommonSimUtils.get_active_sim_info()
        elif isinstance(sim_identifier, str):
            if Oops19Constants.SIM_NAME_SEP in sim_identifier:
                self._sim_name = self.oh.get_full_sim_name(sim_identifier)
                first_name, last_name = self.sim_name.split(Oops19Constants.SIM_NAME_SEP, 1)
                self._sim_identifier: SimInfo = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)
            else:
                errmsg = f'To search by name add {Oops19Constants.SIM_NAME_SEP} to the search term.'
                raise ValueError(errmsg)
        else:
            self._sim_identifier = sim_identifier

    # noinspection PyBroadException
    @classmethod
    def __init(cls):
        if not hasattr(cls, '_client_mgr') or not cls._client_mgr:
            cls._client_mgr = services.client_manager()
        if not hasattr(cls, 'oh') or not cls.oh:
            cls.oh = O19Helper()

    # Public API to retrieve values
    @property
    def sim(self) -> Sim:
        if not self._sim:
            self._sim = CommonSimUtils.get_sim_instance(self.sim_info)
        return self._sim

    @property
    def sim_id(self) -> int:
        if not self._sim_id:
            self._sim_id = CommonSimUtils.get_sim_id(self.sim_info)
        return self._sim_id

    @property
    def sim_info(self) -> SimInfo:
        if not self._sim_info:
            self._sim_info = CommonSimUtils.get_sim_info(self._sim_identifier)
        return self._sim_info

    @property
    def sim_name(self) -> str:
        if not self._sim_name:
            first_name = CommonSimNameUtils.get_first_name(self.sim_info)
            last_name = CommonSimNameUtils.get_last_name(self.sim_info)
            self._sim_name = f"{first_name}{Oops19Constants.SIM_NAME_SEP}{last_name}"
        return self._sim_name

    @property
    def sim_filename(self) -> str:
        if not self._sim_filename:
            self._sim_filename = self.oh.get_sim_filename(self.sim_name)
        return self._sim_filename
