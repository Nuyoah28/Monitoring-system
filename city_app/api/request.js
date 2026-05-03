import { $http } from './index'
import { API_BASE_URL } from '../common/config.js'

uni.$showMsg = function (title = "数据加载失败", duration = 1500) {
    uni.showToast({
        title,
        duration,
        icon: 'none'
    })
}

uni.$http = $http;
// 后端地址统一在 common/config.js 里修改。
$http.baseUrl = API_BASE_URL;

let requestCount = 0;

$http.beforeRequest = function (options) {
    let token = uni.getStorageSync('token')
    let header = {};
    if (token) {
        header = {
            Authorization: token
        }
    }
    options.header = header
    if (options.silent) return;
    if (requestCount === 0) {
        uni.showLoading({
            title: '加载中',
            mask: true
        })
    }
    requestCount++;
}
$http.afterRequest = function (res, options = {}) {
    if (options.silent) return;
    requestCount--;
    if (requestCount <= 0) {
        requestCount = 0;
        uni.hideLoading();
    }
}
