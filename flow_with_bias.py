import asyncio
import ast
import requests
import json

default_stations = ["铜街子", "龚嘴", "深溪沟", "大岗山", "瀑布沟", "猴子岩", "沙南", "枕头坝"]


def fetch_flow_data(station: str, data_type: str, start_time: str, end_time: str, token: str):
    url = "http://10.163.25.156:11105/ai_workflow/workflow/workflow_api_run"
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsidXNlcm5hbWUiOiJhZG1pbiIsInVzZXJfaWQiOiI5OTkifSwiZXhwIjoxNzU0NTM3MzQ2fQ.MTiQI8TFiO2ITYIY_SHgkGSXV_jMeEpVG7Q_0a6aaeY'}
    data_type_cn = "预报" if data_type == "forecast" else "实测"
    payload = {'user_id': 999,
               'wid': 'db18dab3a8d54af59a655668127ba3c7',
               'input_data': {
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.text': f'{station}{start_time}至{end_time}入库流量',
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.type': '逐日',
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.dataType': data_type_cn,
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.system_str': '数据中台'
               },
               'stream': False
               }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


async def gate_flow_with_bias1(start_time: str, end_time: str, sites: list = None, token: str = " ") -> str:
    """
    查询电站的入库流量数据，并以 Markdown 表格形式返回指定日期范围内的平均绝对偏差信息。
    功能：
    -------
    本工具获取指定电站在过去一段时间内的预报入库流量和实测入库流量，并计算两者之间的偏差。
    返回的 Markdown 表格包含每个电站在指定日期范围内的流量偏差信息，偏差计算为
    预报流量减去实测流量。

    参数：
    ---------
    start_time : str
        查询的起始日期，格式为 "YYYY-MM-DD"。

    end_time : str
        查询的结束日期，格式为 "YYYY-MM-DD"。

    sites : list
        要查询的电站名称列表，如["电站1", "电站2"]。如果未提供，默认为查询所有电站（大渡河流域的八个电站）。

    返回：
    --------
    str:
        一个 Markdown 格式的表格字符串，包含所查询电站在指定日期范围内的入库流量平均绝对偏差信息。
    """

    # 若sites为空或None，使用默认电站
    if not sites:
        sites = default_stations

    async def fetch_station_data(station, data_type):
        # 用asyncio.to_thread将同步IO变为异步
        return await asyncio.to_thread(fetch_flow_data, station, data_type, start_time, end_time, token)

    # 并发查询所有电站的预报和实测数据
    forecast_tasks = [fetch_station_data(station, "forecast") for station in sites]
    actual_tasks = [fetch_station_data(station, "actual") for station in sites]
    forecast_results, actual_results = await asyncio.gather(
        asyncio.gather(*forecast_tasks),
        asyncio.gather(*actual_tasks)
    )

    # 处理数据，计算偏差
    station_avg_bias = []
    station_actual_avg = []
    for idx, station in enumerate(sites):
        try:
            forecast_data = forecast_results[idx]
            actual_data = actual_results[idx]
            forecast_list = ast.literal_eval(forecast_data["data"]["文本呈现"])
            actual_list = ast.literal_eval(actual_data["data"]["文本呈现"])
            # 构建日期到流量的映射，流量四舍五入取整
            forecast_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in forecast_list}
            actual_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in actual_list}
            # 取所有日期的交集
            common_dates = set(forecast_dict.keys()) & set(actual_dict.keys())
            # 绝对平均偏差应为(预测-实测)
            bias_list = [forecast_dict[date] - actual_dict[date] for date in common_dates]
            actual_list_for_avg = [actual_dict[date] for date in common_dates]
            avg_bias = sum(bias_list) / len(bias_list) if bias_list else None
            actual_avg = sum(actual_list_for_avg) / len(actual_list_for_avg) if actual_list_for_avg else None
        except Exception:
            avg_bias = None
            actual_avg = None
        station_avg_bias.append(avg_bias)
        station_actual_avg.append(actual_avg)

    # markdown表格
    headers = ["电站"] + sites
    table = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    row_bias = ["绝对平均偏差(m³/s)"] + [str(round(b)) if b is not None else "N/A" for b in station_avg_bias]
    row_percent = ["相对平均偏差(%)"]
    percent_list = []  # 用于echarts
    for b, a, f in zip(station_avg_bias, station_actual_avg, forecast_results):
        try:
            forecast_data = f
            actual_avg = a
            forecast_list = ast.literal_eval(forecast_data["data"]["文本呈现"])
            forecast_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in forecast_list}
            if actual_avg is not None and actual_avg != 0:
                idx = station_actual_avg.index(actual_avg)
                actual_data = actual_results[idx]
                actual_list = ast.literal_eval(actual_data["data"]["文本呈现"])
                actual_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in actual_list}
                common_dates = set(forecast_dict.keys()) & set(actual_dict.keys())
                forecast_avg = sum([forecast_dict[date] for date in common_dates]) / len(
                    common_dates) if common_dates else None
                if forecast_avg is not None:
                    percent = round((forecast_avg - actual_avg) / actual_avg * 100, 1)
                    row_percent.append(f"{percent}")
                    percent_list.append(percent)
                else:
                    row_percent.append("N/A")
                    percent_list.append(0)
            else:
                row_percent.append("N/A")
                percent_list.append(0)
        except Exception:
            row_percent.append("N/A")
            percent_list.append(0)
    table.append("| " + " | ".join(row_bias) + " |")
    table.append("| " + " | ".join(row_percent) + " |")
    mark_str = "\n".join(table)

    # Echart部分
    title = f"{start_time}至{end_time}各电站入库流量偏差平均值"
    echarts_str = generate_station_bias_option(
        title,
        sites,
        [round(b) if b is not None else 0 for b in station_avg_bias],
        percent_list,
        y1_name="绝对平均偏差(m³/s)",
        y2_name="相对平均偏差(%)"
    )

    r_str = "<text>### " + title + "\n\n" + mark_str + "</text>\n<display>" + json.dumps(echarts_str,
                                                                                        ensure_ascii=False) + "</display>"
    return r_str

