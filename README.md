# 不玩游戏看剧情 · 视频追剧指南

**在线阅读：<https://cdyforever.github.io/fgo-story-guide/>**

为「剧情本身就是卖点」的游戏整理纯视频观影路线：章节梗概 + 解说安利 + 名场面 + 一键直达 B 站对应分 P。所有视频数据通过 Bilibili 开放接口实时校验。

## 收录游戏

| 游戏 | 页面 | 状态 |
|---|---|---|
| Fate / Grand Order | [fgo.html](https://cdyforever.github.io/fgo-story-guide/fgo.html) | 已上线（第一部~奏章IV） |
| 原神 | [genshin.html](https://cdyforever.github.io/fgo-story-guide/genshin.html) | 第一期：魔神任务~7.0至冬 + 大型活动 + 世界观考据区；第二期（传说/世界任务）筹备中 |
| 崩坏：星穹铁道 | — | 筹备中 |

每个游戏一张独立页面，数据互不干扰；`index.html` 为门户。顶部导航在各页面间切换。

## 追更机制

游戏剧情持续更新，本站配套半自动追更流水线（`tools/update.py`）：

1. 每个游戏页内嵌 `watch-meta` 块，登记需要监控的 B 站合集与已收录分 P 数；
2. `python tools/update.py` 重新请求 API，报告新增分 P 标题（如 7.1 新幕）；
3. `python tools/update.py --fix` 自动在页面插入带直达链接的占位卡片并更新登记数；
4. 站长补写梗概后 `git push`，GitHub Pages 自动重建。

## 本地离线使用

直接双击 `fgo.html` / `genshin.html` 也可以看（封面图依赖 no-referrer 直连）。如遇 B 站图床防盗链拦截，双击 `启动FGO剧情指南.bat`（需 Node.js）：本地服务器自动打开指南，并把所有封面图改走本地代理（补 Referer + 内存缓存）。


## 内容管线（面向维护者）

剧情文案以 Markdown 存放于 `content/*.md`，`python tools/build.py` 构建为同名静态HTML：

- front-matter 定义页面元信息（hero/统计/片源/导航）；
- `## 章节 {id, spoiler:light|mid|heavy}` / `### 幕 {act, ver, p:[起,止]}` 声明结构与剧透分级；
- `[[按钮|分P号]]` 自动生成直达合集分P的按钮；
- `::: reveal`（红级剧透遮挡）、`::: personas`、`::: cards2`、`::: pbtns`、`::: note` 等块级指令。

阅读器交互（assets/reader.js）：每幕「已看」勾选存浏览器本地并汇总为进度条；红级内容默认模糊、点击显影；右上角全局「展开全部剧透」开关。改文案 = 改 Markdown，git diff 友好。

## 数据与致谢

- 视频数据（标题/分P/播放量/封面）来自 Bilibili 开放接口，抓取于 2026-08-29
- FGO 主要资源：克罗斯ChrisWayne、魔法立香、棗黑子Ms、緋雨閑丸 等
- 原神主要资源：骚橙丶、星月银、Muc虚空之翼、低配芙兰达（指定优先）+ 你的影月月、天空岛的愚者、四维告白、阿宅不宅a 等头部UP
- 设定查询：[Mooncell](https://fgo.wiki)（FGO）· [BWIKI](https://wiki.biligame.com/ys/)（原神）
- 视频版权归原作者与各 UP 主所有
