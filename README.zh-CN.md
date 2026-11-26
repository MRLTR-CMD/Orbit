# Orbit 简体中文试用版

[English](README.md) · [한국어](README.ko.md)

Orbit 把截图、剪贴板历史、启动器、窗口排列、翻译、菜单栏整理、防止休眠和系统监控等功能放在一个原生 macOS 应用中。可以从菜单栏、快捷键或指针旁的环形菜单打开常用工具。

## 在 Intel Mac 上试用

1. 从本仓库的 [Actions](https://github.com/MRLTR-CMD/Orbit/actions/workflows/chinese-trial.yml) 打开最近一次成功的构建，在 **Artifacts** 下载 `Orbit-Chinese-Intel`。
2. 解压下载文件中的 `Orbit-Chinese-Intel.zip`，把 `Orbit 简体中文.app` 放进“应用程序”。
3. 退出正在运行的原版 Orbit，再打开中文版。简体中文系统会自动使用中文，也可以在 **通用 → 语言 → 简体中文** 选择后点按“重新打开”。
4. 可在设置搜索框输入“窗口管理”“剪贴板”或“菜单栏”。

试用版使用 `~/Library/Application Support/Orbit Chinese` 和独立的应用标识。切回原版前，从试用版菜单栏选择“退出 Orbit”。试用版里的普通压缩与解压可以直接从应用操作。访达服务、快速查看、风扇和电池助手以及 Tavi 集成需要通过对应的签名构建验证。

## 本地构建

使用完整的 Xcode 26 和 Python 3。在仓库根目录运行以下命令，生成 Intel 试用包 `dist/Orbit-Chinese-Intel.zip`。

```bash
bash tools/build-chinese-trial.sh
```

中文源词表位于 `tools/i18n/zh-Hans*.json`。更改后运行 `python3 tools/i18n.py`，同时提交源词表和生成的字符串目录。系统权限说明、访达服务名称和快速查看使用各自的 `.strings` 资源。

## 同步上游

在 Fork 的 `main` 页面点击 **Sync fork**。然后把新的 `main` 合进 `codex/zh-hans`，确认中文界面后推送该分支。也可以直接从本地配置好的 `upstream` 取回最新提交。

```bash
git fetch upstream main
git switch codex/zh-hans
git merge upstream/main
python3 tools/i18n.py
python3 tools/regressions/settings-index-tests.py
```

若生成的字符串目录发生合并冲突，先解决源词表和应用代码的冲突，以上游字符串目录为起点重新生成，再提交结果。试用包从 Fork 的 Actions 获取。

## 许可证

Orbit 由 [3x-haust](https://github.com/3x-haust/Orbit) 开发，使用 [MIT 许可证](LICENSE)。
