package com.souroldgeezer.architecture.layout;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.souroldgeezer.architecture.layout.elk.ElkLayoutBackend;
import com.souroldgeezer.architecture.layout.png.PngAnalysisResult;
import com.souroldgeezer.architecture.layout.png.PngAnalyzer;
import com.souroldgeezer.architecture.layout.png.PngAnalyzer.PngOptions;
import com.souroldgeezer.architecture.layout.polish.GlobalPolishBackend;
import com.souroldgeezer.architecture.layout.router.RouteRepairBackend;
import com.souroldgeezer.architecture.layout.schema.LayoutSchemaValidator;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.PrintStream;
import java.nio.file.Path;
import java.util.concurrent.Callable;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(
        name = "arch-layout",
        mixinStandardHelpOptions = true,
        version = VersionCommand.VERSION,
        description = "Architecture layout validation and repair utilities.",
        subcommands = {
                ArchLayoutCli.ValidateRequestCommand.class,
                ArchLayoutCli.ValidateResultCommand.class,
                ArchLayoutCli.LayoutElkCommand.class,
                ArchLayoutCli.RouteRepairCommand.class,
                ArchLayoutCli.GlobalPolishCommand.class,
                ArchLayoutCli.ValidatePngCommand.class
        })
public final class ArchLayoutCli implements Callable<Integer> {
    private final PrintStream out;
    private final PrintStream err;

    public ArchLayoutCli() {
        this(System.out, System.err);
    }

    public ArchLayoutCli(PrintStream out, PrintStream err) {
        this.out = out;
        this.err = err;
    }

    public static void main(String[] args) {
        int exitCode = new ArchLayoutCli().execute(args);
        System.exit(exitCode);
    }

    public int execute(String... args) {
        CommandLine commandLine = new CommandLine(this);
        commandLine.setOut(new PrintWriter(out, true));
        commandLine.setErr(new PrintWriter(err, true));
        return commandLine.execute(args);
    }

    @Override
    public Integer call() {
        out.println(VersionCommand.VERSION);
        return 0;
    }

    @Command(name = "validate-request", description = "Validate a layout request JSON file.")
    static final class ValidateRequestCommand implements Callable<Integer> {
        @Option(names = "--request", required = true)
        Path request;

        @Override
        public Integer call() throws IOException {
            ValidationResult result = new LayoutSchemaValidator().validateRequest(request);
            if (result.ok()) {
                System.out.println("valid layoutRequest: " + request);
                return 0;
            }
            result.diagnostics().forEach(diagnostic -> System.err.println("invalid layoutRequest: " + diagnostic));
            return 1;
        }
    }

    @Command(name = "validate-result", description = "Validate a layout result JSON file.")
    static final class ValidateResultCommand implements Callable<Integer> {
        @Option(names = "--result", required = true)
        Path resultPath;

        @Override
        public Integer call() throws IOException {
            ValidationResult result = new LayoutSchemaValidator().validateResult(resultPath);
            if (result.ok()) {
                System.out.println("valid layoutResult: " + resultPath);
                return 0;
            }
            result.diagnostics().forEach(diagnostic -> System.err.println("invalid layoutResult: " + diagnostic));
            return 1;
        }
    }

    @Command(name = "layout-elk", description = "Generate a deterministic ELK-style layered layout result.")
    static final class LayoutElkCommand implements Callable<Integer> {
        @Option(names = "--request", required = true)
        Path requestPath;
        @Option(names = "--result", required = true)
        Path resultPath;

        @Override
        public Integer call() throws IOException {
            LayoutSchemaValidator validator = new LayoutSchemaValidator();
            JsonNode request = JsonFiles.read(requestPath);
            ValidationResult requestValidation = validator.validateRequest(request);
            if (!requestValidation.ok()) {
                requestValidation.diagnostics().forEach(diagnostic -> System.err.println("invalid layoutRequest: " + diagnostic));
                return 1;
            }
            ObjectNode result = new ElkLayoutBackend().layout(request);
            ValidationResult resultValidation = validator.validateResult(result);
            if (!resultValidation.ok()) {
                resultValidation.diagnostics().forEach(diagnostic -> System.err.println("invalid generated layoutResult: " + diagnostic));
                return 1;
            }
            JsonFiles.write(resultPath, result);
            System.out.println("wrote layoutResult: " + resultPath);
            return 0;
        }
    }

    @Command(name = "route-repair", description = "Repair routes while preserving node geometry.")
    static final class RouteRepairCommand implements Callable<Integer> {
        @Option(names = "--request", required = true)
        Path requestPath;
        @Option(names = "--result", required = true)
        Path resultPath;

        @Override
        public Integer call() throws IOException {
            LayoutSchemaValidator validator = new LayoutSchemaValidator();
            JsonNode request = JsonFiles.read(requestPath);
            ValidationResult requestValidation = validator.validateRequest(request);
            if (!requestValidation.ok()) {
                requestValidation.diagnostics().forEach(diagnostic -> System.err.println("invalid layoutRequest: " + diagnostic));
                return 1;
            }
            ObjectNode result = new RouteRepairBackend().repair(request);
            JsonFiles.write(resultPath, result);
            System.out.println("wrote routeRepair layoutResult: " + resultPath);
            return 0;
        }
    }

    @Command(name = "global-polish", description = "Apply bounded mental-map preserving polish.")
    static final class GlobalPolishCommand implements Callable<Integer> {
        @Option(names = "--request", required = true)
        Path requestPath;
        @Option(names = "--result", required = true)
        Path resultPath;

        @Override
        public Integer call() throws IOException {
            LayoutSchemaValidator validator = new LayoutSchemaValidator();
            JsonNode request = JsonFiles.read(requestPath);
            ValidationResult requestValidation = validator.validateRequest(request);
            if (!requestValidation.ok()) {
                requestValidation.diagnostics().forEach(diagnostic -> System.err.println("invalid layoutRequest: " + diagnostic));
                return 1;
            }
            ObjectNode result = new GlobalPolishBackend().polish(request);
            JsonFiles.write(resultPath, result);
            System.out.println("wrote globalPolish layoutResult: " + resultPath);
            return 0;
        }
    }

    @Command(name = "validate-png", description = "Validate rendered PNG invariants and optional baseline drift.")
    static final class ValidatePngCommand implements Callable<Integer> {
        @Option(names = "--image", required = true)
        Path image;
        @Option(names = "--baseline")
        Path baseline;
        @Option(names = "--result", required = true)
        Path result;
        @Option(names = "--min-width", defaultValue = "200")
        int minWidth;
        @Option(names = "--min-height", defaultValue = "120")
        int minHeight;
        @Option(names = "--blank-threshold", defaultValue = "0.01")
        double blankThreshold;
        @Option(names = "--crop-margin", defaultValue = "2")
        int cropMargin;
        @Option(names = "--whitespace-threshold", defaultValue = "0.96")
        double whitespaceThreshold;
        @Option(names = "--tolerance", defaultValue = "0.03")
        double tolerance;

        @Override
        public Integer call() throws IOException {
            PngOptions options = new PngOptions(minWidth, minHeight, blankThreshold, 12, cropMargin, whitespaceThreshold, tolerance, 10);
            PngAnalyzer analyzer = new PngAnalyzer();
            PngAnalysisResult analysis = baseline == null ? analyzer.analyze(image, options) : analyzer.compare(image, baseline, options);
            JsonFiles.write(result, analysis.toJson());
            if (analysis.valid()) {
                System.out.println("valid rendered PNG: " + image);
                return 0;
            }
            System.err.println("invalid rendered PNG: " + analysis.message());
            return 1;
        }
    }
}
