#
# License: https://creativecommons.org/licenses/by/4.0/ https://creativecommons.org/licenses/by/4.0/legalcode
# © 2020 https://github.com/Oops19
#
#

from high_heels.utilities.helper_standalone import O19Sim, O19Helper
from high_heels.utilities.manage_sim_object import ManageSimObject
from sims.sim import Sim
import sims4.commands
import sims4.math
import sims4

# Download ATS4_advent2017_21.zip from https://sims4.aroundthesims3.com/objects/special_06.shtml
# To get it working set the walkstyle to "Drone_Fast" and the sim should be moved up a little bit with a slider.
# TS4 uses random walkstyles for short and long distances. Unless this can be fixed use an average distance when travelling with the board.

# 0xC073416FAE8D1B75 . piercing obj


@sims4.commands.Command('o19.del.piercing', command_type=sims4.commands.CommandType.Live)
def o19_piercing_del(p_sim=None, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        oh = O19Helper(output=output)
        o19sim: O19Sim = oh.get_sim_all(p_sim)
        output(f"{o19sim.sim_name}")
        sim: Sim = o19sim.sim

        mo = ManageSimObject()
        mo.add(sim=sim)

        output(f"ok")
    except Exception as ex:
        output(f"o19_board_del() - Error: {ex}")


@sims4.commands.Command('o19.add.piercing', command_type=sims4.commands.CommandType.Live)
def o19_piercing_add(p_sim=None, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        oh = O19Helper(output=output)
        o19sim: O19Sim = oh.get_sim_all(p_sim)
        output(f"{o19sim.sim_name}")
        sim: Sim = o19sim.sim

        position = sims4.math.Vector3(0, 0, 0)  # Standing behind sim: (-move_to_right) .. move_to_left | (-move_down) .. move_up | (-move_behind) .. move_in_front (only for b__ROOT__)
        orientation = sims4.math.Quaternion(0, 0, 0, 1)
        transformation = sims4.math.Transform(position, orientation)

        mso = ManageSimObject()
        rv = mso.add(sim=sim, obj_definition_id=0xC073416FAE8D1B75, bone_name='b__R_breastTarget_slot', scale=1.0, transformation=transformation)
        #

        output(f"ok {rv}")
        if not rv:
            output(f"___ {mso.e()}")
    except Exception as ex:
        output(f"o19.add.piecing() - Error: {ex}")

@sims4.commands.Command('o19.drop.piercing', command_type=sims4.commands.CommandType.Live)
def o19_piercing_any(bone_name, p_sim=None, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output(f"Usage: o19.drop.piercing [bone-name] [sim]")
    try:
        oh = O19Helper(output=output)
        o19sim: O19Sim = oh.get_sim_all(p_sim)
        output(f"{o19sim.sim_name}")
        sim: Sim = o19sim.sim

        if not bone_name:
            bone_name = 'b__L_breastTarget_slot'

        mso = ManageSimObject()
        rv = mso._remove(sim=sim, bone_name=bone_name)

        output(f"ok {rv}")
        if not rv:
            output(f"{mso.e()}")

    except Exception as ex:
        output(f"o19.drop.piercing() - Error: {ex}")