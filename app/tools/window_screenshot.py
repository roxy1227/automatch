"""
WindowScreenshot 模块
=======================
一个用于捕获 Windows 应用程序屏幕截图的 Python 模块，特别支持 DirectX 和其他难以捕获的窗口。
该模块提供了多种捕获窗口屏幕截图的方法，包括标准 GDI、PrintWindow API 以及针对 DirectX 应用程序的替代方法。

功能：
- 按标题或进程名称查找窗口
- 多种捕获方法，具有自动回退机制
- 支持最小化的窗口
- 检测空白/失败的捕获
- 详细的窗口信息访问

依赖项：
- ctypes
- numpy
- opencv-python (cv2)
- pywin32 (win32gui, win32ui, win32con, win32process)
- Pillow (PIL)
"""
import ctypes
from ctypes import wintypes, windll, byref, c_void_p
import time
import numpy as np
import cv2
import win32gui
import win32ui
import win32con
import win32process
from PIL import Image
import os
import sys
from typing import List, Tuple, Dict, Optional, Union, Any

# Windows API 常量
PW_CLIENTONLY = 1
PW_RENDERFULLCONTENT = 2

# Windows API 结构体
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

class WINDOWINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcWindow", RECT),
        ("rcClient", RECT),
        ("dwStyle", wintypes.DWORD),
        ("dwExStyle", wintypes.DWORD),
        ("dwWindowStatus", wintypes.DWORD),
        ("cxWindowBorders", wintypes.WORD),
        ("cyWindowBorders", wintypes.WORD),
        ("atomWindowType", wintypes.ATOM),
        ("wCreatorVersion", wintypes.WORD)
    ]

