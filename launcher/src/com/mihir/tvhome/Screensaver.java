package com.mihir.tvhome;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapShader;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.os.SystemClock;
import android.service.dreams.DreamService;
import android.view.View;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.Random;

/**
 * Retro arcade / synthwave screensaver drawn entirely in code: neon grid racing to the horizon,
 * a striped sunset sun, wireframe mountains, twinkling stars, scanlines, and a glitching neon clock.
 * The palette cycles every 45 s and the clock drifts slowly to avoid burn-in.
 */
public class Screensaver extends DreamService {

    @Override
    public void onAttachedToWindow() {
        super.onAttachedToWindow();
        setInteractive(false);
        setFullscreen(true);
        setScreenBright(true);
        setContentView(new SynthView(this));
    }

    static final class SynthView extends View {

        // skyTop, skyHorizon, grid, sunTop, sunBottom, mountainLine, clockGlow
        private static final int[][] THEMES = {
                {0xFF0B0221, 0xFF7A0F6B, 0xFFFF2BD6, 0xFFFFE45E, 0xFFFF2E88, 0xFF22E4FF, 0xFF22E4FF},
                {0xFF02110B, 0xFF3B0A6B, 0xFF39FF88, 0xFFB8FF3A, 0xFF9B2BFF, 0xFFB46BFF, 0xFF39FF88},
                {0xFF140208, 0xFF8A1A05, 0xFFFF7A1A, 0xFFFFD23A, 0xFFFF3A3A, 0xFFFFB13A, 0xFFFF5A2A},
        };
        private static final float THEME_SECONDS = 45f;
        private static final float BLEND_SECONDS = 4f;

        private final long start = SystemClock.uptimeMillis();
        private final Random rnd = new Random();
        private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint overlay = new Paint();
        private final Path mountainsL = new Path(), mountainsR = new Path();
        private final int[] col = new int[7];
        private final int[] lastCol = new int[7];

        private int w, h;
        private float horizon, sunR;
        private float[] starX, starY, starPhase, starSpeed;
        private Shader skyShader, sunShader, glowShader;
        private String clockStr = "", dateStr = "";
        private long lastSecond = -1;

        SynthView(Context c) {
            super(c);
            line.setStyle(Paint.Style.STROKE);
            line.setStrokeCap(Paint.Cap.ROUND);
            text.setTextAlign(Paint.Align.CENTER);
        }

