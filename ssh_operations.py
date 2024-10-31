import paramiko
import logging
import time


def ssh_to_switch(switch_ip, connect_port, config):
    try:
        logger = logging.getLogger('ap_debug')
        print(f"正在连接交换机 {switch_ip}")
        logger.info(f"正在连接交换机 {switch_ip}")

        username = config['credentials']['username']
        password = config['credentials']['password']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 增加调试信息
        print(f"使用用户名 {username} 进行 SSH 登录")
        logger.info(f"使用用户名 {username} 进行 SSH 登录")

        try:
            ssh.connect(switch_ip, port=22, username=username, password=password, allow_agent=False, look_for_keys=False, timeout=10)
        except paramiko.AuthenticationException:
            logger.error("SSH 操作失败: Authentication failed")
            print("SSH 操作失败: Authentication failed")
            return False
        except paramiko.SSHException as ssh_exception:
            logger.error(f"SSH 操作失败: {ssh_exception}")
            print(f"SSH 操作失败: {ssh_exception}")
            return False

        # 打开交互式shell
        shell = ssh.invoke_shell()

        # 进入全局配置模式
        shell.send('conf t\n')
        time.sleep(1)

        # 进入接口配置模式并执行 shut/no shut 命令
        shell.send(f'interface {connect_port}\n')
        time.sleep(1)

        shell.send('shutdown\n')
        time.sleep(1)

        shell.send('no shutdown\n')
        time.sleep(1)

        # 获取命令执行的输出
        output = shell.recv(65535).decode('utf-8')
        print(output)
        logger.debug(f"命令执行输出: {output}")

        # 关闭连接
        ssh.close()

        return True
    except Exception as e:
        logger.error(f"SSH 操作失败: {e}")
        print(f"SSH 操作失败: {e}")
        return False



