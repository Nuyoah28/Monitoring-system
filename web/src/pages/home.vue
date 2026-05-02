<template>
  <div class="dash home">
    <header class="head profile-head">
      <div>
        <h1>值班员信息</h1>
        <p>快速查看个人资料，返回驾驶舱或进入智能助手</p>
      </div>
      <div class="head-actions">
        <button class="pill action-pill" type="button" @click="goBack">返回驾驶舱</button>
        <button class="pill action-pill action-pill-primary" type="button" @click="goAgent">进入智能助手</button>
      </div>
    </header>

    <section class="grid single">
      <article class="card profile">
        <div class="profile-meta">
          <div class="avatar-shell">
            <div class="avatar big">张三</div>
            <span class="role-chip">值班中</span>
          </div>

          <div class="profile-copy">
            <div class="profile-label">值班人员档案</div>
            <div class="profile-name">张三</div>
            <div class="profile-list">
              <div class="info-row">
                <span>用户名</span>
                <strong>张三</strong>
              </div>
              <div class="info-row">
                <span>手机号</span>
                <strong>18735261687</strong>
              </div>
              <div class="info-row">
                <span>岗位</span>
                <strong>社区安防值班员</strong>
              </div>
            </div>
          </div>
        </div>

        <div class="profile-img">
          <div class="portrait-frame">
            <img src="../../public/assets/t01c209d217482e57de.jpg" alt="值班员头像">
          </div>
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
  router.push('/visual')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
}

.profile-head {
  grid-template-columns: minmax(0, 1fr) auto;
}

.head-actions {
  display: inline-flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-pill {
  cursor: pointer;
  min-width: 140px;
  justify-content: center;
  border-color: rgba(126, 197, 255, 0.36);
  background:
    linear-gradient(180deg, rgba(22, 56, 89, 0.96), rgba(12, 34, 57, 0.92));
  color: #eef8ff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 10px 22px rgba(4, 12, 20, 0.14);
  font-weight: 600;
}

.action-pill-primary {
  border-color: rgba(255, 141, 141, 0.54);
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 141, 141, 0.22), transparent 38%),
    linear-gradient(180deg, rgba(132, 44, 58, 0.98), rgba(78, 22, 35, 0.94));
  color: #fff1f3;
  box-shadow:
    0 0 0 1px rgba(255, 141, 141, 0.16),
    0 12px 24px rgba(255, 78, 102, 0.14);
}

.grid.single {
  grid-template-columns: 1fr;
}

.profile {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) 360px;
  align-items: center;
  gap: 24px;
  min-height: 0;
}

.profile-meta {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 20px;
  align-items: center;
}

.avatar-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.role-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(126, 232, 255, 0.3);
  background: rgba(126, 232, 255, 0.12);
  color: #c8f4ff;
  font-size: 12px;
  letter-spacing: 0.06em;
}

.profile-copy {
  display: grid;
  gap: 12px;
}

.profile-label {
  color: var(--sub);
  font-size: 12px;
  letter-spacing: 0.14em;
}

.profile-name {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #f7fbff;
}

.profile-list {
  display: grid;
  gap: 10px;
  margin-top: 8px;
}

.info-row {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 18px;
  background:
    radial-gradient(circle at 0% 0%, rgba(126, 232, 255, 0.08), transparent 30%),
    rgba(12, 30, 50, 0.58);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.info-row span {
  color: var(--sub);
  font-size: 12px;
}

.info-row strong {
  color: #eff7ff;
  font-size: 15px;
  font-weight: 600;
}

.profile-img {
  justify-self: end;
}

.portrait-frame {
  position: relative;
  padding: 12px;
  border-radius: 28px;
  border: 1px solid rgba(126, 232, 255, 0.26);
  background:
    radial-gradient(circle at 18% 12%, rgba(126, 232, 255, 0.18), transparent 28%),
    linear-gradient(180deg, rgba(13, 33, 56, 0.9), rgba(9, 23, 39, 0.96));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 18px 30px rgba(4, 12, 20, 0.14);
}

.portrait-frame::after {
  content: '';
  position: absolute;
  inset: auto 12px 12px auto;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(126, 232, 255, 0.24), transparent 72%);
  filter: blur(8px);
}

.profile-img img {
  display: block;
  width: 240px;
  height: 300px;
  border-radius: 20px;
  object-fit: cover;
  border: 1px solid rgba(126, 232, 255, 0.28);
  position: relative;
  z-index: 1;
}

.avatar.big {
  width: 88px;
  height: 88px;
  border-radius: 24px;
  font-size: 20px;
}

@media (max-width: 960px) {
  .profile-head {
    grid-template-columns: 1fr;
  }

  .profile {
    grid-template-columns: 1fr;
  }

  .profile-img {
    justify-self: start;
  }
}

@media (max-width: 760px) {
  .profile-meta {
    grid-template-columns: 1fr;
    justify-items: start;
  }

  .head-actions {
    width: 100%;
  }

  .action-pill {
    flex: 1 1 100%;
  }

  .profile-img img {
    width: min(100%, 240px);
    height: auto;
    aspect-ratio: 4 / 5;
  }

  .info-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
</style>
