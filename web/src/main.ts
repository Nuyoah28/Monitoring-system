import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// import 'lib-flexible/flexible.js'
import './flexible'
import axios from 'axios'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import {baseUrl} from './config/config'

// 创建应用实例
const app = createApp(App)

// 配置全局属性
app.config.globalProperties.$axios = axios
app.config.globalProperties.$bus = app

// 设置axios默认baseURL
axios.defaults.baseURL = baseUrl;

// 创建并使用 pinia
const pinia = createPinia()

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