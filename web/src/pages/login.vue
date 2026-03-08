<template>
    <div class="body">
        <div class="wrapper">

            <span class="bg-animate">

            </span>
            <div class="form-box login">
                <h2>Login</h2>
                <form action="#" @submit.prevent>
                    <div class="input-box">
                        <input type="text" required v-model="username">
                        <label>Username</label>
                        <i class="bx bxs-user"></i>
                    </div>
                    <div class="input-box">
                        <input type="password" required v-model="password">
                        <label>Password</label>
                        <i class="bx bxs-lock-alt"></i>
                    </div>

                    <button type="submit" class="btn" @click="login">login</button>
                
                    <div class="logreg-link">
                        <p>仅限系统内部授权管理者使用！
                        <a href="#" class="register-link">了解详情</a>
                        </p>
                    </div>
                </form>
            </div>

            <div class="info-text login">
                <h2>智慧社区</h2>
                <h2>监控预警系统</h2>
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
        console.log(res.data);
        if(res.data.code === "A1000"){
            ElMessage(res.data.message)
            return;
        }
        if(res.data.code === "00000"){
            ElMessage({
                message: '登录成功',
                type: 'success'
            });
            // 使用 Pinia store 存储用户信息
            userStore.setUserInfo(username.value, res.data.data.name, res.data.data.id, res.data.data.token)
            // 同步到 sessionStorage 以实现持久化
            userStore.syncToSessionStorage()
            router.push('/visual');
        }
    }).catch((error: any) => {
        console.error('Login error:', error);
    })
}
</script>

<style>
@import url('https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css');
.body {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #081b29;
}

.wrapper {
    position: relative;
    width: 46.875rem; /* 750px -> 46.875rem */
    height: 28.125rem; /* 450px -> 28.125rem */
    background: transparent;
    border: 0.125rem solid #01ade1; /* 2px -> 0.125rem */
    box-shadow: 0 0 1.5625rem #01ade1; /* 25px -> 1.5625rem */
    overflow: hidden;
}

.wrapper .form-box {
    position: absolute;
    top: 0;
    width: 50%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.wrapper .form-box.login {
    width: 48%;
    left: 0;
    padding: 0 0.9375rem 0 1.25rem; /* 15px -> 0.9375rem, 20px -> 1.25rem */
}

.form-box h2 {
    font-size: 2rem; /* 32px -> 2rem */
    color: #fff;
    text-align: center;
    margin: 0 auto 1.5625rem auto; /* 顶部和底部的间距 */
    display: block;
}

.form-box .input-box {
    position: relative;
    width: 100%;
    height: 3.125rem; /* 50px -> 3.125rem */
    margin: 1.5625rem 0; /* 25px -> 1.5625rem */
}

.input-box input {
    width: 100%;
    height: 3.125rem; /* 50px -> 3.125rem */
    background: transparent;
    border: none;
    outline: none;
    border-bottom: 0.125rem solid #fff; /* 2px -> 0.125rem */
    font-size: 1rem; /* 16px -> 1rem */
    color: #fff;
    font-weight: 500;
    transition: 0.5s;
}

.input-box input:focus,
.input-box input:valid {
    border-bottom-color: #01ade1;
}

.input-box label {
    position: absolute;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    font-size: 1rem; /* 16px -> 1rem */
    color: #fff;
    pointer-events: none;
    transition: 0.5s;
}

.input-box input:focus~label,
.input-box input:valid~label {
    top: -0.3125rem; /* 5px -> 0.3125rem */
    color: #01ade1;
}

.input-box i {
    position: absolute;
    top: 50%;
    right: 1.1rem; /* 10px -> 0.625rem */
    transform: translateY(-50%);
    font-size: 1.125rem; /* 18px -> 1.125rem */
    color: #fff;
}

.input-box input:focus~i,
.input-box input:valid~i {
    color: #01ade1;
}

.btn {
    position: relative;
    width: 100%;
    height: 2.8125rem; /* 45px -> 2.8125rem */
    background: transparent;
    border: 0.125rem solid #01ade1; /* 2px -> 0.125rem */
    outline: none;
    border-radius: 2.5rem; /* 40px -> 2.5rem */
    cursor: pointer;
    font-size: 1rem; /* 16px -> 1rem */
    color: #fff;
    font-weight: 600;
    z-index: 1;
    overflow: hidden;
}

.btn::before {
    content: '';
    position: absolute;
    top: -100%;
    left: 0;
    width: 100%;
    height: 18.75rem; /* 300px -> 18.75rem */
    background: linear-gradient(#081b29, #80e1ff, #081b29, #71deff);
    z-index: -1;
}

.btn:hover::before {
    top: 0;
}

.form-box .logreg-link {
    font-size: 0.90625rem; /* 14.5px -> 0.90625rem */
    color: #fff;
    text-align: center;
    margin: 1.25rem 0 0.625rem; /* 20px -> 1.25rem, 10px -> 0.625rem */
}

.logreg-link p a {
    color: #01ade1;
    text-decoration: none;
    font-weight: 600;
}

.logreg-link p a:hover {
    text-decoration: underline;
}

.wrapper .info-text {
    position: absolute;
    top: 0;
    width: 50%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.wrapper .info-text.login {
    right: 0;
    z-index: 2;
    text-align: right;
    align-items: flex-end;
    gap: 0.375rem;
    padding: 0 2.5rem 3rem 7rem;
}

.info-text h2 {
    font-size: 2rem; /* 32px -> 2rem */
    color: #fff;
    text-transform: uppercase;
    margin-bottom: 0.9375rem; /* 15px -> 0.9375rem */
}

.info-text p {
    font-size: 1rem; /* 16px -> 1rem */
    color: #fff;
}

.info-text.login h2 {
    margin: 0;
    font-size: 2.25rem;
    font-weight: 700;
    letter-spacing: 0.14rem;
    line-height: 1.15;
    text-shadow: 0 0 1.25rem rgba(1, 173, 225, 0.4);
}

.info-text.login h2:nth-of-type(2) {
    font-size: 1.7rem;
    font-weight: 500;
    letter-spacing: 0.08rem;
    color: #b7f0ff;
}

.info-text.login p {
    margin-top: 0.75rem;
    font-size: 0.95rem;
    letter-spacing: 0.24rem;
    color: #89dbf3;
}

.wrapper .bg-animate {
    position: absolute;
    top: 0;
    right: 0;
    width: 53.125rem; /* 850px -> 53.125rem */
    height: 37.5rem; /* 600px -> 37.5rem */
    background: linear-gradient(45deg, #081b29, #57c3e4);
    transform: rotate(10deg) skewY(40deg);
    transform-origin: bottom right;
    border-bottom: 0.1875rem solid #01ade1; /* 3px -> 0.1875rem */
}

.wrapper .form-box {
    text-align: left;
}


</style>
