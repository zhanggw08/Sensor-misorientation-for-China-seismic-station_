import sys
import os
from obspy import read
from obspy import Stream
from math import cos, sin, radians

######################################################################
def main():
    # 检查命令行参数的数量
    if len(sys.argv) != 3:
        # 如果参数数量不正确，打印错误消息并退出
        print("错误：需要两个命令行参数（BHN和BHE分量的SAC文件路径）。")
        print("用法：python script_name.py path/bhn_file.sac path/bhe_file.sac")
        sys.exit(1)  # 非零退出代码表示错误

    # 从命令行参数中获取mseed文件路径
    bhn_file_path = sys.argv[1]
    bhe_file_path = sys.argv[2]

    # 验证文件路径是否存在
    if not os.path.isfile(bhn_file_path):
        print(f"错误：文件 {bhn_file_path} 不存在。")
        sys.exit(1)
    if not os.path.isfile(bhe_file_path):
        print(f"错误：文件 {bhe_file_path} 不存在。")
        sys.exit(1)

    # 读取SAC文件
    try:
        stream_n = read(bhn_file_path)
        trace_n = stream_n[0]
        stream_e = read(bhe_file_path)
        trace_e = stream_e[0]
    except Exception as e:
        print(f"错误：读取SAC文件时出错 - {e}")
        sys.exit(1)
            
    station_name = trace_n.stats.station
    network_name = trace_n.stats.network  
    start_time = trace_n.stats.starttime  
    date_string = start_time.strftime("%Y%m%d")
    station_name = network_name+"."+station_name
    csv_filename = 'orient_results_2007_2023_use.csv'
    results =  get_azi_from_csv(csv_filename,station_name,date_string)
    # 读取方位角偏差值  
    azimuth_deviation = results[0]
    correct_azi = float(azimuth_deviation)
    # 存在特殊处理情况
    special_instruction = results[1]
    if isinstance(special_instruction, str): 
        if special_instruction.lower() == "nan":    
            trace_n_special = trace_n.copy()
            trace_e_special = trace_e.copy()         
        elif special_instruction == "E_N":  
            trace_n_special = trace_e.copy()  
            trace_e_special = trace_n.copy()  
        elif special_instruction == "`-E_-N":  
            trace_n_special = trace_e.copy()  
            trace_n_special.data = trace_e.data * (-1)  
            trace_e_special = trace_n.copy()  
            trace_e_special.data = trace_n.data * (-1)  
        elif special_instruction == "N_-N":  
            trace_n_special = trace_n.copy()  
            trace_n_special.data = trace_n.data * (-1)  
            trace_e_special = trace_e.copy()  
        elif special_instruction == "E_-E":  
            trace_n_special = trace_n.copy()  
            trace_e_special = trace_e.copy()  
            trace_e_special.data = trace_e.data * (-1)      
    ############################################方位角校正
    ba = radians(correct_azi)   
    trace_n_new = trace_n_special.copy()
    trace_e_new = trace_e_special.copy()
    trace_n_new.data = trace_n_special.data*cos(ba)-trace_e_special.data*sin(ba)
    trace_e_new.data = trace_n_special.data*sin(ba)+trace_e_special.data*cos(ba)
    
   
    stream_n_new = Stream([trace_n_new])  
    stream_e_new = Stream([trace_e_new])  
    ############################################ 
    # 保存到文件      
    current_directory = os.path.dirname(os.path.abspath(__file__)) 
    save_path = current_directory + '/correct_traces/'    
    if not os.path.exists(save_path):  
        os.makedirs(save_path)
        
    base_bhn_name = os.path.basename(bhn_file_path)
    base_bhe_name = os.path.basename(bhe_file_path)
    new_bhn_name = f"correct.{base_bhn_name}"
    new_bhe_name = f"correct.{base_bhe_name}"
      
    new_bhn_path = os.path.join(save_path, new_bhn_name)  
    new_bhe_path = os.path.join(save_path, new_bhe_name)
    # 写入SAC文件
    stream_n_new.write(new_bhn_path, format='SAC')  
    stream_e_new.write(new_bhe_path, format='SAC')       
    
    print(f"{station_name} Average:{correct_azi} Special:{special_instruction}")
    print(f"finished")

######################################################################

######################################从CSV文件中根据台站名和日期读取对应的方位角偏差值####################################################    
import pandas as pd  
def get_azi_from_csv(filename, station_name, target_date):  
    """  
    从CSV文件中根据台站名和日期读取对应的方位角偏差值。  
  
    参数:  
    filename (str): CSV文件的路径。  
    station_name (str): 要查询的台站名。  
    target_date (str): 查询的目标日期（格式为yyyymmdd）。  
  
    返回:  
    float 或 None: 找到的方位角偏差值，如果未找到则返回None。  
    """  
    try:   
        df = pd.read_csv(filename)  
    except FileNotFoundError:  
        print(f"文件未找到: {filename}")  
        return None  
     
    if 'Station' in df.columns and 'StartDate' in df.columns and 'EndDate' in df.columns and 'Average' in df.columns and 'Special' in df.columns:   
        df['StartDate'] = df['StartDate'].astype(str) 
        df['EndDate'] = df['EndDate'].astype(str)  
        # 筛选台站名和日期  
        mask = (df['Station'] == station_name) & (df['StartDate'] <= target_date) & (df['EndDate'] >= target_date) 
        matched_rows = df[mask]  
  
        # 检查是否有匹配项  
        if matched_rows.empty:  
            print(f"未找到台站名 {station_name} 在日期 {target_date} 的数据。")  
            return None  
   
        return (matched_rows['Average'].iloc[0], matched_rows['Special'].iloc[0]) 
    else:  
        print("CSV文件中缺少必要的列（'Date', 'Station', 或 'Average'）。")  
        return None      
################################从CSV文件中根据台站名和日期读取对应的方位角偏差值函数######################################

if __name__ == "__main__":
    main()
