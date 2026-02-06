<template>
  <div id="demoDiv">
    <!-- <img src="./assets/logo.png"> -->
    <header1></header1>
    <div class="mainbody">
      <body1></body1>
      <body2></body2>
      <body3></body3>
    </div>
    <chat-panel></chat-panel>
    <!-- <router-link to=""></router-link>
    <router-view/> -->
  </div>
</template>
  
<script setup lang="ts">
import header1 from '../components/header.vue';
import body1 from '../components/body1.vue';
import body2 from '../components/body2.vue';
import body3 from '../components/body3.vue';
import chatPanel from '../components/chat_panel.vue';
</script>
  
<style>
/* @import url('../static/font/font.css'); */
* {
  margin: 0;
  padding: 0;
}

#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  /* margin-top: 60px; */
  background-image: url('../../public/assets/bg.jpg');
  background-size: cover;
  /* background-repeat: no-repeat; */
  /* background-size: 100% 120%; */
  /* height: 100%;
  width: 100%; */
}

.mainbody {
  display: flex;
  width: 100%;
  /* background-size: cover; */
  /* height: 40rem; */
  /* height: 100%; */
  /* background-image: url('./assets/bg.jpg'); */
  background-repeat: no-repeat;
  /* background-size: 100% 100%; */
}

.panel {
  position: relative;
  height: 17.875rem;
  border: 1px solid rgba(25, 186, 139, 0.17);
  background: rgba(255, 255, 255, 0.04) url('../../public/assets/line.png');
  padding: 0 1.875rem;
  margin-bottom: 1.0rem;
  margin-top: 0.2rem;
}
.panel::before {
  position: absolute;
  top: 0;
  left: 0;
  content: "";
  width: .625rem;
  height: .625rem;
  border-top: 2px solid #02a6b5;
  border-left: 2px solid #02a6b5;
}
.panel::after {
  position: absolute;
  top: 0;
  right: 0;
  content: "";
  width: .625rem;
  height: .625rem;
  border-top: 2px solid #02a6b5;
  border-right: 2px solid #02a6b5;
}

.panel .panel-footer {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
}
.panel .panel-footer::before {
  position: absolute;
  bottom: 0;
  left: 0;
  content: "";
  width: .625rem;
  height: .625rem;
  border-bottom: 2px solid #02a6b5;
  border-left: 2px solid #02a6b5;
}
.panel .panel-footer::after {
  position: absolute;
  bottom: 0;
  right: 0;
  content: "";
  width: .625rem;
  height: .625rem;
  border-bottom: 2px solid #02a6b5;
  border-right: 2px solid #02a6b5;
}

</style>
  