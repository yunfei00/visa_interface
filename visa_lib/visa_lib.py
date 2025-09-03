import json
import os
import pyvisa


class VisaInstrumentManager:
    def __init__(self, config_file="visa_devices.json"):
        self.config_file = config_file
        self.devices = {}

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
        """搜索 VISA 设备并更新配置文件"""
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()

        devices = {}
        for res in resources:
            try:
                inst = rm.open_resource(res)
                inst.timeout = 2000
                idn = inst.query("*IDN?").strip()
                devices[res] = idn
                inst.close()
            except Exception as e:
                devices[res] = f"未知设备/无法识别 ({e})"

        self.devices = devices
        self._save_to_config()
        print("🔍 已刷新并保存 VISA 设备信息")

    def _save_to_config(self):
        """保存设备信息到配置文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.devices, f, indent=4, ensure_ascii=False)

    def get_devices(self):
        """获取已知设备字典 {资源: 名称}"""
        return self.devices

    def get_instrument(self, keyword=None):
        """
        获取一个仪表实例
        - keyword=None: 返回第一个设备
        - keyword=字符串: 匹配IDN或资源名
        """
        rm = pyvisa.ResourceManager()
        for res, name in self.devices.items():
            if keyword is None or keyword.lower() in res.lower() or keyword.lower() in name.lower():
                try:
                    inst = rm.open_resource(res)
                    print(f"✅ 已连接到: {res} ({name})")
                    return inst
                except Exception as e:
                    print(f"⚠️ 打开 {res} 失败: {e}")
        return None


if __name__ == "__main__":
    manager = VisaInstrumentManager()

    # 打印所有已知设备
    devices = manager.get_devices()
    for res, name in devices.items():
        print(f"{res} -> {name}")

    # 获取某个仪表
    inst = manager.get_instrument("CMW")  # 关键字匹配
    if inst:
        print(inst.query("*IDN?"))
        inst.close()
