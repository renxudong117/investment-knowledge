import { defineConfig } from 'vitepress'

// VitePress 配置文档：https://vitepress.dev/zh/reference/site-config
export default defineConfig({
  lang: 'zh-CN',
  title: '投资逻辑和知识',
  description: '个人投资体系、估值方法与案例复盘的知识库',
  lastUpdated: true,
  cleanUrls: true,

  // 部署到 GitHub Pages 项目页时由 CI 注入 /<仓库名>/；本地与根路径部署回落为 '/'
  base: process.env.DOCS_BASE || '/',

  themeConfig: {
    // 顶部导航
    nav: [
      { text: '首页', link: '/' },
      { text: '投资框架', link: '/framework/' },
      { text: '估值方法', link: '/valuation/' },
      { text: '案例复盘', link: '/cases/' },
      { text: '清单工具', link: '/checklists/' }
    ],

    // 侧边栏：按栏目分组，后续新增 .md 文件时在这里登记
    sidebar: {
      '/framework/': [
        {
          text: '投资框架',
          items: [{ text: '概览', link: '/framework/' }]
        }
      ],
      '/valuation/': [
        {
          text: '估值方法',
          items: [{ text: '概览', link: '/valuation/' }]
        }
      ],
      '/cases/': [
        {
          text: '案例复盘',
          items: [
            { text: '概览', link: '/cases/' },
            { text: '示例案例（模板）', link: '/cases/example' }
          ]
        }
      ],
      '/checklists/': [
        {
          text: '清单工具',
          items: [{ text: '概览', link: '/checklists/' }]
        }
      ]
    },

    // 本地全文搜索（无需外部服务）
    search: { provider: 'local' },

    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdatedText: '最后更新于',
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    returnToTopLabel: '返回顶部',
    sidebarMenuLabel: '菜单',
    langMenuLabel: '切换语言'
  }
})
