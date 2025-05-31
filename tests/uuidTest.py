import uuid
import hashlib
import getmac
import psutil
import platform

def get_device_id() -> str:
    # Собираем уникальные данные системы
    mac_address = getmac.get_mac_address() or ""
    disk_serial = (psutil.disk_partitions()[0].device if psutil.disk_partitions() else "")
    cpu_id = platform.processor()
    system_info = f"{mac_address}{disk_serial}{cpu_id}"

    # Хешируем, чтобы избежать прямого раскрытия данных
    hash_object = hashlib.sha256(system_info.encode())
    device_id = str(uuid.UUID(hash_object.hexdigest()[:32]))
    
    return device_id

device_id = get_device_id()
print("Device ID:", device_id)