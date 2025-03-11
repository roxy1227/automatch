# WindowScreenshot 模块文档

## 概述

WindowScreenshot 是一个专门用于捕获 Windows 应用程序屏幕截图的 Python 模块，尤其适用于那些传统上难以捕获的应用程序，例如 DirectX 应用程序、最小化的窗口或具有自定义渲染方法的应用程序。

该模块提供多种捕获方法，并具备自动回退机制、窗口检测功能以及详细的窗口信息访问能力，使其成为自动化窗口捕获任务的强大解决方案。

## 主要功能

- 多种捕获方法（GDI、PrintWindow API、兼容 DirectX 的方法）
- 自动选择捕获方法并支持回退以应对难以捕获的窗口
- 支持通过标题或进程名称发现窗口
- 支持捕获最小化的窗口
- 空白/失败捕获检测
- 详细的窗口信息检索
- 快速操作的命令行接口

## 安装

### 前置条件

该模块依赖于以下 Python 包：

```
pip install numpy opencv-python pywin32 pillow
```

### 依赖项

- ctypes（标准库）
- numpy
- opencv-python (cv2)
- pywin32 (win32gui, win32ui, win32con, win32process)
- Pillow (PIL)

## 基本用法
注: `需要进行dpi优化，可使用dpi模块中的set_dpi_awareness方法`

### 查找窗口

```python
from window_screenshot import WindowScreenshot, list_all_windows, find_windows

# 列出所有可见窗口
all_windows = list_all_windows()

# 查找标题中包含 "Chrome" 的窗口
chrome_windows = find_windows("Chrome")
```

### 捕获屏幕截图

```python
from window_screenshot import capture_window, capture_window_by_title

# 通过窗口句柄捕获
hwnd = 123456  # 替换为实际窗口句柄
img = capture_window(hwnd, save_path="screenshot.png")

# 通过窗口标题捕获
img = capture_window_by_title("记事本", save_path="notepad.png")
```

### 使用 WindowScreenshot 类

```python
from window_screenshot import WindowScreenshot

# 创建实例并启用详细日志记录
screenshot = WindowScreenshot(verbose=True)

# 通过标题查找窗口
windows = screenshot.find_window("计算器")
if windows:
    # 获取窗口句柄
    hwnd = windows[0]["handle"]
    
    # 使用不同方法捕获
    img_standard = screenshot.screenshot_window(hwnd, method="standard")
    img_print = screenshot.screenshot_window(hwnd, method="printwindow")
    img_d3d = screenshot.screenshot_window(hwnd, method="d3d")
    img_auto = screenshot.screenshot_window(hwnd, method="auto")  # 尝试所有方法
    
    # 保存图像
    if img_auto:
        img_auto.save("calculator.png")
```

## 捕获方法

该模块提供多种捕获方法以处理不同类型的窗口：

1. **标准方法** (`method="standard"`): 使用 Windows GDI BitBlt 进行捕获。速度快，但可能无法兼容某些应用程序。

2. **PrintWindow 方法** (`method="printwindow"`): 使用 Windows PrintWindow API，与 DirectX 应用程序有更好的兼容性。

3. **D3D 方法** (`method="d3d"`): 使用 Windows WM_PRINT 消息，可能适用于其他方法无法捕获的某些 DirectX 应用程序。

4. **组合方法** (`method="composition"`): 一种回退方法，尝试强制窗口可见并置于前台后再进行捕获。

5. **自动方法** (`method="auto"`): 按顺序尝试所有方法（standard → printwindow → d3d → composition），直到获得有效图像。

## 命令行接口

该模块包含一个命令行接口，用于常见操作：

```
# 列出所有窗口
python window_screenshot.py list

# 通过句柄捕获特定窗口
python window_screenshot.py capture 123456 output.png [method]

# 通过标题查找并捕获窗口
python window_screenshot.py search "计算器" output.png [method]
```

## 高级功能

### 处理最小化窗口

该模块可以检测并临时恢复最小化的窗口以进行捕获：

