import asyncio
import ast
import requests
import json

default_stations = ["龚嘴", "大岗山", "瀑布沟", "猴子岩"]


def fetch_flow_data(station: str, data_type: str, start_time: str, end_time: str, token: str):
    url = "http://10.163.25.156:11105/ai_workflow/workflow/workflow_api_run"
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsidXNlcm5hbWUiOiJhZG1pbiIsInVzZXJfaWQiOiI5OTkifSwiZXhwIjoxNzU0NTM3MzQ2fQ.MTiQI8TFiO2ITYIY_SHgkGSXV_jMeEpVG7Q_0a6aaeY'}
    data_type_cn = "预报" if data_type == "forecast" else "实测"
    payload = {'user_id': 999,
               'wid': 'db18dab3a8d54af59a655668127ba3c7',
               'input_data': {
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.text': f'{station}{start_time}至{end_time}入库流量',
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.type': '上下限',
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.dataType': data_type_cn,
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.system_str': '数据中台'
               },
               'stream': False
               }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


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
    station_data = {}
    for idx, station in enumerate(sites):
        try:
            data = results[idx]
            data_list = ast.literal_eval(data["data"]["文本呈现"])
            
            # 构建日期到上下限的映射
            for item in data_list:
                date = item["dataTime"][:10]  # 提取日期部分
                if date not in station_data:
                    station_data[date] = {}
                station_data[date][f"{station}上限"] = round(item["up"])
                station_data[date][f"{station}下限"] = round(item["down"])
            
        except Exception as e:
            print(f"处理{station}数据时出错: {e}")
            continue

    # 按日期排序
    sorted_dates = sorted(station_data.keys())
    
    if not sorted_dates:
        return "没有找到有效数据"

    # 生成markdown表格
    # 第一行：时间 + 各电站的上下限列
    headers = ["时间"]
    for station in sites:
        headers.append(f"{station}上限m3/s")
        headers.append(f"{station}下限m3/s")
    
    table = ["| " + " | ".join(headers) + " |"]
    table.append("|" + "|".join(["------"] * len(headers)) + "|")
    
    # 数据行：按日期输出
    for date in sorted_dates:
        row = [date]
        for station in sites:
            up_key = f"{station}上限"
            down_key = f"{station}下限"
            row.append(str(station_data[date].get(up_key, "N/A")))
            row.append(str(station_data[date].get(down_key, "N/A")))
        table.append("| " + " | ".join(row) + " |")
    
    mark_str = "\n".join(table)

    # 生成ECharts图表配置
    title = f"{start_time}至{end_time}各电站入库流量上下限"
    echarts_str = generate_daily_limits_option(
        title,
        sorted_dates,
        sites,
        station_data
    )

    # 返回包含markdown表格和ECharts图表的完整结果
    # r_str = "\n" + title + "\n\n" + mark_str + "\n\n<display>" + json.dumps(echarts_str,ensure_ascii=False, indent=2) + "</display>"
    r_str = "\n" + title + "\n\n" + mark_str + "\n\n<display>"
    return r_str


def generate_daily_limits_option(title: str, dates: list, stations: list, station_data: dict) -> dict:
    """
    根据日期、电站和上下限数据，生成时间序列ECharts option。
    :param title: 图表标题
    :param dates: 日期列表
    :param stations: 电站列表
    :param station_data: 按日期和电站存储的数据
    :return: ECharts option 字典
    """
    series = []
    colors = ['#FF4D4F', '#52C41A', '#1890FF', '#FAAD14', '#722ED1', '#13C2C2', '#EB2F96', '#F5222D']
    
    # 为每个电站生成上下限数据系列
    for i, station in enumerate(stations):
        color_index = i % len(colors)
        
        # 上限数据系列
        up_data = []
        for date in dates:
            up_key = f"{station}上限"
            value = station_data[date].get(up_key, 0)
            up_data.append(value)
        
        series.append({
            "name": f"{station}上限",
            "type": "line",
            "data": up_data,
            "itemStyle": {"color": colors[color_index]},
            "lineStyle": {"color": colors[color_index], "width": 2},
            "symbol": "circle",
            "symbolSize": 6
        })
        
        # 下限数据系列
        down_data = []
        for date in dates:
            down_key = f"{station}下限"
            value = station_data[date].get(down_key, 0)
            down_data.append(value)
        
        series.append({
            "name": f"{station}下限",
            "type": "line",
            "data": down_data,
            "itemStyle": {"color": colors[color_index]},
            "lineStyle": {"color": colors[color_index], "width": 2, "type": "dashed"},
            "symbol": "circle",
            "symbolSize": 6
        })
    
    return {
        "title": {
            "text": title,
            "left": 14,
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": [f"{station}上限" for station in stations] + [f"{station}下限" for station in stations],
            "icon": "roundRect",
            "top": 50,
            "itemWidth": 12,
            "itemHeight": 8,
            "itemGap": 16,
            "textStyle": {
                "rich": {
                    "a": {
                        "verticalAlign": "middle"
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
            "type": "category",
            "data": dates,
            "axisTick": {
                "show": False
            },
            "axisLabel": {
                "textStyle": {
                    "color": "#86909C"
                },
                "rotate": 45
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#c9cdd4"
                }
            }
        },
        "yAxis": {
            "type": "value",
            "name": "流量(m³/s)",
            "nameTextStyle": {
                "padding": [0, 0, 0, 0]
            },
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": series
    }


if __name__ == "__main__":
    # 测试调用函数
    result = gate_flow_upper_lower_limits("2025-08-05", "2025-08-15", [])

    print(result)


