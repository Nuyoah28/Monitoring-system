class Request {
	constructor(options = {}) {
		this.baseUrl = options.baseUrl || ''
		this.beforeRequest = null
		this.afterRequest = null
	}
	get(url, data = {}, options = {}) {
		return this._({ url: this.baseUrl + url, method: 'GET', data, options })
	}
	post(url, data = {}, options = {}) {
		return this._({ url: this.baseUrl + url, method: 'POST', data, options })
	}
	delete(url, data = {}, options = {}) {
		return this._({ url: this.baseUrl + url, method: 'DELETE', data, options })
	}
	put(url, data = {}, options = {}) {
		return this._({ url: this.baseUrl + url, method: 'PUT', data, options })
	}
	_(requestConfig) {
		const request = {
			url: requestConfig.url,
			method: requestConfig.method,
			data: requestConfig.data,
			header: {},
			silent: requestConfig.options && requestConfig.options.silent === true,
		}
		this.beforeRequest && typeof this.beforeRequest === 'function' && this.beforeRequest(request);
		return new Promise((resolve, reject) => {
			uni.request({
				url: request.url,
				method: request.method,
				data: request.data,
				header: request.header,
				sslVerify: false,
				success: (res) => {
					resolve(res);
				},
				fail: (err) => { reject(err) },
				complete: (res) => {
					this.afterRequest && typeof this.afterRequest === 'function' && this.afterRequest(res, request);
				}
			})
		})
	}
}

export const $http = new Request();