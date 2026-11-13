# ai-pose-gallery-zh安卓版

> Android 客户端（Capacitor）构建、打包与使用说明

本项目除了 Web 版，还提供基于 **Capacitor 8** 的 Android 客户端。它把 `dist/`、`data/`、`img/`、`thumbs/` 全部打包进 APK，实现**完全离线**的图库与合成台。

> 🤖 **制作说明**：本 Android 客户端的代码修改、离线资源打包、原生插件、构建脚本与 APK 打包，均由 **DeepSeek V4.1 Flash 1017** 执行；上游图库与 Web 应用版权归原作者所有。

- **应用 ID**：`app.anhao.poselib`
- **应用名称**：AI 角色图鉴
- **最低系统**：Android 7.0（API 24）
- **目标 / 编译 SDK**：Android 16（API 36）
- **APK 体积**：约 **1.27 GB**（主要是图库资源，属于正常现象）

> ⚠️ APK 内打包了 ギア 与 CharaDB 的图片。**仅供个人离线使用，请勿公开分发**；CharaDB 原作者明确禁止再分发，详见文末「授权与分发」。

---

## 下载安装（夸克网盘）

已构建的 APK 已上传到夸克网盘，可直接下载安装，无需自行编译：

- **下载链接**：<https://pan.quark.cn/s/502d4fe41d7f>
- **夸克口令**：`/~3a383cGdRT~:/`（复制后打开「夸克 App」也可获取）
- **文件**：AI-Figure-Atlas 安卓版 APK（约 **1.27 GB**）

安装步骤：

1. 在手机上下载 APK
2. 允许浏览器 / 文件管理器「安装未知来源应用」
3. 直接安装即可；要求 Android 7.0+，建议预留 **3 GB** 以上空间

> 网盘链接可能失效；若无法打开，请按下方步骤自行构建。
> APK 内包含受限制图库，**仅限个人学习与离线使用，请勿二次分发或上传到公开下载站**。

---

## 1. 环境要求

| 依赖 | 版本 | 说明 |
| --- | --- | --- |
| Node.js | 20+（推荐 24） | 构建 Web 产物 |
| pnpm | 10+ | 可用 `corepack enable` 启用 |
| JDK | **21** | 需设置 `JAVA_HOME` |
| Android SDK | API 36 | 需包含 build-tools 与 platform 36 |
| Python | 3.10+ | 下载与同步脚本 |

Android SDK 路径写在 `android/local.properties`（该文件不入库）：

```properties
sdk.dir=C\:\\path\\to\\android-sdk
```

或在构建前设置环境变量：

```powershell
$env:JAVA_HOME = "C:\path\to\jdk-21"
$env:ANDROID_HOME = "C:\path\to\android-sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
```

---

## 2. 首次完整构建

```bash
corepack enable
corepack pnpm install
corepack pnpm build

# 复制 Web 产物到 Android（注意：会清空 assets/public）
npx cap sync android

# 下载两款热链服装图（首次约 3,520 个文件 / 128 MB；已存在会自动跳过）
python3 scripts/download_remote_costumes.py

# 把 data/img/thumbs 同步进 APK，并把热链地址改写为本地路径
python3 scripts/sync_android_assets.py

cd android
./gradlew assembleDebug        # Windows: .\gradlew.bat assembleDebug
```

产物：

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

### 构建顺序很重要

```text
pnpm build  →  npx cap sync android  →  sync_android_assets.py  →  gradlew assembleDebug
```

`npx cap sync android` 会**清空** `android/app/src/main/assets/public`。如果跳过 `sync_android_assets.py`，App 里只有网页壳，没有图库数据。

---

## 3. 日常构建

前端代码有改动时：

```bash
corepack pnpm build
npx cap sync android
python3 scripts/sync_android_assets.py
cd android && ./gradlew assembleDebug
```

只更新热链服装图时：

```bash
python3 scripts/download_remote_costumes.py   # 增量下载
python3 scripts/sync_android_assets.py
cd android && ./gradlew assembleDebug
```

---

## 4. 版本号

编辑 `android/app/build.gradle`：

```gradle
defaultConfig {
    versionCode 11          // 每次发布必须 +1
    versionName "0.1.9"     // 展示给用户的版本号
}
```

覆盖安装要求 `versionCode` 递增；同一台机器使用同一个 debug keystore 签名即可直接升级。

安装：

