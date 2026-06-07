# 投资逻辑和知识

个人投资体系与知识库，基于 [VitePress](https://vitepress.dev/zh/) 搭建。

## 快速开始

```bash
npm install          # 安装依赖
npm run docs:dev     # 本地预览（默认 http://localhost:5173）
npm run docs:build   # 构建静态站点到 docs/.vitepress/dist
npm run docs:preview # 预览构建产物
```

## 目录结构

```
docs/
├─ .vitepress/
│  └─ config.mts      # 站点配置：导航、侧边栏、搜索等
├─ public/            # 静态资源（图片等）
├─ index.md           # 首页
├─ framework/         # 投资框架
├─ valuation/         # 估值方法
├─ cases/             # 案例复盘
└─ checklists/        # 清单工具
```

## 新增内容

1. 在对应栏目目录下新建 `.md` 文件。
2. 到 `docs/.vitepress/config.mts` 的 `sidebar` 里登记链接。
3. `npm run docs:dev` 实时预览。

## 部署到 GitHub Pages

已内置 `.github/workflows/deploy.yml`，推送到 `main` 即自动构建并发布。首次启用：

1. 在 GitHub 新建仓库，把本项目推上去：
   ```bash
   git remote add origin git@github.com:<用户名>/<仓库名>.git
   git push -u origin main
   ```
2. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。
3. 之后每次 `git push` 到 `main` 会自动部署，地址为 `https://<用户名>.github.io/<仓库名>/`。

> 工作流会自动把 VitePress 的 `base` 设为 `/<仓库名>/`。若改用**自定义域名**或**用户主页仓库**（`<用户名>.github.io`），删掉工作流里 `DOCS_BASE` 那一行即可（`base` 回落为 `/`）。
