layui.define(function (exports) {
    const $asr = {
        ws: null,
        app_id: '',
        app_key: '',
        open: function (callback) {
            const loading = layui.layer.load(0);
            $asr.ws = new WebSocket(`wss://vop.baidu.com/realtime_asr?sn=${Date.now()}`);
            $asr.ws.onopen = function () {
                $asr.start();
                typeof callback === 'function' && callback(null, null);
            };
            $asr.ws.onclose = function () {
                layui.layer.close(loading);
                console.log('WebSocket关闭！！');
                $asr.ws = null;
            };
            $asr.ws.onerror = function () {
                layui.layer.close(loading);
                layui.layer.msg('语音识别失败！！（WebSocket）');
                $asr.ws = null;
            };
            $asr.ws.onmessage = function (e) {
                console.log(e.data);
                const data = JSON.parse(e.data);
                if (data.type === 'MID_TEXT' && data.err_no === 0) {
                    typeof callback === 'function' && callback(false, data.result);
                }
                if (data.type === 'FIN_TEXT' && data.err_no === 0) {
                    typeof callback === 'function' && callback(true, data.result);
                }
                if (data.err_no !== 0) {
                    $asr.ws.close()
                    console.log('语音识别失败:', data);
                    //layui.layer.msg(`语音识别失败！（${data.err_no}:${data.err_msg}）`);
                }
            };
        },
        start: function () {
            if ($asr.ws) {
                $asr.ws.send(JSON.stringify({
                    type: 'START',
                    data: {
                        appid: $asr.app_id,
                        appkey: $asr.app_key,
                        dev_pid: 15372,
                        cuid: 'SC1234567890',
                        format: 'pcm',
                        sample: 16000
                    }
                }));
            }
        },
        stop: function () {
            if ($asr.ws) {
                $asr.ws.send(JSON.stringify({type: 'CANCEL'}));
            }
        },
        send: function (buffer) {
            if ($asr.ws) {
                $asr.ws.send(buffer);
            }
        },
        asr: function (blob, callback) {
            const loading = layui.layer.load(0);
            const fileReader = new FileReader();
            fileReader.onload = function (e) {
                console.log(e.target.result);
                layui.$.post('baidu/speech/recognitions', {
                    vop: encodeURIComponent(e.target.result.split(',')[1])
                }, function (data) {
                    console.log(data);
                    if (data.err_no !== 0) {
                        layui.layer.msg(`语音识别失败！（${data.err_no}:${data.err_msg}）`);
                    } else {
                        typeof callback === 'function' && callback(data.result[0]);
                    }
                    layui.layer.close(loading);
                }).error(function (xhr, status, error) {
                    layui.layer.close(loading);
                    layui.layer.msg(`语音识别请求异常，请重试！（${error || status}）`);
                });
            };
            fileReader.onerror = function () {
                layui.layer.close(loading);
                layui.layer.msg(`读取录音文件失败！（${fileReader.error}）`);
            };
            fileReader.readAsDataURL(blob);
        }
    };
    exports('asr', $asr);
});