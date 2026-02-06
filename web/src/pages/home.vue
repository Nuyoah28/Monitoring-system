<template>
  <div class="home">
    <div class="contentText1">
      <el-button type="primary" round class="btn2" @click="goBack">
      <span>&#8592;</span>
       返回
      </el-button>
      <el-button type="success" round class="btn-agent" @click="goAgent">
        智能助手
      </el-button>
    </div>
    

    <div class="contentText2">
      <div class="text1">
        <div>用户名： 小警</div>
        <hr>
        <div>手机号： 18735261687</div>
        <hr>
      </div>
      <div class="text2">
        <img src="../../public/assets/t01c209d217482e57de.jpg" alt="">
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = (): void => {
    router.push('/visual')
}

const goAgent = (): void => {
    router.push('/agent')
}
</script>

<style scoped>
.home {
  width: 100%;
  height: 100%;
    background-color: white;
    position: relative;
}

.btn2 {
  position: absolute;
  left: 0;
  top: 0;
}

.btn-agent {
  position: absolute;
  right: 0;
  top: 0;
}

.btn2 span {
  font-size: 1.3rem;
}

.contentText1 {
  height: 5rem;
}
.contentText2 {
  width: 50%;
  margin: 0 auto;
  /* background-color: skyblue; */
  text-align: left;
  font-size: 1.8rem;
  display: flex;
}

.text1 {
  flex: 11;
}

.text2 {
  flex: 4;
  margin-left: 1rem;
}

.text1 div {
  margin-bottom: 1.5rem;
  margin-top: 1.5rem;
}

.text2 img {
  width: 20rem;
  height: 20rem;
  border: 1px solid gray;
  padding: 1rem;
}

</style>