
import numpy as np

parameter = {}
# fmi_gym parameter
parameter['seed'] = 1
parameter['store_data'] = True

# fmu parameter
dtype = np.float64
parameter['fmu_step_size'] = 3600 / 6
parameter['fmu_path'] = 'office.fmu'
parameter['fmu_start_time'] = 140 * 60 * 60 * 24
parameter['fmu_warmup_time'] = 10 * 60 * 60 * 24
parameter['fmu_final_time'] = 240 * 60 * 60 * 24

# data exchange parameter
parameter['action_names'] = ['Cool_SP_SE_1F_fmu', 'Cool_SP_NW_1F_fmu', 'Cool_SP_NE_1F_fmu', 'Cool_SP_SW_1F_fmu', 'Cool_SP_SW_2F_fmu', 'Cool_SP_SE_2F_fmu', 'Cool_SP_NW_2F_fmu', 'Cool_SP_NE_2F_fmu']
parameter['action_min'] = np.array(['16', '16', '16', '16', '16', '16', '16', '16'], dtype=np.float64)
parameter['action_max'] = np.array(['35', '35', '35', '35', '35', '35', '35', '35'], dtype=np.float64)
parameter['observation_names'] = ['T_Block1:OfficeXSWX1f_fmu', 'T_Block1:OfficeXSEX1f_fmu', 'T_Block1:OfficeXNWX1f_fmu', 'T_Block1:OfficeXNEX1f_fmu', 'T_Block2:OfficeXSWX2f_fmu', 'T_Block2:OfficeXSEX2f_fmu', 'T_Block2:OfficeXNWX2f_fmu', 'T_Block2:OfficeXNEX2f_fmu']
parameter['reward_names'] = []

Begin_Month = 1
Begin_Day_of_Month = 1
