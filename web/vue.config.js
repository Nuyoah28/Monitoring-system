const { defineConfig } = require('@vue/cli-service')

const trimRightSlash = (value) => String(value || '').replace(/\/+$/, '')
const proxyTarget = trimRightSlash(
  process.env.VUE_APP_DEV_PROXY_TARGET ||
  process.env.VUE_APP_API_BASE_URL ||
  'http://123.56.248.17:10215',
)

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: './',
  devServer: {
    port: Number(process.env.VUE_APP_DEV_SERVER_PORT || 8081),
    proxy: {
      '/api': {
        target: proxyTarget,
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