class WindowScreenshot:
    """
    用于捕获 Windows 应用程序屏幕截图的类。
    提供多种方法捕获窗口内容，特别处理 DirectX 和其他难以捕获的窗口。
    """
    def __init__(self, verbose: bool = False):
        """
        使用 Windows API 库初始化 WindowScreenshot。
        参数：
            verbose: 如果为 True，在捕获尝试期间打印详细日志
        """
        self.user32 = ctypes.WinDLL('user32')
        self.gdi32 = ctypes.WinDLL('gdi32')
        self.verbose = verbose
        # 定义 user32.dll 中的 PrintWindow 函数
        self.user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
        self.user32.PrintWindow.restype = wintypes.BOOL

    def log(self, message: str) -> None:
        """如果启用了详细模式，则打印日志消息。"""
        if self.verbose:
            print(message)

    def get_window_handles_by_title(self, title_substring: str) -> List[Tuple[int, str]]:
        """
        获取标题中包含子字符串的窗口句柄。
        参数：
            title_substring: 要在窗口标题中搜索的字符串
        返回：
            匹配窗口的元组列表 (hwnd, window_title)
        """
        result = []
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title_substring.lower() in window_title.lower():
                    result.append((hwnd, window_title))
            return True
        win32gui.EnumWindows(callback, None)
        return result

    def get_window_handles_by_process_name(self, process_name: str = "") -> List[Tuple[int, str, int]]:
        """
        根据进程名称获取窗口句柄。
        参数：
            process_name: 要过滤的进程名称（空字符串表示所有进程）
        返回：
            匹配窗口的元组列表 (hwnd, window_title, process_id)
        """
        result = []
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                    if process_id:
                        window_title = win32gui.GetWindowText(hwnd)
                        if window_title:  # 仅包括有标题的窗口
                            if not process_name or process_name.lower() in window_title.lower():
                                result.append((hwnd, window_title, process_id))
                except Exception:
                    pass
            return True
        win32gui.EnumWindows(callback, None)
        return result

    def get_window_info(self, hwnd: int) -> WINDOWINFO:
        """
        获取有关窗口的详细信息。
        参数：
            hwnd: 窗口句柄
        返回：
            包含窗口详细信息的 WINDOWINFO 结构体
        """
        wi = WINDOWINFO()
        wi.cbSize = ctypes.sizeof(WINDOWINFO)
        self.user32.GetWindowInfo(hwnd, ctypes.byref(wi))
        return wi

    def is_window_minimized(self, hwnd: int) -> bool:
        """
        检查窗口是否已最小化。
        参数：
            hwnd: 窗口句柄
        返回：
            如果窗口已最小化则返回 True，否则返回 False
        """
        return self.user32.IsIconic(hwnd)

    def restore_window(self, hwnd: int) -> None:
        """
        恢复最小化的窗口。
        参数：
            hwnd: 窗口句柄
        """
        self.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)  # 给窗口一些时间恢复

    def capture_standard(self, hwnd: int) -> Optional[Image.Image]:
        """
        使用标准 Windows GDI 方法捕获窗口。
        参数：
            hwnd: 窗口句柄
        返回：
            窗口内容的 PIL 图像，如果捕获失败则返回 None
        """
        try:
            # 获取窗口尺寸
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            # 创建设备上下文
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            # 创建位图
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            # 捕获窗口内容
            result = save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            # 将位图转换为 PIL 图像
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return img if result else None
        except Exception as e:
            self.log(f"标准捕获失败: {e}")
            return None

    def capture_with_print_window(self, hwnd: int) -> Optional[Image.Image]:
        """
        使用 PrintWindow API 捕获窗口内容（对 DirectX 更友好）。
        参数：
            hwnd: 窗口句柄
        返回：
            窗口内容的 PIL 图像，如果捕获失败则返回 None
        """
        try:
            # 获取窗口尺寸
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            # 创建设备上下文
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            # 创建位图
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            # 使用 PrintWindow 捕获 - 直接通过 ctypes 使用 user32.dll
            result = self.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)
            # 将位图转换为 PIL 图像
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return img if result else None
        except Exception as e:
            self.log(f"PrintWindow 捕获失败: {e}")
            return None

    def capture_with_d3d(self, hwnd: int) -> Optional[Image.Image]:
        """
        使用 WM_PRINT 消息捕获 DirectX 窗口的替代方法。
        这可能适用于某些 PrintWindow 失败的 DirectX 应用程序。
        参数：
            hwnd: 窗口句柄
        返回：
            窗口内容的 PIL 图像，如果捕获失败则返回 None
        """
        try:
            # 获取窗口尺寸
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            # 创建设备上下文
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            # 创建位图
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            # 尝试使用 WM_PRINT/WM_PRINTCLIENT 消息
            WM_PRINT = 0x0317
            PRF_CLIENT = 0x00000004
            PRF_CHILDREN = 0x00000010
            PRF_NON_CLIENT = 0x00000002
            self.user32.SendMessageW(
                hwnd,
                WM_PRINT,
                save_dc.GetSafeHdc(),
                PRF_CLIENT | PRF_CHILDREN | PRF_NON_CLIENT
            )
            # 将位图转换为 PIL 图像
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            # 清理资源
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return img
        except Exception as e:
            self.log(f"D3D 捕获方法失败: {e}")
            return None

    def capture_with_composition(self, hwnd: int) -> Optional[Image.Image]:
        """
        尝试使用 DWM 合成捕获 DirectX 内容。
        这是一种替代方法，可能适用于其他方法失败的某些窗口。
        参数：
            hwnd: 窗口句柄
        返回：
            窗口内容的 PIL 图像，如果捕获失败则返回 None
        """
        try:
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            # 尝试强制窗口可见并捕获
            # 保存当前窗口状态
            was_iconic = self.is_window_minimized(hwnd)
            was_visible = win32gui.IsWindowVisible(hwnd)
            # 强制窗口可见并置于前台
            if was_iconic:
                self.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
            # 将窗口置于前台（可能有助于某些 DirectX 应用程序）
            self.user32.SetForegroundWindow(hwnd)
            time.sleep(0.1)  # 给窗口一些时间渲染
            # 首先使用标准方法捕获
            img = self.capture_standard(hwnd)
            # 如果失败，尝试 PrintWindow
            if img is None or self._is_blank_image(img):
                img = self.capture_with_print_window(hwnd)
            # 恢复窗口状态
            if was_iconic:
                self.user32.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return img
        except Exception as e:
            self.log(f"合成捕获失败: {e}")
            return None

    def screenshot_window(self, hwnd: int, save_path: Optional[str] = None,
                          method: str = "auto") -> Optional[Image.Image]:
        """
        使用指定方法捕获窗口的屏幕截图。
        参数：
            hwnd: 窗口句柄
            save_path: 保存屏幕截图的路径（如果为 None，则不保存直接返回图像）
            method: 捕获方法 ("standard", "printwindow", "d3d", "composition", 或 "auto")
        返回：
            PIL 图像对象，如果捕获失败则返回 None
        异常：
            ValueError: 如果指定了未知的捕获方法
        """
        # 检查窗口是否最小化
        was_minimized = self.is_window_minimized(hwnd)
        if was_minimized:
            self.restore_window(hwnd)
        # 尝试使用指定方法捕获
        img = None
        if method == "auto":
            # 按复杂性/兼容性顺序尝试方法
            methods = ["standard", "printwindow", "d3d", "composition"]
            for m in methods:
                self.log(f"尝试 {m} 方法...")
                if m == "standard":
                    img = self.capture_standard(hwnd)
                elif m == "printwindow":
                    img = self.capture_with_print_window(hwnd)
                elif m == "d3d":
                    img = self.capture_with_d3d(hwnd)
                elif m == "composition":
                    img = self.capture_with_composition(hwnd)
                # 如果获得非空白图像，则退出循环
                if img is not None and not self._is_blank_image(img):
                    self.log(f"{m} 方法成功！")
                    break
                else:
                    self.log(f"{m} 方法失败或返回空白图像。")
        elif method == "standard":
            img = self.capture_standard(hwnd)
        elif method == "printwindow":
            img = self.capture_with_print_window(hwnd)
        elif method == "d3d":
            img = self.capture_with_d3d(hwnd)
        elif method == "composition":
            img = self.capture_with_composition(hwnd)
        else:
            raise ValueError(f"未知的捕获方法: {method}")
        # 如果之前是最小化状态，恢复到该状态
        if was_minimized:
            self.user32.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        # 如果提供了路径，则保存图像
        if img is not None and save_path:
            img.save(save_path)
            self.log(f"图像已保存到 {save_path}")
        return img

    def _is_blank_image(self, img: Image.Image, threshold: float = 0.95) -> bool:
        """
        检查图像是否大部分为空白（单一颜色）。
        参数：
            img: 要检查的 PIL 图像
            threshold: 判断图像是否为空白的阈值
        返回：
            如果检测到图像为空白则返回 True，否则返回 False
        """
        # 转换为 numpy 数组并检查方差
        img_array = np.array(img)
        # 检查大多数像素是否为相同颜色
        if img_array.size == 0:
            return True
        # 计算每个通道的方差
        r_var = np.var(img_array[:, :, 0])
        g_var = np.var(img_array[:, :, 1])
        b_var = np.var(img_array[:, :, 2])
        # 如果方差非常低，则图像可能是空白的
        return (r_var + g_var + b_var) / 3 < 100

    def get_all_windows(self) -> List[Dict[str, Any]]:
        """
        获取所有可见窗口的信息。
        返回：
            每个窗口信息的字典列表
        """
        windows = self.get_window_handles_by_process_name("")
        result = []
        for hwnd, title, pid in windows:
            if title:  # 仅包括有标题的窗口
                result.append({
                    "handle": hwnd,
                    "title": title,
                    "process_id": pid
                })
        return result

    def find_window(self, title_substring: str) -> List[Dict[str, Any]]:
        """
        查找与标题子字符串匹配的窗口。
        参数：
            title_substring: 要在窗口标题中搜索的子字符串
        返回：
            匹配窗口信息的字典列表
        """
        windows = self.get_window_handles_by_title(title_substring)
        result = []
        for hwnd, title in windows:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            result.append({
                "handle": hwnd,
                "title": title,
                "process_id": pid
            })
        return result

