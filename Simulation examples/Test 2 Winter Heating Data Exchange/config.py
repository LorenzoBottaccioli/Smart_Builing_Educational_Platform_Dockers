
import numpy as np

parameter = {}
# fmi_gym parameter
parameter['seed'] = 1
parameter['store_data'] = True

# fmu parameter
dtype = np.float64
parameter['fmu_step_size'] = 3600 / 6
parameter['fmu_path'] = 'Pa3_RES4.fmu'
parameter['fmu_start_time'] = 155 * 60 * 60 * 24
parameter['fmu_warmup_time'] = 10 * 60 * 60 * 24
parameter['fmu_final_time'] = 364 * 60 * 60 * 24

# data exchange parameter
parameter['action_names'] = ['Heat_SP_IngressoxCucina_fmu', 'Heat_SP_Bagno_fmu', 'Heat_SP_Camera', 'Heat_SP_Soggiorno_fmu', 'Heat_SP_Stairs_fmu', 'Heat_SP_Storage_fmu']
parameter['action_min'] = np.array(['12', '12', '12', '12', '12', '12'], dtype=np.float64)
parameter['action_max'] = np.array(['23', '23', '23', '23', '23', '23'], dtype=np.float64)
parameter['observation_names'] = ['T_IngressoxCucina_fmu', 'T_StairsWest_fmu', 'T_Bagno_fmu', 'T_Storage_fmu', 'T_Camera_fmu', 'T_Soggiorno_fmu']
parameter['reward_names'] = []

Begin_Month = 1
Begin_Day_of_Month = 1
