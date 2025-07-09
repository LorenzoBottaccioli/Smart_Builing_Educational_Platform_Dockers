
import numpy as np

parameter = {}
# fmi_gym parameter
parameter['seed'] = 1
parameter['store_data'] = True

# fmu parameter
dtype = np.float64
parameter['fmu_step_size'] = 3600 / 6
parameter['fmu_path'] = 'lab_building.fmu'
parameter['fmu_start_time'] = 255 * 60 * 60 * 24
parameter['fmu_warmup_time'] = 10 * 60 * 60 * 24
parameter['fmu_final_time'] = 364 * 60 * 60 * 24

# data exchange parameter
parameter['action_names'] = ['Heat_SP_Kitchen_fmu', 'Heat_SP_Room1_fmu', 'Heat_SP_Corridor_fmu', 'Heat_SP_Bath_fmu', 'Heat_SP_Livingroom_fmu', 'Heat_SP_Bath1_fmu', 'Heat_SP_Room_fmu']
parameter['action_min'] = np.array(['12', '12', '12', '12', '12', '12', '12'], dtype=np.float64)
parameter['action_max'] = np.array(['20', '20', '20', '20', '20', '20', '20'], dtype=np.float64)
parameter['observation_names'] = ['T_Block1B:Kitchen_fmu', 'T_Block1B:Bathroom1_fmu', 'T_Block1B:Room1_fmu', 'T_Block1B:Corridor_fmu', 'T_Block1B:Bathroom_fmu', 'T_Block1B:Livingroom_fmu', 'T_Block1B:Room_fmu', 'Tout_fmu']
parameter['reward_names'] = []

Begin_Month = 1
Begin_Day_of_Month = 1
