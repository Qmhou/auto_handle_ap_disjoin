import http.client
import json
import base64
import ssl
import yaml


# 从 YAML 文件中加载 DNAC 相关信息
def load_dnac_config():
    with open('dnac.yaml', 'r') as file:
        return yaml.safe_load(file)

# 获取 x-auth-token
def get_auth_token(dnac_config):
    print("获取 x-auth-token...")
    try:
        context = ssl._create_unverified_context()  # 禁用 SSL 验证
        conn = http.client.HTTPSConnection(dnac_config['dnac']['ip'], context=context)

        auth_string = f"{dnac_config['dnac']['username']}:{dnac_config['dnac']['password']}"
        auth_encoded = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        headers = {
            'Content-Type': "application/json",
            'Authorization': f"Basic {auth_encoded}"
        }

        conn.request("POST", "/dna/system/api/v1/auth/token", headers=headers)
        res = conn.getresponse()
        data = res.read()

        print("获取 token 的 API 响应数据:", data.decode("utf-8"))

        # 从响应中获取 token
        token = json.loads(data.decode("utf-8"))['Token']
        print("成功获取到 token:", token)
        return token

    except Exception as e:
        print(f"获取 token 时发生错误: {e}")
        return None

# 获取设备详情（通过 AP 名称）
def get_device_detail(ap_name, token, dnac_config):
    print(f"获取设备详情，AP 名称: {ap_name}")
    try:
        context = ssl._create_unverified_context()  # 禁用 SSL 验证
        conn = http.client.HTTPSConnection(dnac_config['dnac']['ip'], context=context)

        headers = {
            'x-auth-token': token,
            'Content-Type': 'application/json'
        }

        # 使用 nwDeviceName 作为 identifier，searchBy 为 AP 名称
        url = f"/dna/intent/api/v1/device-detail?identifier=nwDeviceName&searchBy={ap_name}"
        print(f"调用设备详情 API 的 URL: {url}")
        conn.request("GET", url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        print("获取设备详情的 API 响应数据:", data.decode("utf-8"))

        # 解析返回的 JSON 数据
        device_details = json.loads(data.decode("utf-8"))

        # 提取 nwDeviceId
        if 'response' in device_details and 'nwDeviceId' in device_details['response']:
            nwDeviceId = device_details['response']['nwDeviceId']
            print(f"成功获取到 nwDeviceId: {nwDeviceId}")
            return nwDeviceId
        else:
            print(f"API 响应中未找到 'nwDeviceId' 字段: {device_details}")
            return None

    except Exception as e:
        print(f"获取设备详情时发生错误: {e}")
        return None

# 获取设备丰富详情（通过 nwDeviceId）
def get_device_enrichment_details(nwDeviceId, token, dnac_config, mac_address=None, ip_address=None):
    print(f"获取设备丰富详情，nwDeviceId: {nwDeviceId}")

    # 尝试使用 nwDeviceId 或者 mac_address、ip_address
    if ip_address:
        entity_type = 'ip_address'
        entity_value = ip_address
    elif mac_address:
        entity_type = 'mac_address'
        entity_value = mac_address
    else:
        entity_type = 'device_id'
        entity_value = nwDeviceId

    print(f"使用 entity_type: {entity_type}, entity_value: {entity_value}")

    try:
        context = ssl._create_unverified_context()  # 禁用 SSL 验证
        conn = http.client.HTTPSConnection(dnac_config['dnac']['ip'], context=context)

        headers = {
            'x-auth-token': token,
            'Content-Type': 'application/json',
            'entity_type': entity_type,
            'entity_value': entity_value,
            '__persistbapioutput': 'true'
        }

        url = "/dna/intent/api/v1/device-enrichment-details"
        print(f"调用设备丰富详情 API 的 URL: {url}")
        conn.request("GET", url, headers=headers)

        res = conn.getresponse()
        data = res.read()

        print("获取设备丰富详情的 API 响应数据:", data.decode("utf-8"))

        # 解析返回的 JSON 数据
        enrichment_details = json.loads(data.decode("utf-8"))

        if 'deviceDetails' not in enrichment_details[0]:
            print(f"API 响应中未找到 'deviceDetails' 字段: {enrichment_details}")
            return None

        # 提取 AP 名称 (hostname), 交换机名称 (switch_name), 交换机 IP (switch_ip), 连接端口 (connect_port)
        ap_name = enrichment_details[0]['deviceDetails']['hostname']
        neighbor_topology = enrichment_details[0]['deviceDetails']['neighborTopology'][0]['nodes']

        # 找到交换机信息
        switch_info = None
        for node in neighbor_topology:
            if node['deviceType'] and "Switch" in node['deviceType']:  # 匹配交换机类型
                switch_info = node
                break

        if switch_info is None:
            print("未找到交换机信息")
            return None

        switch_name = switch_info['name']
        switch_ip = switch_info['ip']

        # 查找连接的接口信息
        for link in enrichment_details[0]['deviceDetails']['neighborTopology'][0]['links']:
            if link['target'] == switch_info['id'] and link['source'] == nwDeviceId:
                connect_port = link['targetInterfaceName']
                break
        else:
            print("未找到连接端口信息")
            return None

        ap_info = {
            'ap_name': ap_name,
            'switch_name': switch_name,
            'switch_ip': switch_ip,
            'connect_port': connect_port
        }

        print(f"成功提取到 AP 信息: {ap_info}")
        return ap_info

    except Exception as e:
        print(f"获取设备丰富详情时发生错误: {e}")
        return None

# 整合的动态获取 AP 信息的主函数
def get_ap_info_dynamically(ap_name):
    # 加载 DNAC 配置
    dnac_config = load_dnac_config()

    # 获取 x-auth-token
    token = get_auth_token(dnac_config)
    if token is None:
        print("获取 token 失败，程序退出")
        return

    # 使用 AP 名称获取 nwDeviceId
    nwDeviceId = get_device_detail(ap_name, token, dnac_config)
    if nwDeviceId is None:
        print("获取设备详情失败，程序退出")
        return

    # 使用 nwDeviceId 获取 AP 的相关信息
    ap_info = get_device_enrichment_details(nwDeviceId, token, dnac_config)
    if ap_info is None:
        print("获取设备丰富详情失败，程序退出")
        return

    print(f"最终提取的 AP 信息: {ap_info}")
    return ap_info
