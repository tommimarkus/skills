package com.souroldgeezer.architecture.layout.png;

import java.awt.Rectangle;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import javax.imageio.ImageIO;

public final class PngAnalyzer {
    public PngAnalysisResult analyze(Path imagePath, PngOptions options) throws IOException {
        BufferedImage image = readPng(imagePath);
        Analysis analysis = inspect(image, options);
        boolean valid = !analysis.blank()
                && !analysis.tiny()
                && !analysis.croppedToEdge();
        return new PngAnalysisResult(
                valid,
                image.getWidth(),
                image.getHeight(),
                analysis.colorDiversity(),
                analysis.blank(),
                analysis.tiny(),
                analysis.croppedToEdge(),
                analysis.whitespaceRatio() > options.whitespaceWarningThreshold(),
                0.0,
                valid ? "PNG passes invariant checks." : "PNG failed invariant checks.");
    }

    public PngAnalysisResult compare(Path imagePath, Path baselinePath, PngOptions options) throws IOException {
        BufferedImage image = readPng(imagePath);
        BufferedImage baseline = readPng(baselinePath);
        Analysis analysis = inspect(image, options);
        if (image.getWidth() != baseline.getWidth() || image.getHeight() != baseline.getHeight()) {
            return new PngAnalysisResult(false, image.getWidth(), image.getHeight(), analysis.colorDiversity(), analysis.blank(), analysis.tiny(), analysis.croppedToEdge(), analysis.whitespaceRatio() > options.whitespaceWarningThreshold(), 1.0, "Baseline dimensions differ.");
        }
        int changed = 0;
        int total = image.getWidth() * image.getHeight();
        for (int y = 0; y < image.getHeight(); y++) {
            for (int x = 0; x < image.getWidth(); x++) {
                if (colorDistance(image.getRGB(x, y), baseline.getRGB(x, y)) > options.baselineColorTolerance()) {
                    changed++;
                }
            }
        }
        double ratio = total == 0 ? 0.0 : (double) changed / total;
        boolean valid = ratio <= options.baselineTolerance() && !analysis.blank() && !analysis.tiny();
        return new PngAnalysisResult(valid, image.getWidth(), image.getHeight(), analysis.colorDiversity(), analysis.blank(), analysis.tiny(), analysis.croppedToEdge(), analysis.whitespaceRatio() > options.whitespaceWarningThreshold(), ratio, valid ? "PNG baseline comparison passes." : "PNG baseline comparison failed.");
    }

    private static BufferedImage readPng(Path path) throws IOException {
        if (!Files.isRegularFile(path)) {
            throw new IOException("PNG file not found: " + path);
        }
        BufferedImage image = ImageIO.read(path.toFile());
        if (image == null) {
            throw new IOException("File is not a readable PNG: " + path);
        }
        return image;
    }

    private static Analysis inspect(BufferedImage image, PngOptions options) {
        int width = image.getWidth();
        int height = image.getHeight();
        int background = image.getRGB(0, 0);
        Set<Integer> colors = new HashSet<>();
        int minX = width;
        int minY = height;
        int maxX = -1;
        int maxY = -1;
        int nonBackground = 0;
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int rgb = image.getRGB(x, y);
                colors.add(rgb);
                if (colorDistance(rgb, background) > options.blankColorDistance()) {
                    nonBackground++;
                    minX = Math.min(minX, x);
                    minY = Math.min(minY, y);
                    maxX = Math.max(maxX, x);
                    maxY = Math.max(maxY, y);
                }
            }
        }
        boolean tiny = width < options.minimumWidth() || height < options.minimumHeight();
        boolean blank = colors.size() <= 1 || nonBackground < Math.max(2, (int) (width * height * options.blankPixelThreshold()));
        Rectangle bounds = maxX >= minX ? new Rectangle(minX, minY, maxX - minX + 1, maxY - minY + 1) : new Rectangle();
        boolean cropped = !blank && (bounds.x <= options.cropMargin()
                || bounds.y <= options.cropMargin()
                || bounds.x + bounds.width >= width - options.cropMargin()
                || bounds.y + bounds.height >= height - options.cropMargin());
        double whitespace = 1.0 - ((double) nonBackground / Math.max(1, width * height));
        return new Analysis(colors.size(), blank, tiny, cropped, whitespace);
    }

    private static int colorDistance(int a, int b) {
        int ar = (a >> 16) & 0xff;
        int ag = (a >> 8) & 0xff;
        int ab = a & 0xff;
        int br = (b >> 16) & 0xff;
        int bg = (b >> 8) & 0xff;
        int bb = b & 0xff;
        return Math.abs(ar - br) + Math.abs(ag - bg) + Math.abs(ab - bb);
    }

    private record Analysis(int colorDiversity, boolean blank, boolean tiny, boolean croppedToEdge, double whitespaceRatio) {
    }

    public record PngOptions(
            int minimumWidth,
            int minimumHeight,
            double blankPixelThreshold,
            int blankColorDistance,
            int cropMargin,
            double whitespaceWarningThreshold,
            double baselineTolerance,
            int baselineColorTolerance) {
        public static PngOptions defaults() {
            return new PngOptions(200, 120, 0.01, 12, 2, 0.96, 0.03, 10);
        }
    }
}
