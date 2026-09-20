---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 3492397679226d6505949fd36ce12be5_a5e89ffbb40a11f1ba1b525400638852
    ReservedCode1: iOWnNqzEKLD4mI50e229Anrn+dB5K9YmYQZ/M0/SQ2WIMk5Bztl+GhyN0SGDj3POto6BWi6MuiKaJOS2h1wP2bCpkB+G3ImHoJ1srCmSTKx/p/m7vXRzEM7EblOBTZxqsxTTe93aw+6i9INaRTVB4ah7CqjNUVaaMh2HXzhrmEkA9gX1bTgOax1LOk4=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 3492397679226d6505949fd36ce12be5_a5e89ffbb40a11f1ba1b525400638852
    ReservedCode2: iOWnNqzEKLD4mI50e229Anrn+dB5K9YmYQZ/M0/SQ2WIMk5Bztl+GhyN0SGDj3POto6BWi6MuiKaJOS2h1wP2bCpkB+G3ImHoJ1srCmSTKx/p/m7vXRzEM7EblOBTZxqsxTTe93aw+6i9INaRTVB4ah7CqjNUVaaMh2HXzhrmEkA9gX1bTgOax1LOk4=
---

# WS-4 公开排行榜前端（Phase 1 / 1.3，静态占位版）

本目录是 WS-4 Phase 1 子任务 **1.3** 的产物：一个面向公众的只读排行榜页面。
当前为**静态占位**实现——不包含任何写操作，真实发布仍须走
`scoring.leaderboard.save()` 门禁链。

## 文件

| 文件 | 说明 |
|---|---|
| `index.html` | 页面结构：排序/筛选控件 + 榜单表格 |
| `style.css` | 响应式样式（窄屏控件折行、表格横向滚动） |
| `app.js` | 数据加载（接口占位 + 本地回退）、排序、筛选、渲染 |
| `README.md` | 本说明 |

## 功能

- 排序指标：`bander_roi / bander_full / roi_tm_auc / cnr_mean / cho_auc_mean /
  npwe_mean / psnr_db / ssim`，方向可切换（默认 `bander_roi` 降序，trap 垫底）
- 筛选：`metric / vendor / dose / year`（year 从 `submitted_at` 提取）
- 只读：页面不调用任何写接口

## 数据接口（占位）

`app.js` 中 `API_SOURCES` 依序尝试：

1. `/api/leaderboard` —— **正式接入点（占位）**，当前不存在，返回 404 即跳过。
2. `../scoring/data/leaderboard.json` —— 本地开发回退，即仓库现成的榜单文件。

正式接入时：

- 将 `/api/leaderboard` 换成 scoring 服务实际端点（建议返回
  `{ task, entries }`，`entries` 与 `scoring/data/leaderboard.json` 同构）。
- 若需 CORS，服务端放行同源或配置允许来源。
- 若接口分页，将 `loadBoard()` 改为分页拉取并保留 `entries` 合并逻辑。

## 本地预览

在仓库根目录起静态服务后访问 `/web/`：

```powershell
cd D:\ZHY\low_dose_CT-heyang\WS-4_leaderboard
python -m http.server 8000 --bind 127.0.0.1
# 浏览器打开 http://127.0.0.1:8000/web/
```

直接用 `file://` 打开 `web/index.html` 时，浏览器同源策略会阻止 fetch 本地
JSON，此时页面会显示"没有可用的排行榜数据源"，属预期行为；请使用上面的静态服务。

## 红线

- 不 commit / push（由主仓统一管控）。
- 不修改 `scoring/data/leaderboard.json` 等红线字段。
- 本页面是**展示层**，任何发布动作都必须经过 `leaderboard.save()` 门禁链。
*（内容由AI生成，仅供参考）*
