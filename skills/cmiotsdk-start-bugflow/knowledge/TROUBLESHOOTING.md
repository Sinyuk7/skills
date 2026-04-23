# CMIOTSDK 问题排查指南

快速定位问题并搜索关键日志，从而高效解决问题。

---

## 快速查询表

按问题现象直接搜索对应的日志 TAG，快速定位问题根源。

| 问题现象 | 搜索 TAG（优先级） | 模块链路 |
|---------|------------------|--------|
| **播放失败 / 无声音** | `LocalPlayback` → `NCMAudioPlayer` → `ComplexBaseDataSource` | 播放控制 → 底层播放器 → 数据源 |
| **播放卡顿 / 频繁缓冲** | `ComplexBaseDataSource` → `CmPlayCacheManager` | 数据加载 → 缓存管理 |
| **播放状态不同步** | `LocalPlayback` → `LF-PlayServiceImpl` | 播放状态机 → 服务实现 |
| **URL 获取失败** | `LF-AccessTokenRefreshInterceptor` → `ComplexBaseDataSource` | Token 处理 → 数据源请求 |
| **缓存相关问题** | `CmPlayCacheManager` → `NMCacheConfigHelper` | 播放缓存 → 缓存配置 |
| **音频焦点丢失** | `LF-AudioFocusManager` | 音频焦点管理 |
| **登录 / Token 异常** | `LF-AccessTokenRefreshInterceptor` → `LF-Session` | Token 刷新 → 会话管理 |
| **内存泄漏 / OOM** | `LocalPlayback` + `NCMAudioPlayer` (检查释放日志) | 释放逻辑 |

---

## 核心模块 TAG 参考

### 播放链路（从上到下）

| 类名 | TAG | 职责 简述 |
|------|-----|---------|
| **GlobalPlayManager** | `GlobalPlayManager` | 播放管理入口 |
| **PlayServiceImpl** | `LF-PlayServiceImpl` | 播放服务实现 |
| **AudioAgent** | `LF-AudioAgent` | 音频代理 |
| **LocalPlayback** | `LocalPlayback` | 播放控制核心（**承上启下**） |
| **NCMAudioPlayer** | `NCMAudioPlayer` | 底层音频播放器（Native 交互） |
| **ComplexBaseDataSource** | `ComplexBaseDataSource` | 网络/缓存数据加载 |

### 缓存与资源

| 类名 | TAG | 职责 简述 |
|------|-----|---------|
| **CmPlayCacheManager** | `CmPlayCacheManager` | 播放缓存管理 |
| **PlayUrlCache** | `LF-PlayUrlCache` | 播放 URL 缓存 |
| **NMCacheConfigHelper** | `NMCacheConfigHelper` | 缓存配置 |
| **PreloadMusicManager** | `PreloadMusicManager` | 预加载管理 |

### 网络与认证

| 类名 | TAG | 职责 简述 |
|------|-----|---------|
| **AccessTokenRefreshInterceptor** | `LF-AccessTokenRefreshInterceptor` | Token 刷新（**认证关键**） |
| **InitAccessTokenInterceptor** | `LF-InitAccessTokenInterceptor` | Token 初始化 |
| **Session** | `LF-Session` | 会话管理 |

### 音频与效果

| 类名 | TAG | 职责 简述 |
|------|-----|---------|
| **AudioFocusManager** | `LF-AudioFocusManager` | 音频焦点管理 |
| **AidjManager** | `AidjManager` | AI DJ 播放管理 |
| **NPUPlayerManager** | `NPUPlayerManager` | NPU 超分管理 |

---

## 问题排查步骤

### 第一步：快速定位（搜索特定 TAG）

根据上面的 **快速查询表**，选择对应的 TAG 在日志中搜索。例如：

- **问题**：播放失败
- **搜索步骤**：
  1. 搜索 `LocalPlayback` 日志，查看是否成功调用 `playInner()`
  2. 如无关键信息，搜索 `NCMAudioPlayer` 日志，查看 Native 层是否初始化成功
  3. 如仍未找到，搜索 `ComplexBaseDataSource` 日志，查看数据源是否加载成功

### 第二步：全量搜救（当第一步无法定位时）

如果上述特定 TAG 的日志无法定位问题，使用 **全量搜救 TAG**：

| 主 TAG | 说明 |
|--------|------|
| **`LF-CMSDKLog`** | SDK 全量日志汇聚点（所有 CMSDKLogUtils 调用的日志） |
| **`AUDIO_PLAYER`** | 播放器全量日志汇聚点（所有 NBLogger 调用的日志） |

**使用方式**：
- 在完整日志中搜索 `LF-CMSDKLog` 或 `AUDIO_PLAYER`，获得 SDK 所有输出
- 日志格式：`LF-CMSDKLog <version>[moduleTag] message` 或 `AUDIO_PLAYER## moduleTag##desc:... ##keyVals:...`
- 扫描全量日志，寻找异常或关键路径的缺失

---

## 关键日志点位置

播放一首网络歌曲的完整日志链路：

