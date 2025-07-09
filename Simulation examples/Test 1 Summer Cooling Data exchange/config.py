
import numpy as np

parameter = {}
# fmi_gym parameter
parameter['seed'] = 1
parameter['store_data'] = True

# fmu parameter
dtype = np.float64
parameter['fmu_step_size'] = 3600 / 6
parameter['fmu_path'] = 'edited_Pa8_RES5.fmu'
parameter['fmu_start_time'] = 135 * 60 * 60 * 24
parameter['fmu_warmup_time'] = 15 * 60 * 60 * 24
parameter['fmu_final_time'] = 255 * 60 * 60 * 24

# data exchange parameter
parameter['action_names'] = ['Cool_SP_Ingresso_fmu', 'Cool_SP_Camera1_fmu', 'Cool_SP_Camera2_fmu', 'Cool_SP_Camera3_fmu', 'Cool_SP_Bagno1_fmu', 'Cool_SP_Bagno2_fmu', 'Cool_SP_Cucina_fmu']
parameter['action_min'] = np.array(['26', '26', '26', '26', '26', '26', '26'], dtype=np.float64)
parameter['action_max'] = np.array(['30', '30', '30', '30', '30', '30', '30'], dtype=np.float64)
parameter['observation_names'] = ['Tingresso_fmu', 'Tcamera1_fmu', 'Tcamera2_fmu', 'Tcamera3_fmu', 'Tbagno1_fmu', 'Tbagno2_fmu', 'Tcucina_fmu']
parameter['reward_names'] = []

Begin_Month = 1
Begin_Day_of_Month = 1
