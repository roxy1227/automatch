from window_screenshot import WindowScreenshot

# 创建实例并启用详细日志记录
screenshot = WindowScreenshot(verbose=True)

hwnd = 2034014

img_auto = screenshot.screenshot_window(hwnd)


    # 保存图像
if img_auto:
    img_auto.save("calculator.png")