# Python Fireworks

一个使用 **Python + pygame-ce** 实现的高级粒子烟花演示，同时支持桌面和手机浏览器。

> `main` 分支为 Python 新版；原 EasyX / C++ 版本保留在 `master` 分支。

## 现在支持手机

手机端不是把 Python 改成 JavaScript，而是通过 **Pygbag + WebAssembly** 让 Python/Pygame 代码直接运行在浏览器中。

手机操作：

- 点击 / 触摸天空：在触摸位置发射烟花
- `FINALE`：触发一轮大型烟花
- `AUTO ON/OFF`：开启或关闭自动烟花
- 建议手机横屏使用，视野更好
- Android Chrome / Edge、iPhone Safari 均可使用现代浏览器访问

程序同时做了移动端性能优化：Web 端会自动降低部分粒子数量并限制最大粒子数，在保持效果的同时降低手机 GPU / CPU 压力。

## 烟花效果

- 菊花、圆环、垂柳、棕榈、爱心 5 种形态
- 粒子重力、空气阻力、速度衰减与自然下坠
- 发射尾焰、闪烁火星、余烬与烟雾
- 加色混合辉光
- 星空和城市夜景
- 爆炸镜头震动
- 自动烟花秀
- 鼠标 + 触摸双输入
- 桌面窗口缩放 / 全屏

## 桌面运行

推荐 Python 3.10+。

```bash
pip install -r requirements.txt
python main.py
```

桌面快捷键：

| 操作 | 功能 |
| --- | --- |
| 鼠标左键 | 发射烟花 |
| `Space` | 终场烟花 |
| `A` | 自动烟花开关 |
| `R` | 清空当前粒子 |
| `F11` | 全屏 |
| `Esc` | 退出 |

## 本地测试手机版 / Web 版

安装 Web 构建依赖：

```bash
pip install -r requirements-web.txt
```

启动 Pygbag：

```bash
python -m pygbag --ume_block 0 .
```

然后在浏览器打开终端显示的本地地址。

Pygbag 要求 Web 项目存在 `main.py`，并且主循环需要支持 async；本项目已经按这个方式处理好了。

## GitHub Pages

仓库已经包含：

```text
.github/workflows/pages.yml
```

每次向 `main` 分支提交代码时，GitHub Actions 会自动：

1. 安装 pygame-ce 和 pygbag
2. 将 Python 烟花构建为 WebAssembly 网页
3. 上传 GitHub Pages 构建产物
4. 部署手机版网页

如果仓库第一次使用 Pages，请在 GitHub 仓库中打开：

`Settings -> Pages -> Build and deployment -> Source -> GitHub Actions`

完成后，网页通常会使用：

`https://smallqi25.github.io/firework/`

## 分支

- `main`：Python / pygame-ce，桌面 + 手机 Web 版
- `master`：原 C/C++ + EasyX 版本
