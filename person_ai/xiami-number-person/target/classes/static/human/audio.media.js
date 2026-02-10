const AudioContext = function () {
    return new (window.AudioContext || window.webkitAudioContext)();
};

const AudioPlayer = function (audioOptions, onPlay, onDone) {
    this.audioOptions = audioOptions;
    this.audioContext = null;
    this.onPlay = onPlay;
    this.onDone = onDone;
    this.bufferSource = null;
    this.audioQueue = [];
    this.isPlaying = false;
    this.isDoneing = true;

    this.onPause = function () {
        this.bufferSource && this.bufferSource.stop();
        this.audioContext && this.audioContext.close();
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.isDoneing = true;
    };
    this.onPush = function (buffer) {
        this.audioContext = this.audioContext || new AudioContext();
        this.audioQueue.push(buffer);
        this.onPlayNextAudio();
    };
    //将arrayBuffer转为audioBuffer
    this.onBufferPCMData = function (buffer) {
        const length = buffer.byteLength / 2; // 假设 PCM 数据为 16 位，需除以 2
        const audioBuffer = this.audioContext.createBuffer(this.audioOptions.numberChannels, length, this.audioOptions.sampleRate);
        const channelData = audioBuffer.getChannelData(0);
        const bufferArray = new Int16Array(buffer);// 将 PCM 数据转换为 Int16Array
        for (let i = 0; i < length; i++) {
            // 将 16 位 PCM 转换为浮点数 (-1.0 到 1.0)
            channelData[i] = bufferArray[i] / 32768;// 16 位数据转换范围
        }
        return audioBuffer;
    };

    this.onPlayAudio = function (buffer) {
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        this.bufferSource = this.audioContext.createBufferSource();
        this.bufferSource.buffer = buffer;
        this.bufferSource.connect(this.audioContext.destination);
        this.bufferSource.onended = () => {
            this.isPlaying = false;
            this.bufferSource = null;
            this.onPlayNextAudio();
        };
        this.bufferSource.start();
        if (this.isDoneing) {
            this.isDoneing = false;
            this.onPlay();
        }
        this.isPlaying = true;
    };
    // Play the next audio in the queue
    this.onPlayNextAudio = function () {
        if (this.audioQueue.length > 0 && !this.isPlaying) {
            // 计算总的字节长度
            const totalLength = this.audioQueue.reduce((acc, buffer) => acc + buffer.byteLength, 0);
            const bufferArray = new Uint8Array(totalLength);
            let offset = 0;
            // 将所有 audioQueue 中的 buffer 拼接到一个新的 Uint8Array 中
            for (const buffer of this.audioQueue) {
                bufferArray.set(new Uint8Array(buffer), offset);
                offset += buffer.byteLength;
            }
            // 清空 audioQueue，因为我们已经拼接完所有数据
            this.audioQueue = [];
            // 发送拼接的 audio 数据给 PlayAudio
            this.onPlayAudio(this.onBufferPCMData(bufferArray.buffer));
        }
        if (this.audioQueue.length === 0 && !this.isPlaying) {
            this.isDoneing = true;
            this.onDone();
        }
    };
};

const AudioRecorder = function (audioOptions) {
    this.audioOptions = audioOptions;
    this.audioContext = null;
    this.mediaStreamSource = null;
    this.scriptProcessor = null;
    this.mediaStream = null;
    this.buffer = [];
    this.duration = 0;
    this.size = 0;
    this.vol = 0;
    this.onProcess = function (params) {
        console.log(params);
    };
    this.open = function () {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            return navigator.mediaDevices.getUserMedia({audio: true});
        }
        return Promise.reject(new Error('浏览器不支持麦克风！'));
    };
    this.start = function (mediaStream, _onProcess) {
        this.clear();
        this.audioContext = this.audioContext || new AudioContext();
        this.mediaStream = mediaStream;
        this.mediaStreamSource = this.audioContext.createMediaStreamSource(mediaStream);
        this.scriptProcessor = (this.audioContext.createScriptProcessor || this.audioContext.createJavaScriptNode)
            .apply(this.audioContext, [4096, this.audioOptions.numberChannels, this.audioOptions.numberChannels]);
        this.scriptProcessor.onaudioprocess = (event) => {
            const data = event.inputBuffer.getChannelData(0);
            this.buffer.push(new Float32Array(data));
            this.size += data.length;
            this.duration += 4096 / this.audioOptions.sampleRate;
            this.vol = Math.max.apply(Math, data) * 100;
            const params = {
                data: data,
                vol: this.vol,
                size: this.size,
                duration: this.duration
            };
            (typeof _onProcess === 'function' && _onProcess(params)) || this.onProcess(params);
        };
        this.mediaStreamSource.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.audioContext.destination);
    };
    this.stop = function () {
        this.scriptProcessor && this.scriptProcessor.disconnect();
        this.mediaStreamSource && this.mediaStreamSource.disconnect();
        this.mediaStream && this.mediaStream.getTracks().forEach(track => track.stop());
        this.audioContext && this.audioContext.close();
        this.audioContext = null;
    };
    this.clear = function () {
        this.vol = 0;
        this.size = 0;
        this.duration = 0;
        this.buffer = [];
    };
    this.compress = function () {
        const data = new Float32Array(this.size);
        let offset = 0;
        for (let i = 0; i < this.buffer.length; i++) {
            data.set(this.buffer[i], offset);
            offset += this.buffer[i].length;
        }
        const compression = this.audioContext.sampleRate / this.audioOptions.sampleRate;
        const length = data.length / compression;
        const result = new Float32Array(length);
        let index = 0, j = 0;
        while (index < length) {
            result[index] = data[j];
            j += compression;
            index++;
        }
        return result;
    };
    this.pcm = function () {
        const data = this.compress();
        this.stop();
        const dataView = new DataView(new ArrayBuffer(data.length * (16 / 8)));
        let offset = 0;
        for (let i = 0; i < data.length; i++, offset += 2) {
            const value = Math.max(-1, Math.min(1, data[i]));
            dataView.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7FFF, true);
        }
        return new Blob([dataView]);
    };
}