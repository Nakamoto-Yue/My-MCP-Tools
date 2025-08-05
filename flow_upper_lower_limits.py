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
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.type': '上下限',
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.dataType': data_type_cn,
                   '9e895884-591f-455a-a00c-4e9eac9a09d0.system_str': '数据中台'
               },
               'stream': False
               }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # mcp.run(transport='stdio')
    print(fetch_flow_data)