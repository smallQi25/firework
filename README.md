# Python Fireworks

一个使用 **Python + Pygame** 实现的高级粒子烟花演示。

> `main` 分支为新的 Python 版本；原 EasyX / C++ 版本完整保留在 `master` 分支。

## 效果升级

- 5 种烟花形态：菊花、圆环、垂柳、棕榈、爱心
- 粒子重力、空气阻力、速度衰减与自然下坠
- 发射尾焰、火星闪烁、余烬和烟雾
- 加色混合辉光（Bloom 风格）
- 星空闪烁与城市夜景剪影
- 爆炸轻微镜头震动
- 自动烟花秀与手动交互发射
- 支持窗口缩放和全屏

## 环境

- Python 3.10+
- Pygame 2.5+

## 安装与运行

```bash
pip install -r requirements.txt
python fireworks.py
```

## 操作

| 操作 | 功能 |
| --- | --- |
| 鼠标左键 | 在鼠标位置发射烟花 |
| `Space` | 触发一轮终场烟花 |
| `A` | 开启/关闭自动烟花 |
| `R` | 清空当前烟花粒子 |
| `F11` | 切换全屏 |
| `Esc` | 退出程序 |

## 分支说明

- `main`：Python/Pygame 新版
- `master`：原 C/C++ + EasyX 版本
