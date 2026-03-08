import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// import 'lib-flexible/flexible.js'
import './flexible'
import './styles/theme.css'
import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { baseUrl } from './config/config'
import { useUserStore } from './stores/user'

// 创建应用实例
const app = createApp(App)

// 配置全局属性
app.config.globalProperties.$axios = axios
app.config.globalProperties.$bus = app

// 设置axios默认baseURL，附带 /api/v1
axios.defaults.baseURL = `${baseUrl}/api/v1`

// 创建并使用 pinia
const pinia = createPinia()

// axios 请求拦截：附加 token
axios.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

// 注册Element Plus、路由和pinia
app.use(ElementPlus)
app.use(router)
app.use(pinia)

// 页面加载后从 sessionStorage 恢复状态
app.mount('#app').$nextTick(() => {
  // 恢复用户信息
  const { useUserStore } = require('@/stores/user')
  const userStore = useUserStore()
  userStore.hydrateFromSessionStorage()
  
  // 恢复应用信息
  const { useAppStore } = require('@/stores/app')
  const appStore = useAppStore()
  appStore.hydrateFromSessionStorage()
})