# 辅助函数
def list_all_windows(verbose: bool = True) -> List[Dict[str, Any]]:
    """
    列出系统上的所有可见窗口。
    参数：
        verbose: 如果为 True，则将窗口信息打印到控制台
    返回：
        包含窗口信息的字典列表
    """
    screenshot = WindowScreenshot(verbose=False)
    windows = screenshot.get_all_windows()
    if verbose:
        print("\n可用窗口:")
        print("-" * 80)
        print(f"{'句柄':<12} | {'进程 ID':<12} | {'窗口标题'}")
        print("-" * 80)
        for window in windows:
            print(f"{window['handle']:<12} | {window['process_id']:<12} | {window['title']}")
    return windows

def find_windows(title_substring: str, verbose: bool = True) -> List[Dict[str, Any]]:
    """
    查找与标题子字符串匹配的窗口。
    参数：
        title_substring: 要在窗口标题中搜索的子字符串
        verbose: 如果为 True，则将匹配的窗口信息打印到控制台
    返回：
        包含匹配窗口信息的字典列表
    """
    screenshot = WindowScreenshot(verbose=False)
    windows = screenshot.find_window(title_substring)
    if verbose:
        if not windows:
            print(f"未找到与 '{title_substring}' 匹配的窗口")
        else:
            print(f"\n找到 {len(windows)} 个匹配的窗口:")
            print("-" * 80)
            print(f"{'句柄':<12} | {'进程 ID':<12} | {'窗口标题'}")
            print("-" * 80)
            for window in windows:
                print(f"{window['handle']:<12} | {window['process_id']:<12} | {window['title']}")
    return windows

