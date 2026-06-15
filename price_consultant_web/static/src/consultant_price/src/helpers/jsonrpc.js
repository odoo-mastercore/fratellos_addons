import axios from 'axios';

class JsonRpc {

	constructor() {
		this._call = [
			'web/dataset/call',
			'create',
			'write',
			'unlink'
		]
		this._call_kw = [
			'web/dataset/call_kw',
			'search_read'
		]
	}

	call(params) {
		return new Promise((resolve) => {
			let method_flag = false;
			for (let i = 1; i < this._call.length; i++) {
				if (params.method === this._call[i]) {
					method_flag = true
					if (params.kwargs) {
						resolve({
							'error': true,
							'msg': 'call_kw() takes at least 3 arguments (4 given)'
						})
					} else {
						this._(this._call[0], params).then(res => {
							resolve(res)
						})
					}
				}
			}
			if (!method_flag) {
				if (params.method === this._call_kw[1]) {
					method_flag = true
					if (params.kwargs) {
						this._(this._call_kw[0], params).then(res => {
							resolve(res)
						})
					} else {
						resolve({
							'error': true,
							'msg': `call() with method search_read takes at least 4 arguments (3 given)`
						})
					}
				}
			}
			if (!method_flag) {
				resolve({
					'error': true,
					'msg': `method ${params.method} not found`
				})
			}
		})
	}

	_(url, params) {
		return new Promise((resolve) => {
			axios.post(url, {
				'jsonrpc': '2.0',
				'method': 'call',
				'params': params
			}).then(res => {
				resolve(res)
			})
		})
	}

	_route(url, params, mode='object') {
    /*
    * mode='object' = def example(self, obj)
    * mode='attr' = def example(self, attr_1, attr_2)
    */
		return new Promise((resolve) => {
			axios({
				method: 'POST',
				url,
				headers: {
					'Content-type': 'application/json'
				},
        params: mode == 'object' ? { params } : params
			}).then( res => {
				resolve(res)
			})
		})
	}
}

export default JsonRpc