        @Override
        protected void onSizeChanged(int nw, int nh, int ow, int oh) {
            w = nw;
            h = nh;
            horizon = h * 0.60f;
            sunR = h * 0.21f;

            int n = 140;
            starX = new float[n];
            starY = new float[n];
            starPhase = new float[n];
            starSpeed = new float[n];
            for (int i = 0; i < n; i++) {
                starX[i] = rnd.nextFloat() * w;
                starY[i] = rnd.nextFloat() * horizon * 0.85f;
                starPhase[i] = rnd.nextFloat() * 6.28f;
                starSpeed[i] = 0.6f + rnd.nextFloat() * 2.2f;
            }

            buildMountains(mountainsL, 0, w * 0.40f, true);
            buildMountains(mountainsR, w * 0.60f, w, false);

            // Scanlines: a 1x4 tile with one dark row, repeated over the whole screen.
            Bitmap tile = Bitmap.createBitmap(1, 4, Bitmap.Config.ARGB_8888);
            tile.setPixel(0, 0, 0x30000000);
            overlay.setShader(new BitmapShader(tile, Shader.TileMode.REPEAT, Shader.TileMode.REPEAT));

            text.setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD));
            skyShader = null; // rebuild shaders for the new size
        }

        private void buildMountains(Path p, float x0, float x1, boolean left) {
            p.reset();
            p.moveTo(x0, horizon);
            int peaks = 9;
            for (int i = 0; i <= peaks; i++) {
                float x = x0 + (x1 - x0) * i / peaks;
                // Taller toward the screen edges, flat toward the sun in the middle.
                float edge = left ? 1f - (float) i / peaks : (float) i / peaks;
                float height = h * (0.03f + 0.13f * edge) * (0.55f + 0.45f * rnd.nextFloat());
                p.lineTo(x, horizon - (i % 2 == 0 ? height : height * 0.45f));
            }
            p.lineTo(x1, horizon);
            p.close();
        }

        @Override
        protected void onDraw(Canvas c) {
            float t = (SystemClock.uptimeMillis() - start) / 1000f;
            updateTheme(t);
            updateClock();

            // Sky
            fill.setShader(skyShader);
            c.drawRect(0, 0, w, horizon, fill);
            fill.setShader(null);

            // Stars
            for (int i = 0; i < starX.length; i++) {
                float a = 0.35f + 0.65f * (0.5f + 0.5f * (float) Math.sin(t * starSpeed[i] + starPhase[i]));
                fill.setColor(Color.argb((int) (a * 230), 255, 255, 255));
                float x = (starX[i] + t * 4f * starSpeed[i]) % w;
                c.drawCircle(x, starY[i], i % 9 == 0 ? 2.6f : 1.4f, fill);
            }

            // Sun glow + sun (clipped to the sky) with stripes sliding down
            float cx = w / 2f;
            fill.setShader(glowShader);
            c.drawCircle(cx, horizon - sunR * 0.35f, sunR * 1.9f, fill);
            c.save();
            c.clipRect(0, 0, w, horizon);
            fill.setShader(sunShader);
            c.drawCircle(cx, horizon - sunR * 0.35f, sunR, fill);
            fill.setShader(null);
            fill.setColor(col[1]);
            float bandZone = sunR * 0.95f;
            float zoneTop = horizon - bandZone;
            for (int k = 0; k < 7; k++) {
                float y = zoneTop + ((t * 14f + k * bandZone / 7f) % bandZone);
                float thick = 2f + 16f * (y - zoneTop) / bandZone;
                c.drawRect(cx - sunR * 1.1f, y, cx + sunR * 1.1f, y + thick, fill);
            }
            c.restore();

            // Mountains: dark fill with a neon outline
            fill.setColor(0xFF07010F);
            c.drawPath(mountainsL, fill);
            c.drawPath(mountainsR, fill);
            neon(c, col[5], 2.5f);
            c.drawPath(mountainsL, line);
            c.drawPath(mountainsR, line);

            // Floor
            fill.setColor(0xFF05000C);
            c.drawRect(0, horizon, w, h, fill);

            // Grid: horizontal lines rush toward the viewer, vertical ones converge on the horizon
            float depth = h - horizon;
            float scroll = (t * 0.9f) % 1f;
            for (int k = 0; k < 26; k++) {
                float z = k + 1f - scroll;
                if (z < 0.35f) continue;
                float y = horizon + depth * 0.55f / z;
                if (y > h) continue;
                float a = Math.min(1f, (y - horizon) / depth * 3.2f);
                gridLine(c, 0, y, w, y, a);
            }
            float spread = w * 0.11f;
            for (int i = -18; i <= 18; i++) {
                gridLine(c, cx + i * spread * 0.04f, horizon, cx + i * spread, h, 1f);
            }
            // Bright horizon line
            neon(c, col[2], 3f);
            c.drawLine(0, horizon, w, horizon, line);

            // Clock (drifts slowly so nothing burns in)
            float dx = (float) Math.sin(t / 37f) * w * 0.03f;
            float dy = (float) Math.cos(t / 53f) * h * 0.015f;
            float clockY = h * 0.25f + dy;
            text.setTextSize(h * 0.17f);
            text.setLetterSpacing(0.04f);
            boolean glitch = (t % 7.3f) < 0.22f;
            if (glitch) {
                float off = h * 0.008f + rnd.nextFloat() * h * 0.012f;
                text.clearShadowLayer();
                text.setColor(0xB0FF2040);
                c.drawText(clockStr, cx + dx - off, clockY, text);
                text.setColor(0xB020E0FF);
                c.drawText(clockStr, cx + dx + off, clockY + off * 0.3f, text);
            }
            text.setShadowLayer(h * 0.03f, 0, 0, col[6]);
            text.setColor(0xFFF4F0FF);
            c.drawText(clockStr, cx + dx + (glitch ? rnd.nextFloat() * 6f - 3f : 0f), clockY, text);

            text.setTextSize(h * 0.032f);
            text.setLetterSpacing(0.35f);
            text.setShadowLayer(h * 0.015f, 0, 0, col[6]);
            text.setColor(0xD9FFFFFF);
            c.drawText(dateStr, cx + dx, clockY + h * 0.07f, text);

            // Blinking arcade prompt
            if ((t % 1.6f) < 1.0f) {
                text.setTextSize(h * 0.028f);
                text.setLetterSpacing(0.45f);
                text.setShadowLayer(h * 0.012f, 0, 0, col[2]);
                text.setColor(0xE6FFFFFF);
                c.drawText("PRESS ANY BUTTON", cx, h * 0.94f, text);
            }
            text.clearShadowLayer();

            // CRT scanlines
            c.drawRect(0, 0, w, h, overlay);

            postInvalidateOnAnimation();
        }

        private void gridLine(Canvas c, float x0, float y0, float x1, float y1, float a) {
            int g = col[2];
            line.setShader(null);
            line.clearShadowLayer();
            line.setStrokeWidth(7f);
            line.setColor(Color.argb((int) (55 * a), Color.red(g), Color.green(g), Color.blue(g)));
            c.drawLine(x0, y0, x1, y1, line);
            line.setStrokeWidth(2f);
            line.setColor(Color.argb((int) (235 * a), Color.red(g), Color.green(g), Color.blue(g)));
            c.drawLine(x0, y0, x1, y1, line);
        }

        private void neon(Canvas c, int color, float width) {
            line.setShader(null);
            line.setStrokeWidth(width);
            line.setColor(color);
            line.setShadowLayer(width * 4f, 0, 0, color);
        }

        private void updateTheme(float t) {
            int idx = (int) (t / THEME_SECONDS) % THEMES.length;
            int next = (idx + 1) % THEMES.length;
            float into = t % THEME_SECONDS;
            float f = into > THEME_SECONDS - BLEND_SECONDS ? (into - (THEME_SECONDS - BLEND_SECONDS)) / BLEND_SECONDS : 0f;
            boolean changed = false;
            for (int i = 0; i < col.length; i++) {
                col[i] = lerp(THEMES[idx][i], THEMES[next][i], f);
                if (col[i] != lastCol[i]) changed = true;
            }
            if (!changed && skyShader != null) return;
            System.arraycopy(col, 0, lastCol, 0, col.length);
            skyShader = new LinearGradient(0, 0, 0, horizon, col[0], col[1], Shader.TileMode.CLAMP);
            float sunCy = horizon - sunR * 0.35f;
            sunShader = new LinearGradient(0, sunCy - sunR, 0, sunCy + sunR, col[3], col[4], Shader.TileMode.CLAMP);
            int glow = col[4];
            glowShader = new RadialGradient(w / 2f, sunCy, sunR * 1.9f,
                    new int[]{Color.argb(110, Color.red(glow), Color.green(glow), Color.blue(glow)), 0x00000000},
                    null, Shader.TileMode.CLAMP);
        }

        private void updateClock() {
            long sec = System.currentTimeMillis() / 1000;
            if (sec == lastSecond) return;
            lastSecond = sec;
            Date now = new Date();
            boolean is24 = android.text.format.DateFormat.is24HourFormat(getContext());
            clockStr = new SimpleDateFormat(is24 ? "HH:mm" : "h:mm", Locale.getDefault()).format(now);
            dateStr = new SimpleDateFormat("EEEE, d MMMM", Locale.getDefault()).format(now).toUpperCase(Locale.getDefault());
        }

        private static int lerp(int a, int b, float f) {
            if (f <= 0f) return a;
            int ar = Color.red(a), ag = Color.green(a), ab = Color.blue(a);
            return Color.rgb(
                    (int) (ar + (Color.red(b) - ar) * f),
                    (int) (ag + (Color.green(b) - ag) * f),
                    (int) (ab + (Color.blue(b) - ab) * f));
        }
    }
}
