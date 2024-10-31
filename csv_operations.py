import csv
import logging

def load_ap_info_csv(csv_file):
    logger = logging.getLogger('ap_debug')
    ap_info = {}

    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ap_name = row['ap_name']
                ap_info[ap_name] = {
                    'switch_name': row['switch_name'],
                    'switch_ip': row['switch_ip'],
                    'connect_port': row['connect_port']
                }
    except Exception as e:
        logger.error(f"加载 CSV 文件时发生错误: {e}")
        raise e

    return ap_info
