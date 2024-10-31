AP Disjoin Handler 是一个用于自动处理无线接入点 (AP) 掉线事件的 Python 程序。
该程序通过监听交换机或无线控制器发送的 syslog 消息，检测 AP 是否掉线。
当检测到掉线后，程序会自动连接到对应的交换机，尝试重启端口，并在多次尝试后发送通知邮件。

## 功能描述:
 - **Syslog 监听***：
程序通过指定的端口监听 syslog 消息。
当接收到包含 AP 掉线或恢复的信息时，程序会根据 syslog 内容自动处理相关操作。

 - **AP 查询**：
get_ap_info_dynamically模块，使用API从DNAC获取AP cdp信息，对应模块dnac_api
如果三次动态获取失败，程序会从 CSV 文件中加载 AP 与对应交换机和端口的映射关系
*如果AP出现多次翻转，DNAC的Get Device Enrichment API会无法正常获取到Links键。*

 - **SSH 操作**：
在检测到 AP 掉线后，程序会通过 SSH 连接到对应的交换机。
通过发送交换机命令 (如 shutdown 和 no shutdown)，重启与 AP 连接的端口，以尝试恢复 AP。
多次尝试和通知：

如果重启端口后 AP 仍未恢复，程序会多次尝试进行 SSH 操作（最多三次）。
如果经过三次尝试仍未恢复，程序会通过邮件通知相关人员。

 - **日志记录**：
程序使用 syslog 服务器记录所有重要事件和操作日志，包括 AP 掉线、端口重启、AP 恢复等。

## 主要输入文件：

 - CSV 文件 (cdpnei_ap.csv)：
包含 AP 与交换机及端口的对应关系。程序通过该文件查找 AP 掉线时对应的交换机 IP 地址和端口信息。
示例格式：
```
复制代码
ap_name,switch_name,switch_ip,connect_port
AP1,Switch1,192.168.1.1,GigabitEthernet1/0/1
AP2,Switch2,192.168.1.2,GigabitEthernet1/0/2
```

 - YAML 配置文件 (config.yaml)：

存储程序运行所需的配置信息，包括 syslog 服务器信息、邮件服务器信息、SSH 凭据等。
示例格式：

```yaml
复制代码
syslog:
  server: syslog_ip
  port: udp_port

email:
  smtp_server: your_smtp_server
  sender: your_sender_email
  recipients:
    - recipient1@example.com
    - recipient2@example.com
  smtp_port: 25

credentials:
  username: your_ssh_username
  password: your_ssh_password
  ```

依赖的外部库：
 - paramiko: 用于通过 SSH 与交换机建立连接并执行命令。
 - PyYAML: 用于加载和解析 YAML 配置文件。
 - csv: 用于读取 CSV 文件中的 AP 信息。
 - logging: 用于记录程序的运行日志和发送 syslog 信息。
 - smtplib: 用于发送邮件通知。

主要模块：
 - config.py：
负责加载 YAML 配置文件，包括 syslog、SSH 凭据、邮件服务器等配置。
提供日志系统的设置。
 - csv_operations.py：
负责从 CSV 文件中加载 AP 与交换机的映射信息。
 - ssh_operations.py：
负责通过 SSH 连接交换机，并执行端口重启命令。
 - syslog_listener.py：
负责监听 syslog 消息，解析 AP 掉线或恢复的相关信息，并调用相应的处理逻辑。
 - main.py：
主程序入口，负责整合各个模块，启动 syslog 监听器，并处理异常情况。

增加get_ap_info_dynamically模块，使用API从DNAC获取AP cdp信息，静态csv作为备选。
对应模块dnac_api。
- YAML 配置文件 (dnac.yaml)：
```yaml
dnac:
  ip: "1.1.1.1"
  username: "username"
  password: "password"
```




