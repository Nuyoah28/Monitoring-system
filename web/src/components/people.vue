<template>
  <div class="panel">
        <div class="chart" ref="linechart" id="demoDiv">
            <div class="realpeople">
                <div class="content">
                    <div>实时</div>
                    <div>人流</div>
                    
                </div>
                <div class="digits">
                    <div class="digit">{{ Math.floor(realpeople/1000) }}</div>
                    <div class="digit">{{ Math.floor((realpeople % 1000) / 100) }}</div>
                    <div class="digit">{{ Math.floor((realpeople % 100) / 10) }}</div>
                    <div class="digit">{{ realpeople % 10 }}</div>
                </div>
            </div>
            <div class="daypeople">
                <div class="content">
                    <div>当日</div>
                    <div>人流</div>
                    
                </div>
                <div class="digits">
                    <div class="digit">{{ Math.floor(daypeople/1000) }}</div>
                    <div class="digit">{{ Math.floor((daypeople % 1000) / 100) }}</div>
                    <div class="digit">{{ Math.floor((daypeople % 100) / 10) }}</div>
                    <div class="digit">{{ daypeople % 10 }}</div>
                </div>
            </div>
        </div>
        <div class="panel-footer"></div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const realpeople = ref<number>(2)
const daypeople = ref<number>(134)
</script>

<style lang="less" scoped>
    #demoDiv {
        width: 100%;
        height: 100%;
        color: white;

        .realpeople, .daypeople {
            display: flex;
            height: 50%;
            align-items: center;
            justify-content: space-between; /* 两端对齐，避免挤压 */
            padding: 0 1rem; /* 增加内边距防止贴边 */

            .digits {
                flex: 1; /* 自适应宽度 */
                height: 7rem;
                font-size: 2rem;
                font-weight: 600;
                margin-left: 1rem; /* 减小左边距 */
                display: flex;
                align-items: center;
                justify-content: flex-end; /* 数字靠右显示 */

                .digit {
                    flex: 1; /* 数字块自适应 */
                    max-width: 4rem; /* 限制最大宽度 */
                    height: 5rem; /* 稍微减小高度 */
                    background-color: #07253F;
                    margin-left: 0.2rem; /* 减小间距 */
                    margin-right: 0.2rem;
                    border: 1px solid white;

                    /* 裁剪四个角 */
                    border-radius: 6px;  
                    font-size: 3.5rem; /* 减小字号适配 */
                    line-height: 5rem; /* 对应高度 */
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    
                    text-shadow: 
                        0.2rem 0.4rem 1rem rgba(255, 255, 255, .4), 
                        -0.2rem -0.4rem 1rem rgba(255, 255, 255, .4), 
                        0.2rem -0.4rem 1rem rgba(255, 255, 255, .4), 
                        -0.2rem 0.4rem 1rem rgba(255, 255, 255, .4); 

                }
            }
        }

        .realpeople .content, .daypeople .content {
            width: 4rem; /* 减小文字区域固定宽度 */
            font-size: 1.6rem; /* 稍微调小字号 */
            font-weight: 600;
            flex-shrink: 0; /* 防止文字被压缩 */
            text-align: center;
        }
    }
</style>