async def gate_flow_with_bias2(start_time: str, end_time: str, sites: list = None, token: str = " ") -> dict|None:
    """
    查询电站的入库流量数据，并以 Markdown 表格形式返回指定日期范围内的平均绝对偏差信息。
    功能：
    -------
    本工具获取指定电站在过去一段时间内的预报入库流量和实测入库流量，并计算两者之间的偏差。
    返回的 Markdown 表格包含每个电站在指定日期范围内的流量偏差信息，偏差计算为
    预报流量减去实测流量。

    参数：
    ---------
    start_time : str
        查询的起始日期，格式为 "YYYY-MM-DD"。

    end_time : str
        查询的结束日期，格式为 "YYYY-MM-DD"。

    sites : list
        要查询的电站名称列表，如["电站1", "电站2"]。如果未提供，默认为查询所有电站（大渡河流域的八个电站）。

    返回：
    --------
    str:
        一个 Markdown 格式的表格字符串，包含所查询电站在指定日期范围内的入库流量平均绝对偏差信息。
    """


    # 若sites为空或None，使用默认电站
    if not sites:
        sites = default_stations

    async def fetch_station_data(station, data_type):
        # 用asyncio.to_thread将同步IO变为异步
        return await asyncio.to_thread(fetch_flow_data, station, data_type, start_time, end_time, token)

    # 并发查询所有电站的预报和实测数据
    forecast_tasks = [fetch_station_data(station, "forecast") for station in sites]
    actual_tasks = [fetch_station_data(station, "actual") for station in sites]
    forecast_results, actual_results = await asyncio.gather(
        asyncio.gather(*forecast_tasks),
        asyncio.gather(*actual_tasks)
    )

    # 处理数据，计算偏差
    station_avg_bias = []
    station_actual_avg = []
    for idx, station in enumerate(sites):
        try:
            forecast_data = forecast_results[idx]
            actual_data = actual_results[idx]
            forecast_list = ast.literal_eval(forecast_data["data"]["文本呈现"])
            actual_list = ast.literal_eval(actual_data["data"]["文本呈现"])
            # 构建日期到流量的映射，流量四舍五入取整
            forecast_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in forecast_list}
            actual_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in actual_list}
            # 取所有日期的交集
            common_dates = set(forecast_dict.keys()) & set(actual_dict.keys())
            # 绝对平均偏差应为(预测-实测)
            bias_list = [forecast_dict[date] - actual_dict[date] for date in common_dates]
            actual_list_for_avg = [actual_dict[date] for date in common_dates]
            avg_bias = sum(bias_list) / len(bias_list) if bias_list else None
            actual_avg = sum(actual_list_for_avg) / len(actual_list_for_avg) if actual_list_for_avg else None
        except Exception:
            avg_bias = None
            actual_avg = None
        station_avg_bias.append(avg_bias)
        station_actual_avg.append(actual_avg)
    row_bias = [str(round(b)) if b is not None else "N/A" for b in station_avg_bias]

    # markdown表格
    row_percent = ["相对平均偏差(%)"]
    percent_list = []  # 用于echarts
    for b, a, f in zip(station_avg_bias, station_actual_avg, forecast_results):
        try:
            forecast_data = f
            actual_avg = a
            forecast_list = ast.literal_eval(forecast_data["data"]["文本呈现"])
            forecast_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in forecast_list}
            if actual_avg is not None and actual_avg != 0:
                idx = station_actual_avg.index(actual_avg)
                actual_data = actual_results[idx]
                actual_list = ast.literal_eval(actual_data["data"]["文本呈现"])
                actual_dict = {item["dataTime"][:10]: round(item["dataValue"]) for item in actual_list}
                common_dates = set(forecast_dict.keys()) & set(actual_dict.keys())
                forecast_avg = sum([forecast_dict[date] for date in common_dates]) / len(
                    common_dates) if common_dates else None
                if forecast_avg is not None:
                    percent = round((forecast_avg - actual_avg) / actual_avg * 100, 1)
                    row_percent.append(f"{percent}")
                    percent_list.append(percent)
                else:
                    row_percent.append("N/A")
                    percent_list.append(0)
            else:
                row_percent.append("N/A")
                percent_list.append(0)
        except Exception:
            row_percent.append("N/A")
            percent_list.append(0)
    pmiscodes = {
        "15000016": ["猴子岩", "猴子岩水库"],
        "15000007": ["大岗山", "大岗山水库"],
        "15000002": ["瀑布沟", "瀑布沟水库"],
        "15000003": ["深溪沟", "深溪沟水库"],
        "15000008": ["枕头坝", "枕头坝一级水库"],
        "15000017": ["沙南", "沙南水库"],
        "15000001": ["龚嘴", "龚嘴水库"],
        "15000000": ["铜街子", "铜街子水库"]
    }

    # percent_dict={key:v for key in pmiscodes for k in sites if k in pmiscodes[key] for v in percent_list if sites.index(k) == percent_list.index(v) }
    percent_dict={key: {"rate":r,"value":v} for key in pmiscodes for k in sites if k in pmiscodes[key] for r in percent_list if sites.index(k) == percent_list.index(r)  for v in row_bias if sites.index(k) == row_bias.index(v) }

    return percent_dict

