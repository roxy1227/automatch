from tools.window_screenshot import WindowScreenshot

if __name__ == '__main__':
    window_screen = WindowScreenshot()

    windows = window_screen.get_all_windows()
    print(windows)
    window_screen.get_formatted_windows()