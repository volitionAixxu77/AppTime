# AppTime · 每日软件使用时长

一个适合计算机协会入门实践的 Windows 桌面项目。自动统计你正在操作的软件，按天保存到本机 SQLite 数据库。

## 可以做什么

- 每秒识别一次前台软件，以进程名称（如 `chrome.exe`）汇总时长。
- 查看当天或任意历史日期的排名、累计时间和占比。
- 连续 5 分钟没有键鼠输入时暂停记录，恢复操作后继续。
- 手动暂停 / 继续、导出当日 CSV，跨午夜自动拆分日期。
- 最小化后继续记录，关闭窗口即退出；重复打开会提示。
- 不联网、不记录窗口标题、网页地址、键盘内容或屏幕图像。

## 快速运行

要求 Windows 10 / 11，Python 3.10 或更新版本，包含 Tcl/Tk（python.org 安装器默认包含）。**无需 pip 安装依赖**。

1. 从 <https://www.python.org/downloads/windows/> 安装 Python，勾选 Add python.exe to PATH。
2. 解压项目，双击 `Start.bat`；或在项目文件夹打开终端执行：

```powershell
python app.py
```

3. 切换到记事本、浏览器等软件操作十几秒，再回来查看统计。
4. 输入 `YYYY-MM-DD` 格式日期后点“查看”；点“导出当日 CSV”保存表格。

如果双击失败，请在终端运行 `py -3 app.py` 查看报错。`No module named tkinter` 表示需要修改 Python 安装并添加 Tcl/Tk；不要用 pip 安装 tkinter。受保护进程可能无法识别，不需要为此以管理员运行。

数据库保存在 `%LOCALAPPDATA%\AppTime\usage.db`，不在项目目录内。关闭程序后可以备份它；删除此文件会清空历史数据。默认不开机启动。如需要，可按 Win+R 输入 `shell:startup`，手动放入 `Start.bat` 的快捷方式；移除快捷方式即可取消。

## 统计口径和限制

这是一种**前台使用时长估计**，不是所有运行中进程的存活时间。浏览器标签页统一算作浏览器；不区分同一个程序的多个窗口。长时间不操作的看视频、阅读也会在 5 分钟后停止计时，前 5 分钟仍计入。当前版本阈值固定。

软件切换的那一秒为避免错归属会舍弃，因此频繁切换可能少计。休眠、采样阻塞超过 5 秒、系统时钟明显跳变时舍弃该段。锁屏或无法读取前台进程时不计时；实际锁屏效果请按下方步骤在自己的电脑验证。按电脑本地日期记账，切换时区不会重写过去数据。

关闭程序后不会记录。当前没有系统托盘、云同步、网站细分或 macOS/Linux 采集支持。端口 47839 只用于阻止重复启动，不启动网络服务。

## 项目结构与基础概念

```text
AppTime/
  app.py                 界面、每秒调度、暂停及导出
  win_tracker.py         调用 Windows API 识别前台进程和空闲时间
  storage.py             数据库及计时规则
  tests/test_storage.py  自动化测试
  Start.bat              Windows 启动入口
  .github/workflows/     Push 后自动运行测试
```

这里的“前端”是 Tkinter 桌面窗口；“后端逻辑”是 Python 的采样和统计；“API”是 Windows 提供的 GetForegroundWindow 等函数；“数据库”是 SQLite 的 usage 表。它们都在本机运行，不需要服务器。每条记录包含日期、软件名和累计秒数，日期与软件名构成唯一键。

数据流：Windows 前台进程 → 每秒采样 → 排除空闲/暂停/异常间隔 → 按日期累加 SQLite → 界面读取和导出。

## 测试与验收

```powershell
python -m unittest discover -s tests -v
```

自动测试覆盖正常计时、跨午夜分账、持久化、排序、空闲、暂停、切换、无进程、休眠间隔和时钟跳变。

建议亲自完成以下验收并记录结果，作为学校项目演示材料：

1. 打开记事本持续操作 20 秒，确认出现 `notepad.exe`，允许数秒采样误差。
2. 切换浏览器持续操作 20 秒，确认两类软件分别累加。
3. 手动暂停，操作记事本 10 秒，确认累计不增加；继续后恢复。
4. 静置超过 5 分钟再操作，确认期间超过阈值部分不计入。
5. 锁屏、睡眠后返回，确认不会把整段离开时间补入。
6. 关闭重开确认历史还在；再次启动确认不会重复计时。
7. 导出 CSV 检查秒数；查询没有使用记录的日期应显示 0。

## Git 与 GitHub：完成一次交付

Git 是本机的版本记录，GitHub 是托管这些记录的平台。交付目录可能已包含初始化的 `.git`；ZIP 为便于分享不包含 `.git`，解压后需要重新初始化。

在项目目录打开 PowerShell。第一次使用 Git 时，请填写自己的身份：

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的 GitHub 邮箱或 noreply 邮箱"
git init -b main
git add .
git commit -m "feat: add daily application usage tracker"
```

如果已存在提交，不需要再次初始化或重复提交；用 `git log --oneline` 查看。到 GitHub 创建名为 `AppTime` 的空仓库，不预先生成 README。然后将下方地址替换为你自己的仓库地址：

```powershell
git remote add origin https://github.com/YOUR_USERNAME/AppTime.git
git push -u origin main
```

按 Git 的登录提示完成认证，不要把密码或 Token 写进代码。若 origin 已存在，先运行 `git remote -v` 检查。网页上看到 README 和代码表示上传成功，Actions 页面可查看测试运行。GitHub Pages 无法运行这个 Windows 桌面采集程序。

修改需求后，按下面的循环练习：

```powershell
python -m unittest discover -s tests -v
git diff
git add .
git commit -m "feat: describe your actual change"
git push
```

## 如何用于协会学习

这份代码是第一个项目的起点，需要你亲自运行、修改和解释，不等于已完成 2～3 个项目。

- 创建项目：理解三个 Python 模块的职责，运行并完成验收。
- 添加功能：让 Coding Agent 增加“最近 7 天统计”，先描述期望结果，再检查实现。
- 修改需求：把空闲阈值改成可配置，并要求重启后保留设置。
- 处理报错：提供完整报错、运行命令、预期行为；修复后重现原操作确认问题消失。
- Git 练习：每完成一个真实小功能提交一次，使用明确的提交说明。
- 后续独立项目：番茄钟、作业截止日期管理器，分别走完需求、开发、调试、提交、交付。

答辩时可以说明：为什么只记录前台窗口、为什么选择 SQLite、如何避免休眠时间误计、数据保存在哪里，以及一次实际需求修改的 diff。

## 官方参考

- Windows 前台窗口 API：<https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow>
- GitHub 上传本地项目：<https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github>
