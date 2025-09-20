"""
visa 的接口，并且包含了命令集接口
具体的仪表只需要导入对应的命令集接口，只需要实现逻辑即可
"""
import json
import os
import pyvisa
import time

from visa_commands import Common, Scope


class VisaInstrumentManager:
    def __init__(self, config_file="visa_devices.json"):
        self.config_file = config_file
        self.devices = {}
        # 这个是通用的 都需要
        self.cmd_common = Common()

        # 这个根据实际的仪表导入
        self.cmd_data = Scope()

        if os.path.exists(self.config_file):
            self._load_from_config()
        else:
            self.refresh_devices()

    def _load_from_config(self):
        """从配置文件读取已保存的仪表信息"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.devices = json.load(f)
            print("✅ 从配置文件加载 VISA 设备信息")
        except Exception as e:
            print(f"⚠️ 配置文件读取失败: {e}")
            self.devices = {}
            self.refresh_devices()

    def refresh_devices(self):
        """搜索所有 VISA 后端的设备并更新配置文件"""
        backends = ["@ni", "@keysight", "@rs", "@sim", ""]
        devices = {}

        for backend in backends:
            try:
                rm = pyvisa.ResourceManager(backend)
                resources = rm.list_resources()
                for res in resources:
                    try:
                        inst = rm.open_resource(res)
                        inst.timeout = 2000
                        # idn = inst.query("*IDN?").strip()
                        idn = inst.query(self.cmd_common.Info.IDN).strip()
                        devices[res] = {"idn": idn, "backend": backend}
                        inst.close()
                    except Exception as e:
                        devices[res] = {"idn": f"未知设备/无法识别 ({e})", "backend": backend}
            except Exception as e:
                print(f"⚠️ 后端 {backend} 不可用: {e}")

        self.devices = devices
        self._save_to_config()
        print("🔍 已刷新并保存 VISA 设备信息")

    def _save_to_config(self):
        """保存设备信息到配置文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.devices, f, indent=4, ensure_ascii=False)

    def get_devices(self):
        """获取已知设备字典 {资源: {idn, backend}}"""
        return self.devices

    def get_instrument(self, keyword=None, auto_reconnect=True, max_retries=3):
        """
        获取一个仪表实例 (支持自动重连)
        """
        for res, info in self.devices.items():
            idn = info.get("idn", "")
            backend = info.get("backend", "")
            if keyword is None or keyword.lower() in res.lower() or keyword.lower() in idn.lower():
                return ReconnectableInstrument(res, backend, auto_reconnect, max_retries)
        return None


class ReconnectableInstrument:
    """带自动重连功能的仪表封装"""

    def __init__(self, resource, backend, auto_reconnect=True, max_retries=3):
        self.resource = resource
        self.backend = backend
        self.auto_reconnect = auto_reconnect
        self.max_retries = max_retries
        self.rm = None
        self.inst = None
        self._connect()

    def _connect(self):
        if self.inst:
            try:
                self.inst.close()
            except Exception:
                pass
        self.rm = pyvisa.ResourceManager(self.backend)
        self.inst = self.rm.open_resource(self.resource)
        self.inst.timeout = 3000
        print(f"🔌 已连接到 {self.resource} via {self.backend}")

    def _safe_call(self, func, *args, **kwargs):
        """包装器: 带自动重连和最大重试次数"""
        retries = 0
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not self.auto_reconnect:
                    raise
                retries += 1
                if retries > self.max_retries:
                    raise RuntimeError(f"❌ 设备 {self.resource} 重连超过 {self.max_retries} 次仍失败: {e}")
                print(f"⚠️ 操作失败: {e}, 正在重连({retries}/{self.max_retries})...")
                time.sleep(1)
                self._connect()

    def query(self, cmd):
        return self._safe_call(self.inst.query, cmd)

    def write(self, cmd):
        return self._safe_call(self.inst.write, cmd)

    def read(self):
        return self._safe_call(self.inst.read)

    def close(self):
        if self.inst:
            self.inst.close()


if __name__ == "__main__":
    manager = VisaInstrumentManager()

    # 打印所有设备
    for res, info in manager.get_devices().items():
        print(f"{res} -> {info['idn']} (backend={info['backend']})")

    # 获取一个带自动重连的设备（最多重试 3 次）
    inst = manager.get_instrument("CMW", max_retries=3)

    if inst:
        print(inst.query("*IDN?"))   # 掉线时会尝试重连，最多 3 次
