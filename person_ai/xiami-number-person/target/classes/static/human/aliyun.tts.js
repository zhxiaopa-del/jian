layui.define(function (exports) {
    const $tts = {
        ws: null,
        task_id: null,
        app_key: '',
        sound: [
            {title: '小云', value: 'xiaoyun'},
            {title: '小刚', value: 'xiaogang'}
        ],
        voice: 'xiaoyun',
        open: function (callback) {
            const loading = layui.layer.load(0);
            layui.$.get('aliyun/credentials', function (data) {
                console.log(data);
                $tts.ws = new WebSocket(`wss://nls-gateway-cn-beijing.aliyuncs.com/ws/v1?token=${data}`);
                $tts.ws.binaryType = "arraybuffer";
                $tts.ws.onopen = function () {
                    if ($tts.ws.readyState === WebSocket.OPEN) {
                        $tts.task_id = $tts.uuid();
                        $tts.start();
                    }
                };
                $tts.ws.onclose = function () {
                    layui.layer.close(loading);
                    console.log('WebSocket关闭！！！');
                    $tts.ws = null;
                };
                $tts.ws.onerror = function () {
                    layui.layer.close(loading);
                    layui.layer.msg('语音合成失败！！！（WebSocket）');
                    $tts.ws = null;
                };
                $tts.ws.onmessage = function (e) {
                    console.log(e.data);
                    if (e.data instanceof ArrayBuffer) {
                        typeof callback === 'function' && callback(e.data);
                    } else {
                        const data = JSON.parse(e.data);
                        if (data.header.name === 'SynthesisStarted' && data.header.status === 20000000) {
                            typeof callback === 'function' && callback(null);
                        }
                        if (data.header.name === 'SynthesisCompleted' && data.header.status === 20000000) {
                            $tts.ws.close();
                        }
                        if (data.header.status !== 20000000) {
                            $tts.ws.close();
                            console.log('语音合成失败:', data);
                            //layui.layer.msg(`语音合成失败！（${data.header.status}:${data.header.status_text}）`);
                        }
                    }
                };
            }).error(function (xhr, status, error) {
                layui.layer.close(loading);
                layui.layer.msg(`语音合成请求异常，请重试！（${error || status}）`);
            });
        },
        uuid: function () {
            let d1 = Date.now();
            let d2 = (performance && performance.now && (performance.now() * 1000)) || 0;
            return 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
                let r = Math.random() * 16; //random number between 0 and 16
                if (d1 > 0) {
                    r = (d1 + r) % 16 | 0;
                    d1 = Math.floor(d1 / 16);
                } else {
                    r = (d2 + r) % 16 | 0;
                    d2 = Math.floor(d2 / 16);
                }
                return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
            });
        },
        header: function (name) {
            return {
                message_id: $tts.uuid(),
                task_id: $tts.task_id,
                namespace: 'FlowingSpeechSynthesizer',
                name: name,
                appkey: $tts.app_key
            };
        },
        //voice【发音人，默认是xiaoyun。】
        //format【音频编码格式，支持pcm、wav和mp3格式，默认值：pcm。】
        //sample_rate【音频采样率，默认值：16000Hz。】
        //volume【音量，取值范围：0～100。默认值：50。】
        //speech_rate【语速，取值范围：-500～500，默认值：0。】
        //pitch_rate【语调，取值范围：-500～500，默认值：0。】
        payload: {format: 'PCM', sample_rate: 16000, volume: 100, speech_rate: 0, pitch_rate: 0},
        start: function () {
            if ($tts.ws) {
                $tts.ws.send(JSON.stringify({
                    header: $tts.header('StartSynthesis'),
                    payload: {...$tts.payload, voice: $tts.voice}
                }));
            }
        },
        stop: function () {
            if ($tts.ws) {
                $tts.ws.send(JSON.stringify({header: $tts.header('StopSynthesis')}));
            }
        },
        send: function (text) {
            if ($tts.ws) {
                $tts.ws.send(JSON.stringify({header: $tts.header('RunSynthesis'), payload: {text: text}}));
            }
        }
    };
    exports('tts', $tts);
});