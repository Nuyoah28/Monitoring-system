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
// 目前是连接本地的后端，后续用服务器在这里修改
// $http.baseUrl = "http://8.152.219.117:10215";
// $http.baseUrl = "http://192.168.115.66:10115"
$http.baseUrl = API_BASE_URL;
// $http.baseUrl = "http://192.168.3.135:10215";
// $http.baseUrl = "http://192.168.68.31:10215";

$http.beforeRequest = function (options) {
    let token = uni.getStorageSync('token')
    // console.log("token!!!!1",token);
    let header = {};
    if (token) {
        header = {
            Authorization: token
        }
    }
    options.header = header
    uni.showLoading({
        title: '加载中'
    })
}
$http.afterRequest = function () {
    uni.hideLoading();
}