import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user', () => {
  const phone = ref('');
  const username = ref('');
  const token = ref('');
  const userId = ref<number>(0);

  // 计算属性
  const isAuthenticated = computed(() => !!token.value);
  const getUserInfo = computed(() => ({
    phone: phone.value,
    userId: userId.value,
    username: username.value,
    token: token.value,
  }));

  // 操作方法
  function setUserInfo(phoneParam: string, usernameParam: string, userIdParam:number, tokenParam: string) {
    phone.value = phoneParam;
    userId.value = userIdParam;
    username.value = usernameParam;
    token.value = tokenParam;
  }

  function clearUserInfo() {
    phone.value = '';
    username.value = '';
    token.value = '';
    userId.value = 0;
  }

  // 从 sessionStorage 同步数据到 store (用于页面刷新后恢复状态)
  function hydrateFromSessionStorage() {
    const phoneValue = sessionStorage.getItem('phone');
    const usernameValue = sessionStorage.getItem('username');
    const tokenValue = sessionStorage.getItem('token');
    const userIdValue = sessionStorage.getItem('userId');

    if (phoneValue) phone.value = phoneValue;
    if (usernameValue) username.value = usernameValue;
    if (userIdValue) userId.value = Number(userIdValue);
    if (tokenValue) token.value = tokenValue;
  }

  // 将数据同步到 sessionStorage
  function syncToSessionStorage() {
    if (phone.value) sessionStorage.setItem('phone', phone.value);
    if (username.value) sessionStorage.setItem('username', username.value);
    if (token.value) sessionStorage.setItem('token', token.value);
    if (userId.value) sessionStorage.setItem('userId', userId.value.toString());
  }

  // 清除 sessionStorage 中的数据
  function clearSessionStorage() {
    sessionStorage.removeItem('phone');
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('userId');
  }

  return {
    // 状态
    phone,
    username,
    token,
    userId,
    // 计算属性
    isAuthenticated,
    getUserInfo,

    // 操作方法
    setUserInfo,
    clearUserInfo,
    hydrateFromSessionStorage,
    syncToSessionStorage,
    clearSessionStorage,
  };
});