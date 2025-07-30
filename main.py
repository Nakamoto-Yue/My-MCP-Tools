# server.py
from mcp.server.fastmcp import FastMCP
import operator
import ast

# Create an MCP server
mcp = FastMCP("Demo")


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

# MCP工具9：获取预报降雨色斑图
@mcp.tool()
def get_focast_raining_pictures(startTime: str, endTime: str) -> dict:
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

# MCP工具11：获取小时级预报降雨色斑图
@mcp.tool()
def get_hourly_focast_raining_pictures(startTime: str, endTime: str) -> dict:
    """
    获取小时级预报降雨色斑图地址。
    参数：
        startTime: 开始日期，格式为'YYYY-MM-DD HH:MM:SS'
        endTime: 结束日期，格式为'YYYY-MM-DD HH:MM:SS'
    返回：
        字典，每一项key为日期字符串，value为小时级预报降雨色斑图地址。
    规则：
        如果用户输入的起始时间早于系统时间，则发布时间为用户输入的起始时间，key从用户输入的起始时间到结束时间，value为"起始时间_预报时间.png"。
        如果用户输入的起始时间等于或晚于系统时间，则发布时间为系统时间减一小时，key从系统时间到用户输入的结束时间，value为"系统时间_预报时间.png"。
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")