```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

APK 约 1.27 GB，安装前建议预留 **3 GB** 以上空间。

---

## 5. 离线图片策略

| 来源 | 套数 | 本地文件 | 体积 |
| --- | ---: | ---: | ---: |
| ギア・动漫 | 1,320 | 预览图 `.webp` + 缩略图 `.webp` | ~57 MB |
| CharaDB 二次元 | 440 | 原图 `.jpg` + 缩略图 `.webp` | ~71 MB |
| **合计** | **1,760** | **3,520 张** | **~128 MB** |

- ギア动漫的 PNG 原图与 WebP 预览图**分辨率相同（512×768）**，PNG 仅体积大 8 倍，因此脚本只下载 WebP。
- 图片保存在：
  ```text
  img/costumes/gia-anime/     thumbs/costumes/gia-anime/
  img/costumes/charadb/       thumbs/costumes/charadb/
  ```
  这些目录已加入 `.gitignore`，不会提交到仓库。
- Web 版仍使用原站热链；`sync_android_assets.py` **只改写 Android 资产目录里的 JSON**，不修改仓库中的 `data/*.json`，因此网页部署行为不受影响。
- 上游更新后，重新运行下载脚本与同步脚本即可。

---

## 6. 图片保存（原生插件）

Android WebView **不支持** `<a download>`，所以 App 内置了原生保存插件：

- `android/app/src/main/java/app/anhao/poselib/ImageSaverPlugin.java`
- `src/lib/downloadImage.ts`

行为：

- **Android 10+**：写入系统「下载」目录 `Download/AI-Figure-Atlas/`
- **Android 9 及以下**：写入应用专属下载目录（无需存储权限）
- 支持本地 assets 图片、远程 `https://` 图片、`data:` / `blob:` 图片

新增下载入口时请调用：

```ts
import { downloadImage } from '@/lib/downloadImage'

await downloadImage(src, 'filename.webp')
```

不要改回 `<a download>`，否则在 App 内点击不会有任何反应。

---

## 7. 状态栏与安全区

Capacitor 的 `SystemBars`（配置见 `capacitor.config.ts`）会注入：

```css
--safe-area-inset-top / right / bottom / left
```

注意两个坑：

1. **安全区加在 `#root`，不要加在 `body`**
   Radix 打开下拉菜单/对话框时会锁定滚动，并向 `body` 注入 `padding-top: 0 !important`。如果安全区在 `body` 上，页面会瞬间上移一个状态栏高度。
2. **固定定位浮层要单独处理**
   侧边栏、下拉菜单是 `position: fixed`，不会继承 `#root` 的内边距。对应处理：
   - 侧边栏：`src/index.css` 的 `.safe-top` / `.safe-bottom`
   - 下拉 / 选择菜单：`collisionPadding` + `src/lib/safeArea.ts`
   - 原图查看器：`OriginalImageViewer.tsx` 的 inline padding

---

## 8. 相关目录

```text
android/
├── app/
│   ├── build.gradle                         # versionCode / versionName
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/app/anhao/poselib/
│       │   ├── MainActivity.java            # 注册 ImageSaver 插件
│       │   └── ImageSaverPlugin.java        # 原生图片保存
│       ├── assets/public/                   # cap sync 生成，已忽略
│       └── res/                             # 图标与启动图
├── build.gradle
├── gradle.properties
└── local.properties                         # SDK 路径，已忽略
capacitor.config.ts                          # appId / webDir / SystemBars
scripts/
├── download_remote_costumes.py              # 下载动漫/二次元热链图片
└── sync_android_assets.py                   # 同步资源 + 本地化图片路径
src/lib/downloadImage.ts                     # 下载统一入口
src/lib/safeArea.ts                          # 读取原生安全区
```

---

## 9. 常见问题

**点击「下载原图」没反应**
- 确认 `MainActivity.java` 里注册了 `ImageSaverPlugin`
- 改的是原生代码时必须重新执行 `gradlew assembleDebug`，只跑 `pnpm build` 不会生效

**图库图片 404 / 空白**
- `cap sync` 之后没有运行 `python3 scripts/sync_android_assets.py`
- 或下载脚本没跑完，检查 `download_failed.txt`

**Gradle 报 JDK 版本错误**
- 使用 JDK 21，并确认 `JAVA_HOME` 指向正确目录

**APK 太大**
- 1.27 GB 是完整离线图库的正常体积
- 如需精简，可修改 `sync_android_assets.py` 跳过部分图库，但 App 将无法离线浏览对应内容

**GitHub 拉取/推送失败**
- 本项目在国内网络下通常需要代理（例如 `127.0.0.1:7890`）

---

## 10. 授权与分发

- ギア 系列图片版权归原作者 **ギア（@giaaibusi）** 所有。
- CharaDB 图片来自 **たき AI（@taki_auto）**，其 LICENSE 明确标注：**仅作参考，禁止再分发，禁止用于真人或未成年人用途**。
- 因此：
  - 本仓库**不提交**这两批下载图片（已在 `.gitignore` 中）
  - 本地构建的离线 APK **仅供个人使用**
  - **请勿将 APK 上传到公开 Release、网盘或任何公开下载渠道**

其他授权条款见仓库根目录 [README 的免责声明](../README.md#免责声明与版权说明disclaimer)。
