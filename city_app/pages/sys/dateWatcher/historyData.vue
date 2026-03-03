<template>
    <view class="body">
        <view class="dateSelect">
            <text class="text">选择时间跨度：</text>
            <view class="picker-trigger" @click="showFilter = true">
                <text class="val">{{ currentFilterName }}</text>
                <u-icon name="arrow-down" color="#1A2A3A" size="28rpx"></u-icon>
            </view>
        </view>

        <!-- 这里的 0 宽高容器依然保留，用于放置选择器弹窗 -->
        <view style="position: absolute; width: 0; height: 0; overflow: hidden;">
            <u-picker
                :show="showFilter"
                :columns="filters"
                keyName="label"
                title="请选择跨度"
                :showToolbar="true"
                @confirm="setFilter"
                @cancel="showFilter = false"
            ></u-picker>
        </view>

        <!-- 图表卡片容器：赛博清晨白璃拟态 -->
        <scroll-view scroll-y="true" class="chart-scroll">
            <view class="card">
                <view class="card-header">
                    <view class="decorator"></view>
                    <text class="card-title">报警数量趋势 (折线图)</text>
                </view>
                <view class="chart-box">
                    <line-chart :range="currentFilterValue"></line-chart>
                </view>
            </view>

            <view class="card">
                <view class="card-header">
                    <view class="decorator"></view>
                    <text class="card-title">各类报警数量排行 (雷达图)</text>
                </view>
                <view class="chart-box">
                    <bar-chart :range="currentFilterValue"></bar-chart>
                </view>
            </view>

            <view class="card">
                <view class="card-header">
                    <view class="decorator"></view>
                    <text class="card-title">区域报警分布 (横向柱状图)</text>
                </view>
                <view class="chart-box">
                    <row-chart :range="currentFilterValue"></row-chart>
                </view>
            </view>
        </scroll-view>
    </view>
</template>

<script>
import lineChart from "../../../components/lineChart.vue"
import barChart from "../../../components/barChart.vue"
import rowChart from "../../../components/rowChart.vue"

export default {
    components: {
        lineChart,
        barChart,
        rowChart
    },
    data() {
        return {
            showFilter: false,
            currentFilterName: "近一天",
            currentFilterValue: 1,
            filters: [
                [
                    { label: "近一天", value: 1 },
                    { label: "近三天", value: 3 },
                    { label: "近一周", value: 7 },
                    { label: "近一个月", value: 30 }
                ]
            ]
        }
    },
    methods: {
        setFilter(e) {
            this.currentFilterName = e.value[0].label;
            this.currentFilterValue = e.value[0].value;
            this.showFilter = false;
        }
    }
}
</script>

<style lang="scss" scoped>
.body {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: transparent;
    padding-top: 20rpx;
}

.dateSelect {
    width: 92%;
    margin: 0 auto 30rpx auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20rpx 0;
    
    .text {
        font-size: 28rpx;
        color: #1A2A3A;
        font-weight: 600;
    }
    
    .picker-trigger {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 15rpx 30rpx;
        border-radius: 40rpx;
        border: 1px solid rgba(0, 122, 255, 0.2);
        display: flex;
        align-items: center;
        box-shadow: 0 4rpx 12rpx rgba(100, 150, 200, 0.05);

        .val {
            font-size: 28rpx;
            color: #1A2A3A;
            margin-right: 10rpx;
        }
    }
}

.chart-scroll {
    flex: 1;
    min-height: 0;
    width: 100%;
}

.card {
    width: 92%;
    margin: 0 auto 30rpx auto;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 32rpx;
    border: 1px solid rgba(255, 255, 255, 1);
    padding: 30rpx;
    box-sizing: border-box;
    box-shadow: 0 16rpx 48rpx rgba(26, 42, 58, 0.1);

    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 24rpx;

        .decorator {
            width: 8rpx;
            height: 32rpx;
            background: linear-gradient(180deg, #007AFF, #00D2FF);
            border-radius: 4rpx;
            margin-right: 16rpx;
        }

        .card-title {
            font-size: 30rpx;
            font-weight: 700;
            color: #1A2A3A;
        }
    }

    .chart-box {
        width: 100%;
        height: 480rpx;
    }
}
</style>
