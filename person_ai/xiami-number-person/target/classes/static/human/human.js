layui.define(function (exports) {
    const $human = {
        //画布
        ctx: null,
        canvas: null,
        //待机与说话动画ID
        id: {standby: null, speak: null},
        //待机与说话动画当前帧
        frame: {standby: 0, speak: 0},
        //待机与说话动画全部帧
        frames: {standby: [], speak: []},
        //数字人形象【名称、位置、待机帧数与间隔、说话帧数与间隔】
        human: [
            {
                title: '小川', value: 'human/xiaochuan',
                standby: {frame: 113, interval: 20},
                speak: {frame: 186, interval: 30}
            },
            {
                title: '关关', value: 'human/guanguan',
                standby: {frame: 152, interval: 80},
                speak: {frame: 114, interval: 60}
            }
        ],
        me: null,
        //场景
        scene: [
            {title: '场景1', value: 'human/background/bg_1.png'},
            {title: '场景2', value: 'human/background/bg_2.png'},
            {title: '场景3', value: 'human/background/bg_3.png'},
            {title: '场景4', value: 'human/background/bg_4.png'},
            {title: '场景5', value: 'human/background/bg_5.png'},
            {title: '场景6', value: 'human/background/bg_6.png'},
            {title: '场景7', value: 'human/background/bg_7.png'}
        ],
        //大模型
        model: [],
        //大模型请求
        request: {model: '', stream: true, messages: []},
        //大模型应答
        response: {messages: []},
        //初始化画布，并加载第一个数字人形象
        init: function () {
            const human = document.querySelector('#human');
            console.log(human.clientWidth + 'x' + human.clientHeight);
            $human.canvas = document.querySelector('#canvas');
            $human.canvas.width = human.clientWidth;
            $human.canvas.height = human.clientHeight;
            $human.ctx = $human.canvas.getContext('2d');
            $human.load($human.human[0]);
        },
        //加载数字人形象
        load: function (human) {
            $human.me = human;
            $human.stop();
            const loading = layui.layer.msg('数字人，加载中...', {
                icon: 16, shade: 0.3, time: 0,
                content: '<span id="loading">数字人，加载中...<span>'
            });
            //加载数字人待机形象
            $human.frames.standby = [];
            for (let i = 1; i <= human.standby.frame; i++) {
                const image = new Image();
                image.src = `${human.value}/standby/standby (${i}).png`;
                $human.frames.standby.push(image);
            }
            //加载数字人说话形象
            $human.frames.speak = [];
            for (let i = 1; i <= human.speak.frame; i++) {
                const image = new Image();
                image.src = `${human.value}/speak/speak (${i}).png`;
                $human.frames.speak.push(image);
            }
            //加载全部图像
            let length = 0, frames = [...$human.frames.standby, ...$human.frames.speak];
            frames.forEach(function (value) {
                $human.onload(value, function () {
                    length++;
                    layui.$('#loading').html(`数字人，加载中...（${Math.round(length / frames.length * 100)}%）`);
                    if (length === frames.length) {
                        $human.draw($human.frames.standby[0]);
                        layui.layer.close(loading);
                        $human.standby();
                    }
                });
            });
        },
        //图像加载
        onload: function (image, callback) {
            if (image.complete) {
                typeof callback === 'function' && callback();
            } else {
                image.onload = function () {
                    typeof callback === 'function' && callback();
                };
                image.onerror = function () {
                    typeof callback === 'function' && callback();
                };
            }
        },
        //画一帧图像
        draw: function (image) {
            if (image && image.width > 0 && image.height > 0) {
                $human.ctx.clearRect(0, 0, $human.canvas.width, $human.canvas.height);
                const scale = Math.min($human.canvas.width / image.width, $human.canvas.height / image.height);
                const width = image.width * scale;
                const height = image.height * scale;
                const x = ($human.canvas.width - width) / 2;
                const y = ($human.canvas.height - height) / 2;
                $human.ctx.drawImage(image, x, y, width, height);
            }
        },
        //停止待机与说话动画
        stop: function () {
            cancelAnimationFrame($human.id.standby);
            cancelAnimationFrame($human.id.speak);
            $human.frame.standby = 0;
            $human.frame.speak = 0;
        },
        timestamp: null,
        //待机动画
        standby: function () {
            $human.stop();
            $human.id.standby = requestAnimationFrame($human._standby);
        },
        _standby: function (timestamp) {
            if (timestamp - $human.timestamp >= $human.me.standby.interval) {
                $human.draw($human.frames.standby[$human.frame.standby]);
                $human.frame.standby = ($human.frame.standby + 1) % $human.frames.standby.length;
                $human.timestamp = timestamp;
            }
            $human.id.standby = requestAnimationFrame($human._standby);
        },
        //说话动画
        speak: function () {
            $human.stop();
            $human.id.speak = requestAnimationFrame($human._speak);
        },
        _speak: function (timestamp) {
            if (timestamp - $human.timestamp >= $human.me.speak.interval) {
                $human.draw($human.frames.speak[$human.frame.speak]);
                $human.frame.speak = ($human.frame.speak + 1) % $human.frames.speak.length;
                $human.timestamp = timestamp;
            }
            $human.id.speak = requestAnimationFrame($human._speak);
        },
        chat: function (text, uuid) {
            if (layui.$(`#CHAT-${uuid}`).length > 0) {
                layui.$(`#CHAT-${uuid}`).html(text);
            } else {
                const ymd = layui.util.toDateString(Date.now(), 'yyyy-MM-dd HH:mm:ss');
                layui.$('.layim-chat-main').children().append([
                    '<li class="' + (uuid ? '' : 'layim-chat-role-user') + '">',
                    ' <div class="layim-chat-userinfo">',
                    '  <img src="' + (uuid ? `${$human.me.value}/me.png` : 'logo.png') + '" alt="">',
                    '  <cite>' + (uuid ? `${$human.me.title}<i>${ymd}</i>` : `<i>${ymd}</i>我`) + '</cite>',
                    ' </div>',
                    ' <div id="CHAT-' + (uuid || Date.now()) + '" class="layim-chat-text layui-text">' + text + '</div>',
                    '</li>'
                ].join(''));
            }
            const dom = document.querySelector('.layim-chat-main');
            dom.scrollTop = dom.scrollHeight;
        },
        //说话
        send: function (text, callback) {
            $human.response.messages = [];
            $human.request.messages.push({role: 'user', content: text});
            console.log($human.request);
            SSE.fetchEventSource('chat/completions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify($human.request),
                onopen: function (response) {
                    console.log(response);
                    if (!response.ok) {
                        throw new Error(response.status + '-' + response.statusText);
                    }
                },
                onmessage: function (msg) {
                    console.log(msg);
                    if (msg.event === 'FatalError') {
                        throw new Error(msg.data);
                    }
                    if (msg.data === '[DONE]') {
                        if ($human.response.messages.join('') !== '') {
                            $human.request.messages.push({
                                role: 'assistant',
                                content: $human.response.messages.join('')
                            });
                        }
                        typeof callback === 'function' && callback(true, null);
                    }
                    if (msg.data.startsWith('{') && msg.data.endsWith('}')) {
                        const data = JSON.parse(msg.data);
                        if (data.choices && data.choices[0] && data.choices[0].delta) {
                            const text = data.choices[0].delta.reasoning_content || data.choices[0].delta.content || '';
                            $human.response.messages.push(data.choices[0].delta.content || '');
                            typeof callback === 'function' && callback(false, text);
                        }
                    }
                },
                onclose: function () {
                    console.log('SSE关闭！');
                    typeof callback === 'function' && callback(true, null);
                },
                onerror: function (error) {
                    console.log(error);
                    $human.request.messages.pop();
                    layui.layer.msg(`发送数据失败！（${error}）`);
                    typeof callback === 'function' && callback(true, null);
                    throw error;
                }
            });
        },
        models: function (callback) {
            layui.$.get('chat/models', function (data) {
                $human.model = data;
                $human.request.model = data[0].value;
                typeof callback === 'function' && callback();
            }).error(function (xhr, status, error) {
                layui.layer.msg(`模型请求异常，请重试！（${error || status}）`);
            });
        }
    };
    exports('human', $human);
});

