const { defineConfig } = require('@vue/cli-service')

const trimRightSlash = (value) => String(value || '').replace(/\/+$/, '')
const legacyProxyTarget = trimRightSlash(
  process.env.VUE_APP_DEV_PROXY_TARGET ||
  process.env.VUE_APP_API_BASE_URL ||
  'http://123.56.248.17:10215',
)
const apiProxyTarget = trimRightSlash(process.env.VUE_APP_DEV_API_PROXY_TARGET || legacyProxyTarget)
const algorithmProxyTarget = trimRightSlash(process.env.VUE_APP_DEV_ALGORITHM_PROXY_TARGET || legacyProxyTarget)
const agentProxyTarget = trimRightSlash(process.env.VUE_APP_DEV_AGENT_PROXY_TARGET || legacyProxyTarget)
const mediaProxyTarget = trimRightSlash(process.env.VUE_APP_DEV_MEDIA_PROXY_TARGET || 'http://123.56.248.17:8080')
const wsProxyTarget = trimRightSlash(process.env.VUE_APP_DEV_WS_PROXY_TARGET || 'ws://123.56.248.17')

const proxyWithRewrite = (target) => ({
  target,
  changeOrigin: true,
  pathRewrite: { '^/api-[^/]+': '' },
})

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: './',
  devServer: {
    port: Number(process.env.VUE_APP_DEV_SERVER_PORT || 8081),
    proxy: {
      '/api-backend': proxyWithRewrite(apiProxyTarget),
      '/api-algorithm': proxyWithRewrite(algorithmProxyTarget),
      '/api-agent': proxyWithRewrite(agentProxyTarget),
      '/api-ws': {
        target: wsProxyTarget,
        changeOrigin: true,
        ws: true,
        pathRewrite: { '^/api-ws': '' },
      },
      '/live': {
        target: mediaProxyTarget,
        changeOrigin: true,
      },
      '/video': {
        target: mediaProxyTarget,
        changeOrigin: true,
      },
    },
  },
  configureWebpack: {
    resolve: {
      extensions: ['.js', '.jsx', '.ts', '.tsx', '.vue'],
    },
  },
  chainWebpack: config => {
    config.plugins.delete('eslint')
  },
})
