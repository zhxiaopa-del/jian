layui.define(function (exports) {
    const $asr = {
        ws: null,
        task_id: null,
        app_key: '',
        open: function (callback) {
            const loading = layui.layer.load(0);
            layui.$.get('aliyun/credentials', function (data) {
                console.log(data);
                $asr.ws = new WebSocket(`wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1?token=${data}`);
                $asr.ws.onopen = function () {
                    $asr.task_id = $asr.uuid();
                    $asr.start();
                };
                $asr.ws.onclose = function () {
                    layui.layer.close(loading);
                    console.log('WebSocket关闭！！！');
                    $asr.ws = null;
                };
                $asr.ws.onerror = function () {
                    layui.layer.close(loading);
                    layui.layer.msg('语音识别失败！！！（WebSocket）');
                    $asr.ws = null;
                };
                $asr.ws.onmessage = function (e) {
                    console.log(e.data);
                    const data = JSON.parse(e.data);
                    if (data.header.name === "TranscriptionStarted" && data.header.status === 20000000) {
                        typeof callback === 'function' && callback(null, null);
                    }
                    if (data.header.name === 'SentenceBegin' && data.header.status === 20000000) {
                    }
                    if (data.header.name === 'TranscriptionResultChanged' && data.header.status === 20000000) {
                        typeof callback === 'function' && callback(false, data.payload.result);
                    }
                    if (data.header.name === 'SentenceEnd' && data.header.status === 20000000) {
                        typeof callback === 'function' && callback(true, data.payload.result);
                    }
                    if (data.header.name === 'TranscriptionCompleted' && data.header.status === 20000000) {
                        $asr.ws.close();
                    }
                    if (data.header.status !== 20000000) {
                        $asr.ws.close();
                        console.log('语音识别失败:', data);
                        //layui.layer.msg(`语音识别失败！（${data.header.status}:${data.header.status_text}）`);
                    }
                };
            }).error(function (xhr, status, error) {
                layui.layer.close(loading);
                layui.layer.msg(`语音识别请求异常，请重试！（${error || status}）`);
            });
        },
        uuid: function () {
            return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
                (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
            ).replace(/-/g, '');
        },
        header: function (name) {
            return {
                message_id: $asr.uuid(),
                task_id: $asr.task_id,
                namespace: 'SpeechTranscriber',
                name: name,
                appkey: $asr.app_key
            };
        },
        start: function () {
            if ($asr.ws) {
                $asr.ws.send(JSON.stringify({
                    header: $asr.header('StartTranscription'),
                    payload: {
                        format: 'PCM',
                        sample_rate: 16000,
                        enable_intermediate_result: true,
                        enable_punctuation_prediction: true,
                        enable_inverse_text_normalization: true
                    }
                }));
            }
        },
        stop: function () {
            if ($asr.ws) {
                $asr.ws.send(JSON.stringify({header: $asr.header('StopTranscription')}));
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
                layui.$.post(`aliyun/speech/recognitions`, {
                    appKey: $asr.app_key,
                    vop: encodeURIComponent(e.target.result.split(',')[1])
                }, function (data) {
                    console.log(data);
                    if (data.status !== 20000000) {
                        layui.layer.msg(`语音识别失败！（${data.status}:${data.message}）`);
                    } else {
                        typeof callback === 'function' && callback(data.result);
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