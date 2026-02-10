package web.digital.human;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.digest.HmacUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@RestController
public class HumanController {
    private final static Logger LOGGER = LoggerFactory.getLogger(HumanController.class);
    private final HumanProperties properties;
    private final WebClient webClient;
    private final Credentials credentials = new Credentials();
    private final Token token = new Token();

    public HumanController(HumanProperties properties, WebClient webClient) {
        this.properties = properties;
        this.webClient = webClient;
    }

    /*
     * 模型列表
     */
    @GetMapping(value = "/chat/models", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<List<?>> models() {
        return Mono.just(this.properties.getChat().getModels());
    }

    /*
     * 对话
     */
    @PostMapping(value = "/chat/completions", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> chatCompletions(@RequestBody ChatRequest request) {
        return this.webClient.post()
                .uri(this.properties.getChat().getBaseUrl() + "/chat/completions")
                .header("Authorization", String.format("Bearer %s", this.properties.getChat().getApiKey()))
                .accept(MediaType.TEXT_EVENT_STREAM)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request).retrieve().bodyToFlux(String.class)
                .doOnNext(s -> {
                    if (LOGGER.isInfoEnabled()) {
                        LOGGER.info("对话：{}", s);
                    }
                })
                .onErrorResume(e -> {
                    if (LOGGER.isErrorEnabled()) {
                        LOGGER.error("对话：{}", e.getMessage(), e);
                    }
                    return Flux.empty();
                });
    }

    /*
     * 【阿里云】鉴权认证
     * https://help.aliyun.com/zh/isi/getting-started/use-http-or-https-to-obtain-an-access-token?spm=a2c4g.11186623.help-menu-30413.d_1_2_2.5e196b9bL8hfht&scm=20140722.H_113251._.OR_help-T_cn~zh-V_1
     */
    @GetMapping(value = "/aliyun/credentials", produces = MediaType.TEXT_PLAIN_VALUE)
    public Mono<String> token() {
        return this.refreshToken().map(token -> {
                    if (LOGGER.isInfoEnabled()) {
                        LOGGER.info("【阿里云】TOKEN：{} - {}", token.getId(), new Date(token.getExpireTime()));
                    }
                    return token.getId();
                })
                .onErrorResume(e -> {
                    if (LOGGER.isErrorEnabled()) {
                        LOGGER.error("【阿里云】TOKEN：{}", e.getMessage(), e);
                    }
                    return Mono.empty();
                });
    }

    /*
     * 【阿里云】语音识别
     * https://help.aliyun.com/zh/isi/developer-reference/restful-api-2?spm=a2c4g.11186623.help-menu-30413.d_3_0_0_1.11686b9brDCn5O&scm=20140722.H_92131._.OR_help-T_cn~zh-V_1
     */
    @PostMapping(value = "/aliyun/speech/recognitions", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<String> speechRecognitions(String appKey, String vop) {
        return Mono.fromCallable(() -> Base64.decodeBase64(urlDecoder(vop)))
                .flatMap((bytes) -> this.refreshToken()
                        .flatMap(token -> this.webClient.post()
                                .uri("https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr?appkey={0}&format=pcm&sample_rate=16000"
                                        , appKey)
                                .header("X-NLS-Token", token.getId())
                                .header("Host", "nls-gateway-cn-shanghai.aliyuncs.com")
                                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                                .bodyValue(bytes).retrieve().bodyToMono(String.class)))
                .doOnNext(s -> {
                    if (LOGGER.isInfoEnabled()) {
                        LOGGER.info("【阿里云】语音识别：{}", s);
                    }
                })
                .onErrorResume(e -> {
                    if (LOGGER.isErrorEnabled()) {
                        LOGGER.error("【阿里云】语音识别：{}", e.getMessage(), e);
                    }
                    return Mono.empty();
                });
    }

    /*
     * 【百度】鉴权认证
     * https://ai.baidu.com/ai-doc/REFERENCE/Ck3dwjhhu
     */
    @GetMapping(value = "/baidu/credentials", produces = MediaType.TEXT_PLAIN_VALUE)
    public Mono<String> credentials() {
        return this.refreshCredentials().map(credentials -> {
                    if (LOGGER.isInfoEnabled()) {
                        LOGGER.info("【百度】TOKEN：{} - {}", credentials.getAccessToken(), new Date(credentials.getExpiresIn()));
                    }
                    return credentials.getAccessToken();
                })
                .onErrorResume(e -> {
                    if (LOGGER.isErrorEnabled()) {
                        LOGGER.error("【百度】TOKEN：{}", e.getMessage(), e);
                    }
                    return Mono.empty();
                });
    }

    /*
     * 【百度】语音识别
     * https://ai.baidu.com/ai-doc/SPEECH/4lbxdz34z
     */
    @PostMapping(value = "/baidu/speech/recognitions", produces = MediaType.APPLICATION_JSON_VALUE)
    public Mono<String> speechRecognitions(String vop) {
        return Mono.fromCallable(() -> Base64.decodeBase64(urlDecoder(vop)))
                .flatMap((bytes) -> this.refreshCredentials()
                        .flatMap(credentials -> this.webClient.post()
                                .uri("https://vop.baidu.com/pro_api?token={0}&cuid=SC1234567890&dev_pid=80001"
                                        , credentials.getAccessToken())
                                .header("format", "pcm")
                                .header("rate", "16000")
                                .accept(MediaType.APPLICATION_JSON)
                                .contentType(MediaType.parseMediaType("audio/pcm;rate=16000"))
                                .bodyValue(bytes).retrieve().bodyToMono(String.class)))
                .doOnNext(s -> {
                    if (LOGGER.isInfoEnabled()) {
                        LOGGER.info("【百度】语音识别：{}", s);
                    }
                })
                .onErrorResume(e -> {
                    if (LOGGER.isErrorEnabled()) {
                        LOGGER.error("【百度】语音识别：{}", e.getMessage(), e);
                    }
                    return Mono.empty();
                });
    }

    //【百度】鉴权认证
    Mono<Credentials> refreshCredentials() {
        if (StringUtils.hasText(this.credentials.getAccessToken())
                && this.credentials.getExpiresIn() > System.currentTimeMillis()) {
            return Mono.just(this.credentials);
        }
        return this.webClient.get()
                .uri("https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={0}&client_secret={1}"
                        , this.properties.getBaidu().getApiKey(), this.properties.getBaidu().getSecretKey())
                .accept(MediaType.APPLICATION_JSON)
                .retrieve().bodyToMono(Credentials.class).map(credentials -> {
                    this.credentials.setAccessToken(credentials.getAccessToken());
                    this.credentials.setExpiresIn(System.currentTimeMillis() + credentials.getExpiresIn() * 1000);
                    return this.credentials;
                });
    }

    //【阿里云】鉴权认证
    Mono<Token> refreshToken() {
        if (StringUtils.hasText(this.token.getId())
                && this.token.getExpireTime() > System.currentTimeMillis()) {
            return Mono.just(this.token);
        }
        return Mono.fromCallable(() -> new LinkedMultiValueMap<String, String>() {{
            this.add("AccessKeyId", properties.getAliyun().getAccessKeyId());
            this.add("Action", "CreateToken");
            this.add("Format", "JSON");
            this.add("RegionId", "cn-shanghai");
            this.add("SignatureMethod", "HMAC-SHA1");
            this.add("SignatureNonce", UUID.randomUUID().toString());
            this.add("SignatureVersion", "1.0");
            this.add("Timestamp", LocalDateTime.now(Clock.systemUTC())
                    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'")));
            this.add("Version", "2019-02-28");
            String[] keys = this.toSingleValueMap().keySet().toArray(new String[0]);
            Arrays.sort(keys);
            StringJoiner sign = new StringJoiner("&");
            for (String key : keys) {
                sign.add(String.format("%s=%s", urlEncoder(key), urlEncoder(this.getFirst(key))));
            }
            String key = String.format("%s&", properties.getAliyun().getAccessKeySecret());
            String value = String.format("GET&%s&%s", urlEncoder("/"), urlEncoder(sign.toString()));
            this.add("Signature", Base64.encodeBase64String(new HmacUtils("HmacSHA1", key).hmac(value)));
        }}).flatMap(params -> this.webClient.get()
                .uri("https://nls-meta.cn-shanghai.aliyuncs.com", uriBuilder -> uriBuilder.queryParams(params).build())
                .accept(MediaType.APPLICATION_JSON)
                .retrieve().bodyToMono(Token.class).map(token -> {
                    this.token.setId(token.getId());
                    this.token.setExpireTime(token.getExpireTime() * 1000);
                    return this.token;
                }));
    }

    static String urlDecoder(String s) throws IOException {
        return URLDecoder.decode(s, "UTF-8");
    }

    static String urlEncoder(String s) throws IOException {
        return URLEncoder.encode(s, "UTF-8")
                .replace("+", "%20")
                .replace("*", "%2A")
                .replace("%7E", "~");
    }

    static class ChatRequest {
        public String model;
        public boolean stream;
        public List<Message> messages;

        public ChatRequest() {
            this.model = null;
            this.stream = false;
            this.messages = null;
        }

        static class Message {
            public String role;
            public String content;

            public Message() {
                this.role = null;
                this.content = null;
            }
        }
    }

    static class Credentials {
        @JsonProperty("access_token")
        private String accessToken;
        @JsonProperty("expires_in")
        private long expiresIn;

        public String getAccessToken() {
            return accessToken;
        }

        public void setAccessToken(String accessToken) {
            this.accessToken = accessToken;
        }

        public long getExpiresIn() {
            return expiresIn;
        }

        public void setExpiresIn(long expiresIn) {
            this.expiresIn = expiresIn;
        }
    }

    static class Token {
        @JsonProperty("Token")
        public _Token token = new _Token();

        public String getId() {
            return this.token.id;
        }

        public void setId(String id) {
            this.token.id = id;
        }

        public long getExpireTime() {
            return this.token.expireTime;
        }

        public void setExpireTime(long expireTime) {
            this.token.expireTime = expireTime;
        }

        static class _Token {
            @JsonProperty("Id")
            public String id;
            @JsonProperty("ExpireTime")
            public long expireTime;
        }
    }
}
