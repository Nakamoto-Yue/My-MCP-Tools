# server.py
from mcp.server.fastmcp import FastMCP
import operator
import ast

# Create an MCP server
mcp = FastMCP("Demo")

# MCP工具9：获取预报降雨色斑图
@mcp.tool()
def get_forecast_raining_pictures(startTime: str, endTime: str) -> dict:
    """
    获取预报降雨色斑图地址。
    参数：
        startTime: 开始日期，格式为'YYYY-MM-DD'
        endTime: 结束日期，格式为'YYYY-MM-DD'
    返回：
        字典，每一项key为日期字符串，value为预报降雨色斑图地址。
    规则：
        如果用户输入的起始日期早于系统当天，则发布日期为用户输入的起始日期，key从用户输入的起始日期到结束日期，value为"起始日期080000_预报日期080000.png"。
        如果用户输入的起始日期等于或晚于系统当天，则发布日期为系统当天，key从系统当天到用户输入的结束日期，value为"系统当天080000_预报日期080000.png"。
        字典的第一项（key等于发布日期的那一天）不输出。
    """
    import re
    from datetime import datetime, timedelta

    def parse_date(date_str):
        date_str = date_str.strip()
        # 只支持 YYYY-MM-DD 格式
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            raise ValueError(f"日期格式错误，请严格按照YYYY-MM-DD格式输入，如2025-07-15，当前输入: {date_str}")
        return date_str

    def daterange(start_date, end_date):
        for n in range((end_date - start_date).days + 1):
            yield start_date + timedelta(n)

    today = datetime.today().date()
    
    # 解析开始和结束时间
    user_start = datetime.strptime(parse_date(startTime), "%Y-%m-%d").date()
    user_end = datetime.strptime(parse_date(endTime), "%Y-%m-%d").date()

    if user_start > user_end:
        raise ValueError("开始日期不能晚于结束日期")

    if user_start < today:
        publish_date = user_start
        key_start = user_start
    else:
        publish_date = today
        key_start = today

    result = {}
    for d in daterange(key_start, user_end):
        if d == publish_date:
            continue  # 跳过第一项
        pub_str = publish_date.strftime("%Y%m%d080000")
        forecast_str = d.strftime("%Y%m%d080000")
        # key值减一天
        key_date = d - timedelta(days=1)
        result[key_date.strftime("%Y-%m-%d")] = f"http://10.163.25.156:8502/hsimg/img/1381/{pub_str}_{forecast_str}.png"
    return result


# MCP工具10：获取实测降雨色斑图
@mcp.tool()
def get_actual_raining_pictures(startTime: str, endTime: str) -> dict:
    """
    获取实测降雨色斑图地址。
    参数：
        startTime: 开始日期，格式为'YYYY-MM-DD'
        endTime: 结束日期，格式为'YYYY-MM-DD'
    返回：
        字典，每一项key为日期字符串，value为实测降雨色斑图地址。
    规则：
        今天及之前的地址为http://10.163.25.156:8502/hsimg/img/1301/yyyymmdd090000.png
    """
    import re
    from datetime import datetime, timedelta

    def parse_date(date_str):
        date_str = date_str.strip()
        # 只支持 YYYY-MM-DD 格式
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            raise ValueError(f"日期格式错误，请严格按照YYYY-MM-DD格式输入，如2025-07-15，当前输入: {date_str}")
        return date_str

    def daterange(start_date, end_date):
        for n in range((end_date - start_date).days + 1):
            yield start_date + timedelta(n)

    today = datetime.today().date()
    
    # 解析开始和结束时间
    start_date = datetime.strptime(parse_date(startTime), "%Y-%m-%d").date()
    end_date = datetime.strptime(parse_date(endTime), "%Y-%m-%d").date()
    
    if start_date > end_date:
        raise ValueError("开始日期不能晚于结束日期")

    result = {}
    for d in daterange(start_date, end_date):
        date_str = d.strftime('%Y-%m-%d')
        ymd = d.strftime('%Y%m%d')
        if d <= today:
            result[date_str] = f"http://10.163.25.156:8502/hsimg/img/1301/{ymd}090000.png"
        
    return result


