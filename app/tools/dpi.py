import ctypes

def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 系统级 DPI 感知 [[9]]
    except Exception as e:
        print(f"DPI 设置失败: {e}")