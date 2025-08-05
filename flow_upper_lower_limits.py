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
    result = asyncio.run(gate_flow_upper_lower_limits("2025-08-05", "2025-08-15", []))
    print(result)