# MCP工具11：获取小时级预报降雨色斑图
@mcp.tool()
def get_hourly_forecast_pictures(startTime: str, endTime: str) -> dict:
    """
    获取小时级预报降雨色斑图地址。
    参数：
        startTime: 开始时间，格式为'YYYY-MM-DD HH:MM:SS'
        endTime: 结束时间，格式为'YYYY-MM-DD HH:MM:SS'
    返回：
        字典，每一项key为日期字符串，value为小时级预报降雨色斑图地址。
    规则：
        如果用户输入的起始时间早于系统时间，则发布时间为用户输入的起始时间，key从用户输入的起始时间到结束时间，value为"起始时间_预报时间.png"。
        如果用户输入的起始时间等于或晚于系统时间，则发布时间为系统时间减一小时，key从系统时间减一小时到用户输入的结束时间，value为"系统时间_预报时间.png"。
    """
    import re
    from datetime import datetime, timedelta

    def parse_datetime(datetime_str):
        datetime_str = datetime_str.strip()
        # 支持 YYYY-MM-DD HH:MM:SS 格式
        if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', datetime_str):
            raise ValueError(f"日期时间格式错误，请严格按照YYYY-MM-DD HH:MM:SS格式输入，如2025-07-15 08:00:00，当前输入: {datetime_str}")
        return datetime_str

    def daterange(start_datetime, end_datetime):
        current = start_datetime
        while current <= end_datetime:
            yield current
            current += timedelta(hours=1)

    now = datetime.now()
    
    # 解析开始和结束时间
    user_start = datetime.strptime(parse_datetime(startTime), "%Y-%m-%d %H:%M:%S")
    user_end = datetime.strptime(parse_datetime(endTime), "%Y-%m-%d %H:%M:%S")

    if user_start > user_end:
        raise ValueError("开始时间不能晚于结束时间")

    if user_start < now:
        publish_time = user_start
        key_start = user_start
    else:
        publish_time = now - timedelta(hours=1)
        key_start = now - timedelta(hours=1)

    result = {}
    for d in daterange(key_start, user_end):
        if d == publish_time:
            continue  # 跳过第一项
        # 将分钟和秒数置为0
        pub_datetime = publish_time.replace(minute=0, second=0)
        forecast_datetime = d.replace(minute=0, second=0)
        pub_str = pub_datetime.strftime("%Y%m%d%H%M%S")
        forecast_str = forecast_datetime.strftime("%Y%m%d%H%M%S")
        # key值减一小时
        key_datetime = d - timedelta(hours=1)
        if user_start >= now:
            # 如果用户输入的起始时间等于或晚于系统时间，key值的时间部分全部置为0
            key_datetime = key_datetime.replace(minute=0, second=0)
        result[key_datetime.strftime("%Y-%m-%d %H:%M:%S")] = f"http://10.163.25.156:8502/hsimg/img/1500/{pub_str}_{forecast_str}.png"
    return result


