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
                ArchLayoutCli.MaterializeOefCommand.class,
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

    @Command(name = "materialize-oef", description = "Apply layout result geometry and routes to an OEF view.")
    static final class MaterializeOefCommand implements Callable<Integer> {
        @Option(names = "--oef", required = true)
        Path oefPath;
        @Option(names = "--view", required = true)
        String viewId;
        @Option(names = "--result", required = true)
        Path resultPath;
        @Option(names = "--out", required = true)
        Path outPath;
        @Option(names = "--snap-grid", defaultValue = "0")
        int snapGrid;
        @Option(names = "--preserve-locked-nodes")
        boolean preserveLockedNodes;
        @Option(names = "--fail-on-warning")
        boolean failOnWarning;
        @Option(names = "--run-source-gate")
        boolean runSourceGate;

        @Override
        public Integer call() throws IOException, InterruptedException {
            LayoutSchemaValidator validator = new LayoutSchemaValidator();
            JsonNode result = JsonFiles.read(resultPath);
            ValidationResult resultValidation = validator.validateResult(result);
            if (!resultValidation.ok()) {
                resultValidation.diagnostics().forEach(diagnostic -> System.err.println("invalid layoutResult: " + diagnostic));
                return 1;
            }
            String state = result.path("validation").path("state").asText();
            if ("invalid".equals(state) || (failOnWarning && !"valid".equals(state))) {
                System.err.println("layoutResult validation state is " + state + ": " + resultPath);
                return 1;
            }

            OefMaterializer materializer = new OefMaterializer();
            ValidationResult materialized = materializer.materialize(
                    oefPath,
                    viewId,
                    result,
                    outPath,
                    new OefMaterializer.Options(snapGrid, preserveLockedNodes));
            if (!materialized.ok()) {
                materialized.diagnostics().forEach(diagnostic -> System.err.println("invalid OEF materialization: " + diagnostic));
                return 1;
            }

            if (runSourceGate) {
                int exitCode = runSourceGate(outPath);
                if (exitCode != 0) {
                    System.err.println("source geometry gate failed for: " + outPath);
                    return 1;
                }
            }
            System.out.println("wrote materialized OEF: " + outPath);
            return 0;
        }

        private static int runSourceGate(Path materialized) throws IOException, InterruptedException {
            Path gate = LayoutPaths.referencesDir().resolve("scripts").resolve("validate-oef-layout.sh");
            Process process = new ProcessBuilder("bash", gate.toString(), materialized.toString())
                    .redirectErrorStream(true)
                    .start();
            try (java.io.InputStream stream = process.getInputStream()) {
                stream.transferTo(System.err);
            }
            return process.waitFor();
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
