<template>
  <div class="login-page">
    <div class="wrapper">
      <span class="bg-animate"></span>
      <span class="grid-line grid-line-a"></span>
      <span class="grid-line grid-line-b"></span>

      <div class="form-box login">
        <div class="form-copy">
          <span class="form-badge">SECURITY ACCESS</span>
          <h2>登录系统</h2>
          <p>使用授权账号进入智慧社区安防平台，查看实时监控、告警处置与数字助手能力。</p>
        </div>

        <form action="#" @submit.prevent>
          <div class="input-box">
            <input v-model="username" type="text" required autocomplete="username">
            <label>用户名</label>
            <i class="bx bxs-user"></i>
          </div>
          <div class="input-box">
            <input v-model="password" type="password" required autocomplete="current-password">
            <label>密码</label>
            <i class="bx bxs-lock-alt"></i>
          </div>

          <button type="submit" class="btn" @click="login">进入平台</button>

          <div class="logreg-link">
            <p>仅限系统内部授权管理者使用。<a href="#" class="register-link">查看接入说明</a></p>
          </div>
        </form>
      </div>

      <div class="info-text login">
        <span class="hero-badge">COMPUTER DESIGN CONTEST</span>
        <h2>社区智眼</h2>
        <h2>监控预警系统</h2>
        <p>AI 联动 · 态势感知 · 实时响应</p>
        <div class="hero-metrics">
          <div class="hero-metric">
            <strong>24 / 7</strong>
            <span>全天候监测</span>
          </div>
          <div class="hero-metric">
            <strong>4 大模块</strong>
            <span>告警、视频、环境、Agent</span>
          </div>
          <div class="hero-metric">
            <strong>实时联动</strong>
            <span>监控点位与 AI 处置联动</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const username = ref<string>('')
const password = ref<string>('')
const router = useRouter()
const userStore = useUserStore()

const login = (): void => {
  const data = {
    userName: username.value,
    password: password.value
  }

  axios.post('/user/login', data).then((res: any) => {
    console.log(res.data)
    if (res.data.code === 'A1000') {
      ElMessage(res.data.message)
      return
    }
    if (res.data.code === '00000') {
      ElMessage({
        message: '登录成功',
        type: 'success'
      })
      userStore.setUserInfo(username.value, res.data.data.name, res.data.data.id, res.data.data.token)
      userStore.syncToSessionStorage()
      router.push('/agent')
    }
  }).catch((error: any) => {
    console.error('Login error:', error)
  })
}
</script>

<style scoped>
@import url('https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css');

