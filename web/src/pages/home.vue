<template>
  <div class="dash home">
    <header class="head">
      <div>
        <h1>值班员信息</h1>
        <p>快速查看个人资料，返回驾驶舱或进入智能助手</p>
      </div>
      <div class="pill" @click="goBack" style="cursor:pointer">返回驾驶舱</div>
      <div class="pill" @click="goAgent" style="cursor:pointer">进入智能助手</div>
    </header>

    <section class="grid single">
      <article class="card profile">
        <div class="profile-meta">
          <div class="avatar big">张三</div>
          <div>
            <div class="label">用户名</div>
            <div class="value">张三</div>
            <div class="label">手机号</div>
            <div class="value">18735261687</div>
          </div>
        </div>
        <div class="profile-img">
          <img src="../../public/assets/t01c209d217482e57de.jpg" alt="avatar" />
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  router.push('/visual')
}

const goAgent = () => {
  router.push('/agent')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
}

.grid.single {
  grid-template-columns: 1fr;
}

.profile {
  display: grid;
  grid-template-columns: 1fr 320px;
  align-items: center;
}

.profile-meta {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 12px;
  align-items: center;
}

.profile-img {
  justify-self: end;
}

.profile-img img {
  width: 180px;
  height: 180px;
  border-radius: 12px;
  object-fit: cover;
  border: 1px solid var(--line);
}

.label {
  color: var(--sub);
  font-size: 12px;
  margin-top: 6px;
}

.value {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}

.avatar.big {
  width: 72px;
  height: 72px;
  font-size: 18px;
}

@media (max-width: 760px) {
  .profile {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .profile-img {
    justify-self: start;
  }
}
</style>