# 动态生成 ECharts option 的函数

def generate_station_bias_option(title: str, station_names: list, avg_bias_list: list, percent_list: list,
                                 y1_name: str = "绝对平均偏差(m³/s)", y2_name: str = "相对平均偏差(%)") -> dict:
    """
    根据输入的标题、电站名列表、平均偏差列表和百分比列表，动态生成双y轴ECharts option。
    :param title: 图表标题
    :param station_names: 电站名称列表(X轴)
    :param avg_bias_list: 各电站平均偏差(Y轴1)
    :param percent_list: 各电站相对平均偏差(Y轴2)
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
                "data": avg_bias_list,
                "itemStyle": {
                    "color": '#008AFA'
                },
                "barGap": 0,
                "yAxisIndex": 0
            },
            {
                "name": y2_name,
                "type": 'line',
                "data": percent_list,
                "itemStyle": {
                    "color": '#FFAA00'
                },
                "lineStyle": {
                    "color": '#FFAA00',
                    "width": 3
                },
                "symbol": 'circle',
                "symbolSize": 8,
                "yAxisIndex": 1
            }
        ]
    }
if __name__ == "__main__":
    # mcp.run(transport='stdio')
    inflow_datas = {
        "inflow_datas": {},
        "changed_inflow_datas": {}
    }
    result = asyncio.run(gate_flow_with_bias1("2025-07-25", "2025-07-29",[], "111"))
    print(result)
    result = asyncio.run(gate_flow_with_bias2("2025-07-25", "2025-07-29",[], "111"))
    print(result)