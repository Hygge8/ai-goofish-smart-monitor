class GoofishMonitorError(Exception):
    """项目基础异常。"""


class SearchBlockedError(GoofishMonitorError):
    """搜索页疑似被登录、验证、风控或异常页面拦截。"""


class AccountStateError(GoofishMonitorError):
    """账号登录态不可用。"""