# MCP工具12：获取小时级实测降雨色斑图
@mcp.tool()
def get_hourly_actual_pictures(startTime: str, endTime: str) -> dict:
    """
    获取小时级实测降雨色斑图地址。
    参数：
        startTime: 开始时间，格式为'YYYY-MM-DD HH:MM:SS'
        endTime: 结束时间，格式为'YYYY-MM-DD HH:MM:SS'
    返回：
        字典，每一项key为日期字符串，value为小时级实测降雨色斑图地址。
    规则：
        最终输出格式：http://10.163.25.156:9006/ddh/api/getMeteoSumToPNG?开始时间&结束时间
    """
    import re
    from datetime import datetime, timedelta

    def parse_datetime(datetime_str):
        datetime_str = datetime_str.strip()
        # 支持 YYYY-MM-DD HH:MM:SS 格式
        if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', datetime_str):
            raise ValueError(f"日期时间格式错误，请严格按照YYYY-MM-DD HH:MM:SS格式输入，如2025-07-15 08:00:00，当前输入: {datetime_str}")
        return datetime_str

    def daterange(start_datetime, end_datetime):
        current = start_datetime
        while current <= end_datetime:
            yield current
            current += timedelta(hours=1)

    # 解析开始和结束时间
    start_datetime = datetime.strptime(parse_datetime(startTime), "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(parse_datetime(endTime), "%Y-%m-%d %H:%M:%S")

    if start_datetime > end_datetime:
        raise ValueError("开始时间不能晚于结束时间")

    result = {}
    for d in daterange(start_datetime, end_datetime):
        # 格式化时间为API所需的格式
        start_str = d.strftime("%Y-%m-%d %H:%M:%S")
        end_str = (d + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建API URL
        url = f"http://10.163.25.156:9006/ddh/api/getMeteoSumToPNG?startTime={start_str}&endTime={end_str}"
        result[start_str] = url
    
    return result



# MCP工具13：获取入库流量概率预报上下限
@mcp.tool()
def gate_flow_upper_lower_limits(start_time: str, end_time: str, sites: list = None) -> str:
    """
    查询电站入库流量概率预报上下限，并以 Markdown 表格形式返回指定日期范围内的。
    功能：
    -------
    本工具查询电站入库流量概率预报上下限（Q5和Q95），并返回指定日期范围内的上下限信息。

    参数：
    ---------
    start_time : str
        查询的起始日期，格式为 "YYYY-MM-DD"。

    end_time : str
        查询的结束日期，格式为 "YYYY-MM-DD"。

    sites : list
        要查询的电站名称列表，如["电站1", "电站2"]。如果未提供，默认为查询所有电站（大渡河流域的四个电站）。

    返回：
    --------
    str:
        一个 Markdown 格式的表格字符串
    """
    import os
    import json

    default_stations = ["龚嘴", "大岗山", "瀑布沟", "猴子岩"]

    # 若sites为空或None，使用默认电站
    if not sites:
        sites = default_stations

    # 模拟数据 - 使用本地JSON文件
    def get_mock_data(station):
        """获取模拟数据，直接从JSON文件读取"""
        import os
        
        # 构建JSON文件路径
        json_file_path = f"json_files/{station}日上下限.json"
        
        try:
            # 检查文件是否存在
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    # 读取JSON文件内容
                    json_content = f.read().strip()
                    # 解析JSON
                    import json as json_module
                    data = json_module.loads(json_content)
                    return data
            else:
                # 如果文件不存在，返回默认数据
                return {
                    "code": 404, 
                    "msg": f"File not found: {json_file_path}", 
                    "data": {"文本呈现": "[]"}
                }
        except Exception as e:
            # 如果读取失败，返回错误信息
            return {
                "code": 500, 
                "msg": f"Error reading file: {str(e)}", 
                "data": {"文本呈现": "[]"}
            }

    # 获取模拟数据
    results = [get_mock_data(station) for station in sites]

    # 处理数据，提取上下限信息
    station_up_data = []
    station_down_data = []
    for idx, station in enumerate(sites):
        try:
            data = results[idx]
            data_list = ast.literal_eval(data["data"]["文本呈现"])
            
            # 构建日期到上下限的映射
            up_dict = {item["dataTime"][:10]: round(item["up"]) for item in data_list}
            down_dict = {item["dataTime"][:10]: round(item["down"]) for item in data_list}
            
            # 计算平均值
            up_avg = sum(up_dict.values()) / len(up_dict) if up_dict else None
            down_avg = sum(down_dict.values()) / len(down_dict) if down_dict else None
            
        except Exception:
            up_avg = None
            down_avg = None
            
        station_up_data.append(up_avg)
        station_down_data.append(down_avg)

    # 生成markdown表格
    headers = ["电站"] + sites
    table = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    
    # 下限行（Q5）
    row_down = ["Q5下限(m³/s)"] + [str(round(down)) if down is not None else "N/A" for down in station_down_data]
    
    # 上限行（Q95）
    row_up = ["Q95上限(m³/s)"] + [str(round(up)) if up is not None else "N/A" for up in station_up_data]
    
    table.append("| " + " | ".join(row_down) + " |")
    table.append("| " + " | ".join(row_up) + " |")
    mark_str = "\n".join(table)

    # 生成ECharts图表配置
    title = f"{start_time}至{end_time}各电站入库流量上下限平均值"
    echarts_str = generate_station_limits_option(
        title,
        sites,
        [round(down) if down is not None else 0 for down in station_down_data],
        [round(up) if up is not None else 0 for up in station_up_data],
        y1_name="Q5下限(m³/s)",
        y2_name="Q95上限(m³/s)"
    )

    r_str = "<text>### " + title + "\n\n" + mark_str + "</text>\n<display>" + json.dumps(echarts_str,
                                                                                        ensure_ascii=False) + "</display>"
    return r_str


def generate_station_limits_option(title: str, station_names: list, down_list: list, up_list: list,
                                 y1_name: str = "Q5下限(m³/s)", y2_name: str = "Q95上限(m³/s)") -> dict:
    """
    根据输入的标题、电站名列表、下限和上限列表，动态生成双y轴ECharts option。
    :param title: 图表标题
    :param station_names: 电站名称列表(X轴)
    :param down_list: 各电站下限(Y轴1)
    :param up_list: 各电站上限(Y轴2)
    :param y1_name: Y轴1名称和图例名称
    :param y2_name: Y轴2名称和图例名称
    :return: ECharts option 字典
    """
    return {
        "title": {
            "text": title,
            "left": 14,
        },
        "tooltip": {
            "trigger": 'axis'
        },
        "legend": {
            "data": [y1_name, y2_name],
            "icon": 'roundRect',
            "top": 50,
            "itemWidth": 12,
            "itemHeight": 8,
            "itemGap": 16,
            "textStyle": {
                "rich": {
                    "a": {
                        "verticalAlign": 'middle'
                    }
                },
                "padding": [3, 0, 0, 0]
            }
        },
        "grid": {
            "top": 80,
            "bottom": 20,
            "left": 20,
            "right": 20,
            "containLabel": True
        },
        "xAxis": {
            "type": 'category',
            "data": station_names,
            "axisTick": {
                "show": False
            },
            "axisLabel": {
                "textStyle": {
                    "color": '#86909C'
                }
            },
            "axisLine": {
                "lineStyle": {
                    "color": '#c9cdd4'
                }
            }
        },
        "yAxis": [
            {
                "type": 'value',
                "name": y1_name,
                "nameTextStyle": {
                    "padding": [0, -20, 0, 0]
                },
                "splitLine": {
                    "lineStyle": {
                        "type": 'dashed'
                    }
                }
            },
            {
                "type": 'value',
                "name": y2_name,
                "nameTextStyle": {
                    "padding": [0, 0, 0, 0]
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": y1_name,
                "type": 'bar',
                "data": down_list,
                "itemStyle": {
                    "color": '#52C41A'
                },
                "barGap": 0,
                "yAxisIndex": 0
            },
            {
                "name": y2_name,
                "type": 'bar',
                "data": up_list,
                "itemStyle": {
                    "color": '#FF4D4F'
                },
                "barGap": 0,
                "yAxisIndex": 1
            }
        ]
    }



if __name__ == "__main__":
    mcp.run(transport="stdio")

