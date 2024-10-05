# PromptBall
PromptBall 是一款轻量级的悬浮工具，旨在为用户提供快速访问和管理常用文本片段的便捷方式。
## 环境
只需要常规的python环境，建议3.7以上。
```bash
pip install pyinstaller
pip install PyQt5
```
其他的库缺什么安什么就ok
## 打包
```bash
pyinstaller --noconsole --onefile --icon=pb.ico --name=PromptBall --hidden-import=PyQt5.sip floating_ball.py
```
