<template>
    <div class="header1">
      <img src="../../public/assets/logo1.png" alt="logo" class="img1">
      <img src="../../public/assets/t01c209d217482e57de.jpg" alt="avatar" class="img2"
       @click="goHome">
      
      <h1>智安守护</h1>
      <div ref="showTime" class="showTime">{{ nowtime }}</div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue'
  import { useRouter } from 'vue-router'
  const nowtime = ref<string>('')
  const router = useRouter()
  const goHome = (): void => {
    router.push('/home')
  }
  let timer: ReturnType<typeof setInterval> | null = null // 定时器
  
  const updateTime = (): void => {
      const dt = new Date();
      const y = dt.getFullYear();
      const mt = dt.getMonth() + 1;
      const day = dt.getDate();
      const h = dt.getHours(); //获取时
      const m = dt.getMinutes(); //获取分
      const s = dt.getSeconds(); //获取秒

      nowtime.value =
          "当前时间：" +
          y +
          "年" +
          mt +
          "月" +
          day + "日"+
          "-" +
          h +
          "时" +
          m +
          "分" +
          s +
          "秒";
  }
  
  onMounted(() => {
      updateTime(); // 初始化时间显示
      timer = setInterval(updateTime, 1000); // 每秒更新时间
  })
  
  onUnmounted(() => {
      if (timer) {
          clearInterval(timer)
      }
  })
  </script>
  
  <style scoped>
      .header1 {
          position: relative;
          height: 6rem;
          background: url('../../public/assets/head_bg.png') no-repeat;
          background-size: 100% 100%;
      }

      .header1 .img1 {
        position: absolute;
        width: 3.8rem;
        height: 3.8rem;
        left: 1rem;
        top: 0.6rem;
      }

      .header1 .img2 {
        position: absolute;
        width: 3.8rem;
        height: 3.8rem;
        left: 6rem;
        top: 0.6rem;
        border-radius: 50%;
        cursor: pointer;
      }
  
      .header1 h1 {
          font-size: 1.875rem;
          color: #fff;
          text-align: center;
          line-height: 5rem;
      }
  
      .header1 .showTime {
          position: absolute;
          right: 1.875rem;
          top: 0;
          line-height: 4.6875rem;
          color: rgba(255, 255, 255, 0.7);
          font-size: 1.1875rem;
      }

  </style>
  