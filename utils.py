import re

def parse_syslog_message(message):
    # 从 syslog 消息中提取 AP 名称
    ap_name_match = re.search(r'AP Name: (\S+)', message)
    if not ap_name_match:
        return None, None

    ap_name = ap_name_match.group(1)

    # 判断消息是掉线还是恢复
    if 'Disjoined' in message:
        return ap_name, 'disjoin'
    elif 'Joined' in message:
        return ap_name, 'join'
    else:
        return None, None

