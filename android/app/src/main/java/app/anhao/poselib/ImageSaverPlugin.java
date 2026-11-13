package app.anhao.poselib;

import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 把 App 内置图片或网络图片保存到系统「下载」目录。
 * WebView 本身不支持 <a download>，所以由这个原生插件完成写文件。
 */
@CapacitorPlugin(name = "ImageSaver")
public class ImageSaverPlugin extends Plugin {

    private static final String FOLDER = "AI-Figure-Atlas";
    private static final String ASSET_PREFIX = "public/";

    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    @PluginMethod
    public void save(PluginCall call) {
        String src = call.getString("src");
        String filename = call.getString("filename", "image.webp");
        if (src == null || src.trim().isEmpty()) {
            call.reject("缺少图片地址");
            return;
        }
        executor.execute(() -> {
            try {
                byte[] bytes = readBytes(src);
                if (bytes == null || bytes.length == 0) {
                    throw new IOException("图片内容为空");
                }
                String mime = mimeType(filename, bytes);
                String name = sanitize(filename, mime);
                String path = writeToDownloads(bytes, name, mime);
                JSObject result = new JSObject();
                result.put("path", path);
                call.resolve(result);
            } catch (Exception error) {
                String message = error.getMessage() == null ? "保存失败" : error.getMessage();
                call.reject(message, error);
            }
        });
    }

    private byte[] readBytes(String src) throws IOException {
        if (src.startsWith("data:")) {
            int comma = src.indexOf(',');
            if (comma < 0) {
                throw new IOException("无效的 data URL");
            }
            String meta = src.substring(5, comma);
            String payload = src.substring(comma + 1);
            if (meta.contains(";base64")) {
                return Base64.decode(payload, Base64.DEFAULT);
            }
            return URLDecoder.decode(payload, "UTF-8").getBytes(StandardCharsets.UTF_8);
        }

        String assetPath = assetPath(src);
        if (assetPath != null) {
            try (InputStream input = getContext().getAssets().open(ASSET_PREFIX + assetPath)) {
                return readAll(input);
            }
        }

        if (src.startsWith("blob:")) {
            throw new IOException("暂不支持保存 blob 图片，请重试");
        }

        HttpURLConnection connection = (HttpURLConnection) new URL(src).openConnection();
        connection.setInstanceFollowRedirects(true);
        connection.setConnectTimeout(30_000);
        connection.setReadTimeout(60_000);
        connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android) AI-Figure-Atlas");
        try {
            int code = connection.getResponseCode();
            if (code < 200 || code >= 300) {
                throw new IOException("下载失败 (HTTP " + code + ")");
            }
            try (InputStream input = connection.getInputStream()) {
                return readAll(input);
            }
        } finally {
            connection.disconnect();
        }
    }

    /** 把 https://localhost/... 或 /... 映射为 assets/public/...，外部 URL 返回 null。 */
    private String assetPath(String src) {
        String path = src;
        if (path.startsWith("https://localhost/") || path.startsWith("http://localhost/")) {
            path = path.substring(path.indexOf("localhost") + "localhost".length());
        } else if (path.startsWith("capacitor://localhost/")) {
            path = path.substring("capacitor://localhost".length());
        } else if (!path.startsWith("/")) {
            return null;
        }
        int query = path.indexOf('?');
        if (query >= 0) {
            path = path.substring(0, query);
        }
        try {
            path = URLDecoder.decode(path.startsWith("/") ? path.substring(1) : path, "UTF-8");
        } catch (Exception error) {
            return null;
        }
        if (path.isEmpty() || path.contains("..") || path.contains("\\")) {
            return null;
        }
        return path;
    }

    private String writeToDownloads(byte[] bytes, String filename, String mime) throws IOException {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
            values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/" + FOLDER);
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);
            Uri uri = getContext().getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) {
                throw new IOException("无法创建下载文件");
            }
            try (OutputStream output = getContext().getContentResolver().openOutputStream(uri)) {
                if (output == null) {
                    throw new IOException("无法写入下载文件");
                }
                output.write(bytes);
            }
            values.clear();
            values.put(MediaStore.MediaColumns.IS_PENDING, 0);
            getContext().getContentResolver().update(uri, values, null, null);
            return "下载/" + FOLDER + "/" + filename;
        }

        // Android 9 及以下没有 MediaStore.Downloads，写入应用专属下载目录（无需存储权限）。
        File base = getContext().getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
        if (base == null) {
            throw new IOException("无法访问下载目录");
        }
        File directory = new File(base, FOLDER);
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IOException("无法创建下载目录");
        }
        File target = new File(directory, filename);
        try (FileOutputStream output = new FileOutputStream(target)) {
            output.write(bytes);
        }
        return target.getAbsolutePath();
    }

    private String sanitize(String filename, String mime) {
        String name = filename == null ? "" : filename.trim();
        name = name.replaceAll("[\\\\/:*?\"<>|\\r\\n]", "_");
        if (name.isEmpty()) {
            name = "image";
        }
        if (!name.toLowerCase(Locale.ROOT).matches(".*\\.[a-z0-9]{2,5}$")) {
            name += extensionFor(mime);
        }
        return name;
    }

    private String mimeType(String filename, byte[] bytes) {
        String name = filename == null ? "" : filename.toLowerCase(Locale.ROOT);
        if (name.endsWith(".webp")) return "image/webp";
        if (name.endsWith(".png")) return "image/png";
        if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "image/jpeg";
        if (bytes.length > 12 && bytes[0] == 'R' && bytes[1] == 'I' && bytes[2] == 'F' && bytes[3] == 'F') {
            return "image/webp";
        }
        if (bytes.length > 3 && (bytes[0] & 0xFF) == 0x89 && bytes[1] == 'P' && bytes[2] == 'N' && bytes[3] == 'G') {
            return "image/png";
        }
        return "image/jpeg";
    }

    private String extensionFor(String mime) {
        if ("image/webp".equals(mime)) return ".webp";
        if ("image/png".equals(mime)) return ".png";
        return ".jpg";
    }

    private byte[] readAll(InputStream input) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int read;
        while ((read = input.read(buffer)) != -1) {
            output.write(buffer, 0, read);
        }
        return output.toByteArray();
    }
}
