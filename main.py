"""
主程序调用
"""
from visa_lib.visa_lib import VisaInstrumentManager


if __name__ == "__main__":
    manager = VisaInstrumentManager()

    # 打印所有设备
    for res, info in manager.get_devices().items():
        print(f"{res} -> {info['idn']} (backend={info['backend']})")

    # 获取一个带自动重连的设备（最多重试 3 次）
    inst = manager.get_instrument("CMW", max_retries=3)

    if inst:
        print(inst.query("*IDN?"))   # 掉线时会尝试重连，最多 3 次
