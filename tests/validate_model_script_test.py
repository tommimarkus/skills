import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_MODEL = (
    REPO_ROOT / "souroldgeezer-design/skills/architecture-design/references/scripts/validate-model.ajs"
)


def run_validate_model(model: dict) -> subprocess.CompletedProcess[str]:
    harness = textwrap.dedent(
        """\
        const fs = require("fs");
        const vm = require("vm");

        const model = JSON.parse(process.env.FAKE_JARCHI_MODEL);
        const logs = [];

        function collection(items) {
          return {
            _items: items,
            each: function(callback) {
              for (let index = 0; index < items.length; index += 1) {
                callback(items[index]);
              }
            },
            find: function(selector) {
              let found = [];
              for (let index = 0; index < items.length; index += 1) {
                if (typeof items[index].find === "function") {
                  found = found.concat(items[index].find(selector)._items);
                }
              }
              return collection(found);
            }
          };
        }

        const elementsById = {};
        for (const element of model.elements) {
          elementsById[element.id] = element;
        }

        const relationships = model.relationships.map((relationship) => ({
          id: relationship.id,
          name: relationship.name || "",
          type: relationship.type,
          source: elementsById[relationship.source] || null,
          target: elementsById[relationship.target] || null
        }));
        const relationshipsById = {};
        for (const relationship of relationships) {
          relationshipsById[relationship.id] = relationship;
        }

        function viewNode(node) {
          return {
            id: node.id,
            type: "element",
            name: node.name || "",
            concept: node.elementRef ? (elementsById[node.elementRef] || null) : null
          };
        }

        const views = model.views.map((view) => {
          const nodes = (view.nodes || []).map(viewNode);
          const nodesById = {};
          for (const node of nodes) {
            nodesById[node.id] = node;
          }
          const connections = (view.connections || []).map((connection) => ({
            id: connection.id,
            type: "relationship",
            name: connection.name || "",
            concept: connection.relationshipRef ? (relationshipsById[connection.relationshipRef] || null) : null,
            source: connection.source ? (nodesById[connection.source] || null) : null,
            target: connection.target ? (nodesById[connection.target] || null) : null
          }));

          return {
            id: view.id,
            name: view.name,
            type: "view",
            find: function(selector) {
              if (selector === "element") {
                return collection(nodes);
              }
              if (selector === "relationship") {
                return collection(connections);
              }
              return collection([]);
            }
          };
        });

        function select(selector) {
          if (selector === "element") {
            return collection(model.elements);
          }
          if (selector === "relationship") {
            return collection(relationships);
          }
          if (selector === "view") {
            return collection(views);
          }
          return collection([]);
        }

        select.model = {
          isAllowedRelationship: function(relationshipType, sourceType, targetType) {
            return !(relationshipType === "InvalidRelationship" || sourceType === "InvalidSource" || targetType === "InvalidTarget");
          }
        };

        const context = {
          console: { log: (line) => logs.push(String(line)) },
          $: select
        };

        vm.createContext(context);
        vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), context, { filename: process.argv[2] });
        process.stdout.write(logs.join("\\n"));
        """
    )

    with tempfile.TemporaryDirectory() as tmp:
        harness_path = Path(tmp) / "fake-jarchi.js"
        harness_path.write_text(harness, encoding="utf-8")
        env = os.environ.copy()
        env["FAKE_JARCHI_MODEL"] = json.dumps(model)
        return subprocess.run(
            ["node", str(harness_path), str(VALIDATE_MODEL)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPO_ROOT,
            env=env,
        )


class ValidateModelScriptTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node is required to execute validate-model.ajs")
    def test_warns_for_low_risk_archi_validator_checks_without_failing_model(self) -> None:
        model = {
            "elements": [
                {"id": "id-component-a", "type": "ApplicationComponent", "name": "Checkout"},
                {"id": "id-component-b", "type": "ApplicationComponent", "name": "Checkout"},
                {"id": "id-runtime", "type": "Node", "name": "Function App"},
            ],
            "relationships": [
                {
                    "id": "id-rel-runtime-serves-checkout",
                    "type": "Serving",
                    "source": "id-runtime",
                    "target": "id-component-a",
                }
            ],
            "views": [
                {"id": "id-view-empty", "name": "Empty view", "nodes": [], "connections": []},
                {
                    "id": "id-view-main",
                    "name": "Main view",
                    "nodes": [{"id": "id-node-component-a", "elementRef": "id-component-a"}],
                    "connections": [],
                },
            ],
        }

        result = run_validate_model(model)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ARCHI_VALIDATE_MODEL: WARN empty view", result.stdout)
        self.assertIn("ARCHI_VALIDATE_MODEL: WARN unused element", result.stdout)
        self.assertIn("ARCHI_VALIDATE_MODEL: WARN unused relationship", result.stdout)
        self.assertIn("ARCHI_VALIDATE_MODEL: WARN possible duplicate element", result.stdout)
        self.assertIn("ARCHI_VALIDATE_MODEL: OK invalid=0 warnings=", result.stdout)

    @unittest.skipUnless(shutil.which("node"), "node is required to execute validate-model.ajs")
    def test_invalid_visual_element_reference_is_blocking(self) -> None:
        model = {
            "elements": [{"id": "id-component", "type": "ApplicationComponent", "name": "Checkout"}],
            "relationships": [],
            "views": [
                {
                    "id": "id-view-main",
                    "name": "Main view",
                    "nodes": [{"id": "id-node-missing", "elementRef": "id-missing"}],
                    "connections": [],
                }
            ],
        }

        result = run_validate_model(model)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ARCHI_VALIDATE_MODEL: INVALID visual element", result.stdout)
        self.assertIn("ARCHI_VALIDATE_MODEL: FAIL invalid=1 warnings=", result.stdout)


if __name__ == "__main__":
    unittest.main()
