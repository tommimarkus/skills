package com.souroldgeezer.architecture.layout.png;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.nio.file.Path;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class PngAnalyzerTest {
    @TempDir
    Path tempDir;

    @Test
    void detectsBlankTinyCroppedAndBaselineDrift() throws Exception {
        Path blank = tempDir.resolve("blank.png");
        Path tiny = tempDir.resolve("tiny.png");
        Path valid = tempDir.resolve("valid.png");
        Path cropped = tempDir.resolve("cropped.png");
        Path changed = tempDir.resolve("changed.png");
        write(blank, 240, 160, false, false, false);
        write(tiny, 40, 40, true, false, false);
        write(valid, 320, 220, true, false, false);
        write(cropped, 320, 220, true, true, false);
        write(changed, 320, 220, true, false, true);

        PngAnalyzer analyzer = new PngAnalyzer();
        PngAnalyzer.PngOptions options = PngAnalyzer.PngOptions.defaults();

        assertFalse(analyzer.analyze(blank, options).valid());
        assertFalse(analyzer.analyze(tiny, options).valid());
        assertFalse(analyzer.analyze(cropped, options).valid());
        assertTrue(analyzer.analyze(valid, options).valid());
        assertFalse(analyzer.compare(changed, valid, options).valid());
    }

    private static void write(Path path, int width, int height, boolean diagram, boolean cropped, boolean changed) throws Exception {
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = image.createGraphics();
        graphics.setColor(Color.WHITE);
        graphics.fillRect(0, 0, width, height);
        if (diagram) {
            graphics.setColor(changed ? Color.RED : Color.BLACK);
            int x = cropped ? 0 : 40;
            int y = cropped ? 0 : 40;
            graphics.drawRect(x, y, 120, 60);
            graphics.drawRect(width - 180, height - 100, 120, 60);
            graphics.drawLine(x + 120, y + 30, width - 180, height - 70);
            if (changed) {
                graphics.fillRect(80, 80, 160, 80);
            }
        }
        graphics.dispose();
        ImageIO.write(image, "png", path.toFile());
    }
}