```python
screenshot = WindowScreenshot()
hwnd = 123456  # 窗口句柄

# 检查是否最小化
if screenshot.is_window_minimized(hwnd):
    # 恢复窗口
    screenshot.restore_window(hwnd)
    
    # 捕获
    img = screenshot.screenshot_window(hwnd)
    
    # 再次最小化窗口
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
```

### 获取详细的窗口信息

```python
screenshot = WindowScreenshot()
hwnd = 123456  # 窗口句柄

# 获取窗口信息
window_info = screenshot.get_window_info(hwnd)

# 访问窗口属性
window_rect = window_info.rcWindow
client_rect = window_info.rcClient
window_style = window_info.dwStyle
```

### 检测空白/失败捕获

该模块会自动检测空白或失败的捕获：

```python
screenshot = WindowScreenshot()
hwnd = 123456  # 窗口句柄

img = screenshot.screenshot_window(hwnd)
if img and not screenshot._is_blank_image(img):
    print("捕获成功！")
    img.save("output.png")
else:
    print("捕获失败或返回空白图像。")
```

## 错误处理

该模块包含全面的错误处理，并支持可选的详细日志记录：

```python
try:
    screenshot = WindowScreenshot(verbose=True)
    img = screenshot.screenshot_window(hwnd)
    if img:
        img.save("output.png")
    else:
        print("未能捕获窗口")
except Exception as e:
    print(f"错误: {e}")
```

## 性能注意事项

- `standard` 方法最快但兼容性最差
- `printwindow` 方法在速度和兼容性之间取得了良好的平衡
- `d3d` 和 `composition` 方法较慢但兼容性更强
- 使用 `auto` 可确保最大兼容性，但可能会较慢

## 常见问题及解决方案

1. **空白截图**: 尝试不同的捕获方法，或检查窗口是否最小化。

2. **DirectX 应用程序捕获**: 使用 `method="printwindow"` 或 `method="auto"`。

3. **权限错误**: 确保应用程序有足够的权限访问目标窗口。

4. **找不到窗口**: 检查窗口标题是否正确且可见。某些窗口可能具有隐藏标题。

## 示例

### 捕获多个窗口

```python
from window_screenshot import WindowScreenshot
import os

screenshot = WindowScreenshot()
windows = screenshot.get_all_windows()

# 创建输出目录
os.makedirs("screenshots", exist_ok=True)

# 捕获前 5 个窗口
for i, window in enumerate(windows[:5]):
    hwnd = window["handle"]
    title = window["title"]
    
    # 创建安全文件名
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title[:50]  # 限制长度
    
    filename = f"screenshots/{i+1}_{safe_title}.png"
    
    print(f"正在捕获: {title}")
    img = screenshot.screenshot_window(hwnd)
    
    if img:
        img.save(filename)
        print(f"已保存: {filename}")
    else:
        print(f"未能捕获: {title}")
```

### 周期性监控

```python
from window_screenshot import WindowScreenshot
import time
import os
from datetime import datetime

screenshot = WindowScreenshot()
target_title = "监控目标"
output_dir = "monitoring"

os.makedirs(output_dir, exist_ok=True)

# 监控 1 小时，每 5 分钟捕获一次截图
end_time = time.time() + 3600
while time.time() < end_time:
    windows = screenshot.find_window(target_title)
    
    if windows:
        hwnd = windows[0]["handle"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{timestamp}.png"
        
        img = screenshot.screenshot_window(hwnd)
        if img:
            img.save(filename)
            print(f"已捕获时间: {timestamp}")
    
    # 等待 5 分钟
    time.sleep(300)
```

### 图像处理集成

```python
from window_screenshot import WindowScreenshot
import cv2
import numpy as np

screenshot = WindowScreenshot()
hwnd = 123456  # 窗口句柄

# 捕获窗口
img = screenshot.screenshot_window(hwnd)

if img:
    # 将 PIL 图像转换为 OpenCV 格式
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # 应用图像处理
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    
    # 保存处理后的图像
    cv2.imwrite("edges.png", edges)
```