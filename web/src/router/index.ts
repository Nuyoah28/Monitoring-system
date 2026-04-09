import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import visual from '@/pages/visual.vue'
import login from '@/pages/login.vue'
import home from '@/pages/home.vue'
import simulate from '@/pages/simulate.vue'

const routes = [
  
  {
    path:'/',
    redirect:'/login'
  },
  {
    path:'/visual',
    name:'visual',
    component:visual,
    meta: { requiresAuth: true }
  },
  {
    path:'/agent',
    redirect:'/visual'
  },
  {
    path:'/login',
    name:'login',
    component:login
  },
  {
    path:'/home',
    name:'home',
    component:home,
    meta: { requiresAuth: true }
  },
  {
    path:'/simulate',
    name:'simulate',
    component:simulate
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 添加路由守卫
router.beforeEach((to, from, next) => {
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    // 获取用户 store 实例
    const userStore = useUserStore();
    // 从 sessionStorage 恢复状态（以防页面刷新）
    userStore.hydrateFromSessionStorage();
    
    // 检查是否存在 token 或其他认证标识
    if (!userStore.isAuthenticated) {
      // 如果没有认证信息，重定向到登录页
      next('/login')
    } else {
      // 有认证信息，允许访问
      next()
    }
  } else {
    // 不需要认证的页面，直接访问
    next()
  }
})

export default router