def capture_window(hwnd: int, save_path: Optional[str] = None,
                   method: str = "auto", verbose: bool = False) -> Optional[Image.Image]:
    """
    捕获窗口的屏幕截图。
    参数：
        hwnd: 窗口句柄
        save_path: 保存屏幕截图的路径（如果为 None，则不保存直接返回图像）
        method: 捕获方法 ("standard", "printwindow", "d3d", "composition", 或 "auto")
        verbose: 如果为 True，则在捕获期间打印详细日志
    返回：
        PIL 图像对象，如果捕获失败则返回 None
    """
    screenshot = WindowScreenshot(verbose=verbose)
    return screenshot.screenshot_window(hwnd, save_path, method)

def capture_window_by_title(title_substring: str, save_path: Optional[str] = None,
                            method: str = "auto", verbose: bool = False) -> Optional[Image.Image]:
    """
    按标题子字符串查找并捕获窗口。
    参数：
        title_substring: 要在窗口标题中搜索的子字符串
        save_path: 保存屏幕截图的路径（如果为 None，则不保存直接返回图像）
        method: 捕获方法 ("standard", "printwindow", "d3d", "composition", 或 "auto")
        verbose: 如果为 True，则在捕获期间打印详细日志
    返回：
        PIL 图像对象，如果未找到窗口或捕获失败则返回 None
    """
    screenshot = WindowScreenshot(verbose=verbose)
    windows = screenshot.find_window(title_substring)
    if not windows:
        if verbose:
            print(f"未找到与 '{title_substring}' 匹配的窗口")
        return None
    if verbose:
        print(f"正在捕获第一个匹配的窗口: {windows[0]['title']} (句柄: {windows[0]['handle']})")
    return screenshot.screenshot_window(windows[0]['handle'], save_path, method)

# 命令行接口（保留以保持向后兼容性）
def main():
    if len(sys.argv) < 2:
        print("\n使用示例:")
        print("  python window_screenshot.py list")
        print("  python window_screenshot.py capture <window_handle> [output_filename.png] [method]")
        print("  python window_screenshot.py search \"window title substring\" [output_filename.png] [method]")
        print("\n方法: standard, printwindow, d3d, composition, auto (默认)")
        return
    command = sys.argv[1].lower()
    screenshot = WindowScreenshot(verbose=True)
    if command == "list":
        list_all_windows()
    elif command == "capture" and len(sys.argv) >= 3:
        try:
            hwnd = int(sys.argv[2])
            output_path = sys.argv[3] if len(sys.argv) > 3 else f"window_{hwnd}.png"
            method = sys.argv[4] if len(sys.argv) > 4 else "auto"
            print(f"正在捕获窗口 {hwnd}...")
            img = capture_window(hwnd, output_path, method, verbose=True)
            if img:
                print(f"屏幕截图已保存到 {output_path}")
            else:
                print("捕获窗口失败。")
        except ValueError:
            print("错误: 窗口句柄必须是整数。")
    elif command == "search" and len(sys.argv) >= 3:
        search_term = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        method = sys.argv[4] if len(sys.argv) > 4 else "auto"
        windows = find_windows(search_term)
        if not windows:
            return
        if len(windows) == 1 and output_path:
            hwnd = windows[0]['handle']
            print(f"正在捕获唯一的匹配窗口: {windows[0]['title']} ({hwnd})...")
            img = capture_window(hwnd, output_path, method, verbose=True)
            if img:
                print(f"屏幕截图已保存到 {output_path}")
            else:
                print("捕获窗口失败。")
        elif output_path:
            print("请使用 'capture' 命令并指定窗口句柄来捕获特定窗口。")

if __name__ == "__main__":
    main()