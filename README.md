# automatch
全自动匹配工具-半自动远星杯

### dev
```cmd
  pip install -r requirements.txt
```

```commandline
  python app/main.py
```

### build
使用pyinstaller
```cmd
  pip install pyinstaller
```

正常build
```cmd
  pyinstaller main.py
```
独立exe build，便于分发
```cmd
  pyinstaller --onefile main.py
```