.login-page {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 24px;
  background:
    radial-gradient(circle at 10% 12%, rgba(126, 197, 255, 0.16), transparent 24%),
    radial-gradient(circle at 88% 18%, rgba(75, 230, 168, 0.1), transparent 18%),
    linear-gradient(135deg, #05101d, #0b1f35 56%, #123050);
  overflow: hidden;
}

.wrapper {
  position: relative;
  width: min(72rem, 100%);
  min-height: 39rem;
  background:
    linear-gradient(180deg, rgba(10, 24, 41, 0.88), rgba(7, 17, 30, 0.9));
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 2rem;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 32px 64px rgba(2, 10, 20, 0.42);
  overflow: hidden;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.grid-line {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.24;
}

.grid-line-a {
  background:
    linear-gradient(rgba(126, 197, 255, 0.2) 1px, transparent 1px),
    linear-gradient(90deg, rgba(126, 197, 255, 0.2) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(135deg, transparent, rgba(0, 0, 0, 0.9) 26%, rgba(0, 0, 0, 0.9) 78%, transparent);
}

.grid-line-b {
  background:
    radial-gradient(circle at 72% 24%, rgba(126, 232, 255, 0.26), transparent 18%),
    radial-gradient(circle at 85% 74%, rgba(75, 230, 168, 0.18), transparent 22%);
  filter: blur(10px);
}

.wrapper .form-box {
  position: absolute;
  top: 0;
  width: 46%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: left;
}

.wrapper .form-box.login {
  left: 0;
  padding: 3rem 2.4rem 3rem 3rem;
  z-index: 2;
}

.form-copy {
  margin-bottom: 1rem;
}

.form-badge,
.hero-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  border: 1px solid rgba(126, 197, 255, 0.26);
  background: rgba(17, 47, 75, 0.48);
  color: #cde8ff;
  font-size: 0.74rem;
  letter-spacing: 0.16rem;
  text-transform: uppercase;
}

.form-copy p {
  margin: 0;
  color: rgba(214, 230, 255, 0.72);
  font-size: 0.95rem;
  line-height: 1.7;
  max-width: 30rem;
}

.form-box h2 {
  margin: 1rem 0 0.8rem;
  color: #fff;
  font-size: 2.35rem;
  text-align: left;
  letter-spacing: 0.08rem;
}

.form-box .input-box {
  position: relative;
  width: 100%;
  height: 3.5rem;
  margin: 1.35rem 0;
}

.input-box input {
  width: 100%;
  height: 3.5rem;
  background: rgba(5, 17, 30, 0.4);
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 1rem;
  outline: none;
  font-size: 1rem;
  color: #fff;
  font-weight: 500;
  transition: 0.25s;
  padding: 0 3rem 0 1rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.input-box input:focus,
.input-box input:valid {
  border-color: rgba(126, 232, 255, 0.72);
  box-shadow:
    0 0 0 4px rgba(126, 197, 255, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.input-box label {
  position: absolute;
  top: 1.05rem;
  left: 1rem;
  color: rgba(214, 230, 255, 0.8);
  font-size: 1rem;
  pointer-events: none;
  transition: 0.25s;
}

.input-box input:focus~label,
.input-box input:valid~label {
  top: -0.6rem;
  left: 0.85rem;
  padding: 0 0.45rem;
  border-radius: 999px;
  background: #081726;
  color: #8fe5ff;
  font-size: 0.78rem;
}

.input-box i {
  position: absolute;
  top: 50%;
  right: 1rem;
  transform: translateY(-50%);
  font-size: 1.2rem;
  color: rgba(214, 230, 255, 0.72);
}

.input-box input:focus~i,
.input-box input:valid~i {
  color: #8fe5ff;
}

.btn {
  position: relative;
  width: 100%;
  height: 3.3rem;
  margin-top: 0.4rem;
  background: linear-gradient(135deg, #2f7ff1, #4fc5ff 62%, #7ee8ff);
  border: 1px solid rgba(126, 232, 255, 0.42);
  border-radius: 999px;
  outline: none;
  cursor: pointer;
  font-size: 1rem;
  color: #03101d;
  font-weight: 700;
  z-index: 1;
  overflow: hidden;
  box-shadow:
    0 18px 30px rgba(71, 161, 255, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.55), transparent);
  transform: translateX(-120%);
  z-index: -1;
  transition: transform 0.35s ease;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow:
    0 22px 34px rgba(71, 161, 255, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.btn:hover::before {
  transform: translateX(120%);
}

.form-box .logreg-link {
  margin: 1rem 0 0.625rem;
  color: rgba(214, 230, 255, 0.82);
  font-size: 0.92rem;
  text-align: left;
  line-height: 1.7;
}

.logreg-link p {
  margin: 0;
}

.logreg-link p a {
  color: #8fe5ff;
  text-decoration: none;
  font-weight: 600;
}

.logreg-link p a:hover {
  text-decoration: underline;
}

.wrapper .info-text {
  position: absolute;
  top: 0;
  width: 54%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.wrapper .info-text.login {
  right: 0;
  z-index: 2;
  text-align: left;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 3rem 3rem 3rem 8rem;
}

.info-text h2 {
  margin-bottom: 0.9375rem;
  color: #fff;
  font-size: 2rem;
  text-transform: uppercase;
}

.info-text p {
  font-size: 1rem;
  color: #fff;
}

.info-text.login h2 {
  margin: 0;
  font-size: 3.4rem;
  font-weight: 700;
  letter-spacing: 0.18rem;
  line-height: 1.06;
  text-shadow: 0 0 1.6rem rgba(103, 190, 255, 0.28);
}

.info-text.login h2:nth-of-type(2) {
  font-size: 2rem;
  font-weight: 500;
  letter-spacing: 0.12rem;
  color: #c6f6ff;
}

.info-text.login p {
  margin-top: 0.35rem;
  font-size: 1rem;
  letter-spacing: 0.24rem;
  color: #89dbf3;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  width: 100%;
  margin-top: 1.2rem;
}

.hero-metric {
  padding: 1rem 1rem 1.05rem;
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 1.2rem;
  background:
    linear-gradient(180deg, rgba(15, 39, 64, 0.62), rgba(9, 22, 38, 0.52));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.hero-metric strong {
  display: block;
  margin-bottom: 0.45rem;
  color: #f8fcff;
  font-size: 1.2rem;
  letter-spacing: 0.06rem;
}

.hero-metric span {
  display: block;
  color: rgba(214, 230, 255, 0.74);
  font-size: 0.86rem;
  line-height: 1.6;
}

.wrapper .bg-animate {
  position: absolute;
  inset: -12% -8% auto auto;
  width: 54rem;
  height: 42rem;
  background: linear-gradient(145deg, rgba(39, 118, 197, 0.84), rgba(126, 232, 255, 0.42));
  transform: rotate(12deg) skewY(34deg);
  transform-origin: bottom right;
  border-bottom: 3px solid rgba(126, 232, 255, 0.72);
  box-shadow: 0 0 80px rgba(91, 180, 255, 0.22);
}

@media (max-width: 1180px) {
  .wrapper {
    min-height: 52rem;
  }

  .wrapper .form-box,
  .wrapper .info-text,
  .wrapper .info-text.login {
    position: relative;
    width: 100%;
    padding: 2.25rem;
  }

  .wrapper .info-text.login {
    padding-top: 8rem;
  }

  .hero-metrics {
    grid-template-columns: 1fr;
  }

  .wrapper .bg-animate {
    inset: -26% -12% auto auto;
    width: 40rem;
    height: 30rem;
  }
}

@media (max-width: 760px) {
  .login-page {
    padding: 12px;
  }

  .wrapper {
    min-height: 0;
    border-radius: 1.5rem;
  }

  .wrapper .form-box.login,
  .wrapper .info-text.login {
    padding: 1.4rem;
  }

  .form-box h2 {
    font-size: 2rem;
  }

  .info-text.login h2 {
    font-size: 2.4rem;
    letter-spacing: 0.12rem;
  }

  .info-text.login h2:nth-of-type(2) {
    font-size: 1.45rem;
  }

  .info-text.login p,
  .form-badge,
  .hero-badge {
    letter-spacing: 0.1rem;
  }
}
</style>