```
1. 播放命令发起
   → GlobalPlayManager / PlayServiceImpl (看调用是否进入)
   
2. 创建播放器
   → LocalPlayback.play() (检查状态机)
   → LocalPlayback.playInner() (检查是否成功)
   
3. 设置数据源
   → ComplexBaseDataSource (检查 URL 是否获取成功)
   → LF-AccessTokenRefreshInterceptor (检查 Token 是否有效)
   
4. 底层播放初始化
   → NCMAudioPlayer.prepareAsync() (检查 Native 初始化)
   → onPrepared 回调 (检查 Native 是否回调)
   
5. 开始播放
   → NCMAudioPlayer.start() (检查播放是否启动)
   → onPositionChanged (检查是否产生进度回调)
   
6. 播放完成
   → onCompletion (检查完成回调)
   → LocalPlayback.reset() (检查释放)
```

---

## 关键排查技巧

### 播放失败场景

1. **优先搜索 `LocalPlayback`**：看 `playInner()` 是否执行，检查状态机（mState）
2. **其次搜索 `NCMAudioPlayer`**：检查 Native 初始化是否成功，看 `onPrepared` 回调是否出现
3. **再次搜索 `ComplexBaseDataSource`**：检查 URL 和数据读取是否成功
4. **最后搜索 `LF-AccessTokenRefreshInterceptor`**：检查 Token 是否过期或无效

### 状态不同步场景

1. **搜索 `LocalPlayback` 日志**：查看 mState 状态转移
2. **搜索 `LF-PlayServiceImpl` 日志**：查看 Service 是否同步状态
3. **检查回调**：`onPrepared`, `onCompletion`, `onPlaybackStatusChanged` 是否丢失

### 缓存问题场景

1. **搜索 `CmPlayCacheManager` 日志**：检查缓存是否命中
2. **搜索 `PlayUrlCache` 日志**：检查 URL 缓存是否过期
3. **搜索 `NMCacheConfigHelper` 日志**：检查缓存配置是否正确

### Token / 网络问题场景

1. **搜索 `LF-AccessTokenRefreshInterceptor` 日志**：检查 Token 是否被成功刷新
2. **搜索 `LF-Session` 日志**：检查会话是否有效
3. **搜索 `ComplexBaseDataSource` 日志**：检查网络请求是否成功

---

## 全量搜救方案

当上述所有特定 TAG 都无法定位问题时，使用全量搜救：

**步骤 1**：在完整日志中搜索主 TAG
```
LF-CMSDKLog     # 搜索 SDK 全量日志
AUDIO_PLAYER    # 搜索播放器全量日志
```

**步骤 2**：扫描日志，寻找：
- 异常堆栈 (Throwable / Exception)
- 关键字：`error`, `failed`, `exception`, `crash`, `native`
- 状态转移：`playInner()` → `onPrepared` → `start()` → `onPositionChanged` 的完整链路

**步骤 3**：结合时间戳，定位问题发生的精确时刻，向前后扩展查看上下文

---

## 核心类职责速查

| 类 | 文件路径 | 职责 |
|----|---------|------|
| **GlobalPlayManager** | `iot-sdk/src/main/java/.../repository/music/GlobalPlayManager.kt` | 播放管理入口，接收播放命令 |
| **AudioAgent** | `iot-player/src/main/java/.../player/AudioAgent.kt` | 音频代理，连接 Service 与播放器 |
| **PlayServiceImpl** | `iot-player/src/main/java/.../player/PlayServiceImpl.kt` | 播放服务实现，管理生命周期 |
| **LocalPlayback** | `iot-player/src/main/java/.../player/playback/LocalPlayback.java` | 播放控制核心，**最关键**的诊断点 |
| **CMSDKLogUtils** | `iot-sdk-base/src/main/java/.../sdkbase/utils/CMSDKLogUtils.kt` | SDK 日志工具，TAG: `LF-CMSDKLog` |
| **NBLogger** | `iot-player/src/main/java/.../NBLogger.kt` | 播放器日志工具，TAG: `AUDIO_PLAYER` |

---

## 常见问题速查

| 问题 | 第一搜索 TAG | 关键词 |
|------|-------------|--------|
| 播放失败 | `LocalPlayback` | `playInner()`, `error`, `exception` |
| 卡顿/缓冲慢 | `ComplexBaseDataSource` | `buffer`, `timeout`, `retry` |
| 状态不同步 | `LocalPlayback` + `LF-PlayServiceImpl` | `mState`, `onPrepared`, `onCompletion` |
| URL 失败 | `LF-AccessTokenRefreshInterceptor` | `401`, `token`, `expired` |
| 无声音 | `NCMAudioPlayer` | `onPrepared`, `start()`, `mute` |
| 缓存不命中 | `CmPlayCacheManager` | `hit`, `miss`, `cache` |
| Token 异常 | `LF-AccessTokenRefreshInterceptor` | `refresh`, `token`, `401` |
| 内存泄漏 | `LocalPlayback` | `releaseResources()`, `reset()`, `stop()` |

---

## 备注

- **LocalPlayback** 是诊断的黄金点：它连接上层 Service 和下层 Native 播放器，大多数问题都能通过其日志追踪
- 优先搜索特定 TAG 才是高效排查的关键，全量搜救是最后手段
- 关注时间戳和线程 ID，多线程问题特别需要注意
- Native 层崩溃表现为 NCMAudioPlayer 日志突然中断，检查前序操作和初始化参数
